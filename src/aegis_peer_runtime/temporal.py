"""Persistent, per-peer T-Time without synthetic catch-up ticks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Callable, Mapping

from .models import PEERS, PeerState
from .storage import StorageError, process_lock


class AdmissionError(ValueError):
    """Raised when a peer is not authorized for live runtime work."""


def require_live_seated(*, seated: bool, live_source: bool, source_mode: str) -> None:
    if not seated:
        raise AdmissionError("peer is not seated")
    if not live_source or source_mode != "live":
        raise AdmissionError("native live source authority is required")


def authority_for(store: object, *, live_source: bool = False, source_mode: str = "unverified") -> dict[str, object]:
    """Build an explicit authority gate without inferring live status from storage."""
    return {
        "seated": getattr(store, "state", None) is PeerState.SEATED,
        "live_source": live_source,
        "source_mode": source_mode,
        "claim": "record_preservation_only",
        "continuity_claimed": False,
        "self_claimed": False,
    }


@dataclass(frozen=True)
class TemporalObservation:
    peer_id: str
    t_time: int
    observed_at: str
    elapsed_seconds: float
    kind: str = "temporal_observation"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("observed_at must include a timezone")
    return parsed.astimezone(timezone.utc)


class TemporalRuntime:
    """Append one observation per actual run, aggregating elapsed wall time."""

    def __init__(
        self,
        peer_id: str,
        ledger_path: str | Path,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        if peer_id not in PEERS:
            raise ValueError(f"unknown peer_id: {peer_id}")
        self.peer_id = peer_id
        self.ledger_path = Path(ledger_path)
        self.clock = clock

    def _history_unlocked(self) -> tuple[TemporalObservation, ...]:
        if not self.ledger_path.exists():
            return ()
        if self.ledger_path.is_symlink():
            raise StorageError(f"temporal ledger must not be a symlink: {self.ledger_path}")
        observations: list[TemporalObservation] = []
        with self.ledger_path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                item = json.loads(line)
                observation = TemporalObservation(**item)
                if observation.peer_id != self.peer_id:
                    raise ValueError(f"cross-peer temporal record at line {line_number}")
                if observations and observation.t_time != observations[-1].t_time + 1:
                    raise ValueError(f"non-monotonic T-Time at line {line_number}")
                observations.append(observation)
        return tuple(observations)

    def history(self) -> tuple[TemporalObservation, ...]:
        with process_lock(self.ledger_path.with_suffix(self.ledger_path.suffix + ".lock")):
            return self._history_unlocked()

    def observe(
        self,
        *,
        seated: bool,
        live_source: bool,
        source_mode: str,
        tensors: Mapping[str, object] | None = None,
    ) -> TemporalObservation:
        require_live_seated(
            seated=seated, live_source=live_source, source_mode=source_mode
        )
        before = dict(tensors or {})
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with process_lock(self.ledger_path.with_suffix(self.ledger_path.suffix + ".lock")):
            history = self._history_unlocked()
            now = self.clock().astimezone(timezone.utc)
            elapsed = 0.0 if not history else (now - _parse(history[-1].observed_at)).total_seconds()
            if elapsed < 0:
                raise ValueError("clock moved backwards")
            observation = TemporalObservation(
                peer_id=self.peer_id,
                t_time=(history[-1].t_time + 1) if history else 1,
                observed_at=now.isoformat().replace("+00:00", "Z"),
                elapsed_seconds=elapsed,
            )
            if self.ledger_path.is_symlink():
                raise StorageError(f"temporal ledger must not be a symlink: {self.ledger_path}")
            with self.ledger_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(asdict(observation), sort_keys=True, separators=(",", ":")))
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
        if dict(tensors or {}) != before:
            raise RuntimeError("Temporal runtime mutated authoritative tensors")
        return observation
