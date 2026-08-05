"""Per-invocation evidence recorder for the rls-persistent-relations-core Orb.

Declaring RLS's capabilities in a contract document (see
H:\\AEGIS-POD-ARCHITECTURE\\stage-d-out\\CP-1004-ORION\\pod\\provenance\\
rls-persistent-relations-core.orb.json) states what the Orb does. This module is
what makes each real invocation show what it actually did: every call appends one
hash-bound, append-only line to the Orb's own evidence ledger, distinct from the
cross-tensor relation entries RLS already writes.

runtime_hash binds the evidence to the exact RLS source that produced it - if
engine.py/scoring.py/relevance.py change, runtime_hash changes, so old evidence
can never be mistaken for proof of new behaviour.

Gated via store.is_active(ORB_ID) — the Pod-agnostic form of the Pod-specific
AEGIS_RLS_ACTIVE gate. A true no-op when the capability is not active, matching
the original RelationsRecorder contract this was extracted from.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles
from aegis_pod_sdk import DataQuadStoreProtocol, sha256_upper, stable_json

_SOURCE_FILES = ("engine.py", "scoring.py", "relevance.py")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_runtime_hash() -> str:
    """SHA-256 (uppercase hex) of this Orb's exact source bytes (engine.py +
    scoring.py + relevance.py, concatenated). Public and top-level by
    convention: any Orb package declaring `runtime.package` in its contract
    (contracts/orb.schema.json) is expected to expose a `compute_runtime_hash()`
    callable at its package root, so aegis_pod.orb_runtime.validate_attachment()
    can gate on it generically without hardcoding any Orb's file list."""
    rls_dir = Path(__file__).resolve().parent
    concatenated = "".join(
        (rls_dir / name).read_text(encoding="utf-8") for name in _SOURCE_FILES
    )
    return sha256_upper(concatenated)


class RLSOrbEvidenceRecorder:
    ORB_ID = "rls-persistent-relations-core"

    async def record_invocation(
        self,
        store: DataQuadStoreProtocol,
        peer_id: str,
        invocation_inputs: dict[str, Any],
        session_result: dict[str, Any],
        retrieved_ids: list[str],
    ) -> None:
        """Append one evidence line for this invocation. No-op unless this Orb's
        capability is active on the given store."""
        if not store.is_active(self.ORB_ID):
            return

        input_hash = sha256_upper(stable_json(invocation_inputs))
        output_hash = sha256_upper(stable_json(session_result))
        failure_is_data = bool(session_result.get("failure_is_data"))

        entry = {
            "orb_id": self.ORB_ID,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "runtime_hash": compute_runtime_hash(),
            "observable_events": [
                "session_started",
                "candidates_scored",
                "candidates_partitioned",
                "pct_written",
                "relations_recorded",
                "session_completed",
            ],
            "selected_count": len(session_result.get("selected_refs") or []),
            "rejected_count": len(session_result.get("rejected_refs") or []),
            "relations_recorded_count": len(retrieved_ids),
            "failure_is_data": failure_is_data,
            "timestamp": _now(),
        }

        peer_root = Path(store.peer_root(peer_id))
        path = peer_root / "pod" / "ledgers" / "orbs" / f"{self.ORB_ID}.evidence.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, mode="a", encoding="utf-8") as handle:
            await handle.write(stable_json(entry) + "\n")
