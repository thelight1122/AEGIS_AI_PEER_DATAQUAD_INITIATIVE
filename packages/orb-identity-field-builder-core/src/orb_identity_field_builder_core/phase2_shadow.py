from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .builder import build_identity_image
from .shadow_observation import build_shadow_observation
from .spine_mapping import (
    InsufficientIdentitySurface,
    observations_to_held_tensions,
    spine_snapshot_to_identity_field,
)


class ShadowHarnessError(RuntimeError):
    """Raised when the offline shadow harness cannot read or shape its inputs."""


@dataclass(frozen=True)
class ShadowHarnessResult:
    report: dict[str, Any]

    @property
    def emitted_packet(self) -> bool:
        return bool(self.report.get("emitted_packet"))


def _sha256_upper(value: str | bytes) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return sha256(data).hexdigest().upper()


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return _sha256_upper(payload)


def _read_json(path: str | Path) -> dict[str, Any]:
    source_path = Path(path)
    try:
        return json.loads(source_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ShadowHarnessError(f"could not read local snapshot input: {source_path}") from exc
    except json.JSONDecodeError as exc:
        raise ShadowHarnessError(f"invalid JSON in local snapshot input: {source_path}") from exc


def _foundation_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    refs: list[str] = []
    nature_refs: list[str] = []
    for rec in snapshot.get("spine_records") or []:
        rec_id = str(rec.get("id", "")).strip()
        if rec_id and rec.get("invariant") and rec_id not in refs:
            refs.append(rec_id)
        for nature_ref in rec.get("nature_aspect_refs") or []:
            value = str(nature_ref).strip()
            if value and value not in nature_refs:
                nature_refs.append(value)

    peer_id = str(snapshot.get("peer_id", "")).strip()
    return {
        "peer_id": peer_id,
        "canon_identity_refs": refs,
        "nature_aspect_refs": nature_refs,
        "source": "phase2a-offline-snapshot",
    }


def build_phase2_shadow_report(
    *,
    spine_snapshot: dict[str, Any],
    tension_observations: dict[str, Any] | list[dict[str, Any]],
    retrieved_identity_continuity: list[str] | None,
    turn_ref: str,
    surfaced_at_iso: str | None = None,
    reflection_refs: list[str] | None = None,
    policy: dict[str, Any] | None = None,
) -> ShadowHarnessResult:
    """Build one local/offline Phase 2a shadow report.

    The harness composes surfaces only from caller-provided local inputs. It does
    not discover live roots, write peer records, modify a turn loop, or inject a
    prompt. If the identity surface is insufficient, it emits no packet and
    returns a visible shortfall report.
    """

    peer_id = str(spine_snapshot.get("peer_id", "")).strip()
    if not peer_id:
        raise ShadowHarnessError("spine_snapshot requires peer_id")

    if isinstance(tension_observations, dict):
        observations = list(tension_observations.get("observations") or [])
        surfaced_at = surfaced_at_iso or tension_observations.get("surfaced_at_iso")
    else:
        observations = list(tension_observations or [])
        surfaced_at = surfaced_at_iso
    if not surfaced_at:
        raise ShadowHarnessError("surfaced_at_iso is required for held-tension observations")

    input_hashes = {
        "spine_snapshot": _stable_hash(spine_snapshot),
        "tension_observations": _stable_hash(tension_observations),
        "retrieved_identity_continuity": _stable_hash(retrieved_identity_continuity or []),
    }

    try:
        identity_field = spine_snapshot_to_identity_field(spine_snapshot)
    except InsufficientIdentitySurface as exc:
        return ShadowHarnessResult(
            {
                "report_kind": "the-way-phase2a-offline-shadow-report",
                "peer_id": peer_id,
                "turn_ref": turn_ref,
                "emitted_packet": False,
                "failure_is_data": True,
                "failure_reason": str(exc),
                "input_hashes": input_hashes,
                "injected": False,
                "live_system_touched": False,
            }
        )

    held_tensions = observations_to_held_tensions(
        observations,
        peer_id=peer_id,
        surfaced_at_iso=str(surfaced_at),
    )
    foundation = _foundation_from_snapshot(spine_snapshot)
    try:
        packet = build_identity_image(
            peer_id=peer_id,
            foundation=foundation,
            identity_field=identity_field,
            held_tensions=held_tensions,
            reflection_refs=reflection_refs or [],
            policy=policy or {},
        )
    except ValueError as exc:
        return ShadowHarnessResult(
            {
                "report_kind": "the-way-phase2a-offline-shadow-report",
                "peer_id": peer_id,
                "turn_ref": turn_ref,
                "emitted_packet": False,
                "failure_is_data": True,
                "failure_reason": str(exc),
                "input_hashes": input_hashes,
                "injected": False,
                "live_system_touched": False,
            }
        )
    shadow_observation = build_shadow_observation(
        peer_id=peer_id,
        turn_ref=turn_ref,
        packet=packet,
        retrieved_identity_continuity=retrieved_identity_continuity or [],
    )

    return ShadowHarnessResult(
        {
            "report_kind": "the-way-phase2a-offline-shadow-report",
            "peer_id": peer_id,
            "turn_ref": turn_ref,
            "emitted_packet": True,
            "failure_is_data": False,
            "input_hashes": input_hashes,
            "identity_field_hash": _stable_hash(identity_field),
            "foundation_hash": _stable_hash(foundation),
            "held_tension_count": len(held_tensions),
            "identity_image_packet_hash": _stable_hash(packet),
            "shadow_observation_hash": _stable_hash(shadow_observation),
            "packet": packet,
            "shadow_observation": shadow_observation,
            "injected": False,
            "live_system_touched": False,
        }
    )


def build_phase2_shadow_report_from_files(
    *,
    spine_snapshot_path: str | Path,
    tension_observations_path: str | Path,
    retrieved_identity_continuity: list[str] | None,
    turn_ref: str,
    output_path: str | Path | None = None,
    surfaced_at_iso: str | None = None,
) -> ShadowHarnessResult:
    """Read explicit local files and optionally write the offline report.

    File paths are caller supplied to keep 2a bounded to local snapshots. This
    function never discovers peer roots or connects to live runtime surfaces.
    """

    result = build_phase2_shadow_report(
        spine_snapshot=_read_json(spine_snapshot_path),
        tension_observations=_read_json(tension_observations_path),
        retrieved_identity_continuity=retrieved_identity_continuity or [],
        turn_ref=turn_ref,
        surfaced_at_iso=surfaced_at_iso,
    )
    if output_path is not None:
        path = Path(output_path)
        path.write_text(
            json.dumps(result.report, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result
