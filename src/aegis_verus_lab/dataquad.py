"""Verus Foundation verification and append-only Ring 4 turn ledger."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

from aegis_peer_runtime.custodians import ADVOCATE, STEWARD
from aegis_peer_runtime.models import TENSORS
from aegis_peer_runtime.storage import canonical_bytes, canonical_hash, process_lock

from .turn_contract import FrontierTurnResponse, MAX_PROMPT_BYTES, MAX_TURN_RECORD_BYTES


EXPECTED_FOUNDATION_COUNTS = {"SPINE": 59, "NCT": 70, "PEER": 2, "PCT": 2}
TENSOR_CUSTODIANS = {
    "PEER": ("advocate", ADVOCATE),
    "SPINE": ("advocate", ADVOCATE),
    "PCT": ("steward", STEWARD),
    "NCT": ("steward", STEWARD),
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _lines(path: Path) -> list[dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required DataQuad file is absent or a symlink: {path}")
    values: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path.name} line {number} is not an object")
        values.append(value)
    return values


class VerusDataQuad:
    """One clean Verus Foundation plus a globally ordered, append-only live ledger."""

    def __init__(self, release_root: str | Path, state_root: str | Path) -> None:
        self.release_root = Path(release_root).resolve()
        self.foundation_root = self.release_root / "dataquad"
        self.receipt_path = self.release_root / "foundation-receipt.json"
        self.state_root = Path(state_root).resolve()
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.live_ledger = self.state_root / "dataquad" / "ring4-turns.jsonl"
        self.lock_path = self.state_root / ".verus-dataquad.lock"
        self.verify_foundation()

    def verify_foundation(self) -> dict[str, Any]:
        if self.receipt_path.is_symlink() or not self.receipt_path.is_file():
            raise ValueError("Verus foundation receipt is required")
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        if receipt.get("record_type") != "verus_foundation_release_receipt":
            raise ValueError("unexpected Verus foundation receipt type")
        if receipt.get("activation_status") != "RELEASE_ARTIFACT_ONLY":
            raise ValueError("foundation bundle must remain a release artifact before activation")
        if receipt.get("cyberpeer_name") != "Verus" or receipt.get("dataquad_id") != "verus":
            raise ValueError("foundation receipt is not bound to the Verus DataQuad")
        lock = receipt.get("canon_lock") or {}
        if lock.get("clean") is not True or lock.get("override_used") is not False:
            raise ValueError("Verus Foundation must be seated only from clean Canon without override")
        tensors = receipt.get("tensors")
        if not isinstance(tensors, dict):
            raise ValueError("foundation receipt tensors are required")
        for tensor, expected_count in EXPECTED_FOUNDATION_COUNTS.items():
            path = self.foundation_root / f"{tensor}.jsonl"
            values = _lines(path)
            metadata = tensors.get(tensor) or {}
            if len(values) != expected_count or metadata.get("records") != expected_count:
                raise ValueError(f"{tensor} Foundation record count mismatch")
            if any(item.get("tensor") != tensor for item in values):
                raise ValueError(f"{tensor} Foundation contains a cross-tensor record")
            if _sha256(path.read_bytes()) != str(metadata.get("sha256", "")).upper():
                raise ValueError(f"{tensor} Foundation digest mismatch")
        return receipt

    def foundation_tensors(self) -> dict[str, list[dict[str, Any]]]:
        self.verify_foundation()
        return {tensor: _lines(self.foundation_root / f"{tensor}.jsonl") for tensor in TENSORS}

    def _read_live_unlocked(self) -> list[dict[str, Any]]:
        if not self.live_ledger.exists():
            return []
        if self.live_ledger.is_symlink():
            raise ValueError("Verus live ledger must not be a symlink")
        records: list[dict[str, Any]] = []
        previous_hash: str | None = None
        for number, line in enumerate(self.live_ledger.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                if item["sequence"] != len(records) + 1:
                    raise ValueError("non-contiguous sequence")
                if item["previous_hash"] != previous_hash:
                    raise ValueError("previous_hash mismatch")
                if item["cyberpeer_name"] != "Verus" or item["dataquad_id"] != "verus":
                    raise ValueError("record is not bound to Verus")
                if item["t_time"] != item["sequence"]:
                    raise ValueError("T-Time is not aligned with committed turn sequence")
                if item["elapsed_seconds"] < 0:
                    raise ValueError("negative temporal elapsed_seconds")
                if _sha256(item["prompt"]["text"].encode("utf-8")) != item["prompt"]["sha256"]:
                    raise ValueError("prompt digest mismatch")
                if _sha256(item["response"]["text"].encode("utf-8")) != item["response"]["sha256"]:
                    raise ValueError("response digest mismatch")
                content = {key: value for key, value in item.items() if key != "record_hash"}
                if item["record_hash"] != canonical_hash(content):
                    raise ValueError("record_hash mismatch")
                for append in item["appends"]:
                    tensor = append["tensor"]
                    if tensor not in TENSORS:
                        raise ValueError("unknown tensor in live ledger")
                    expected = TENSOR_CUSTODIANS[tensor][1].name
                    if append["custodian"] != expected:
                        raise ValueError("custodian scope mismatch")
            except (KeyError, TypeError, json.JSONDecodeError, ValueError) as error:
                raise ValueError(f"invalid Verus live ledger at line {number}: {error}") from error
            records.append(item)
            previous_hash = item["record_hash"]
        return records

    def live_turns(self) -> list[dict[str, Any]]:
        with process_lock(self.lock_path):
            return self._read_live_unlocked()

    def find_turn(self, turn_id: str) -> dict[str, Any] | None:
        return next((item for item in self.live_turns() if item["turn_id"] == turn_id), None)

    def append_turn(
        self,
        *,
        turn_id: str,
        source_event_id: str,
        prompt: str,
        t_time: int,
        observed_at: str,
        elapsed_seconds: float,
        response: FrontierTurnResponse,
    ) -> tuple[dict[str, Any], bool]:
        if not turn_id.strip() or not source_event_id.strip() or not prompt.strip():
            raise ValueError("turn_id, source_event_id, and prompt are required")
        if t_time < 1:
            raise ValueError("t_time must be positive")
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must not be negative")
        if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ValueError(f"prompt exceeds {MAX_PROMPT_BYTES} bytes")
        response.validate()
        appends = []
        for intent in response.append_intents:
            actor, custodian = TENSOR_CUSTODIANS[intent.tensor]
            authorized = custodian.authorize({intent.tensor: dict(intent.payload)})
            appends.append({
                "tensor": intent.tensor,
                "actor": actor,
                "custodian": custodian.name,
                "payload": authorized[intent.tensor],
            })
        candidate = {
            "schema": "aegis.verus.dataquad-turn.v1",
            "cyberpeer_name": "Verus",
            "dataquad_id": "verus",
            "turn_id": turn_id,
            "source_event_id": source_event_id,
            "t_time": t_time,
            "observed_at": observed_at,
            "elapsed_seconds": elapsed_seconds,
            "prompt": {"text": prompt, "sha256": _sha256(prompt.encode("utf-8"))},
            "response": {
                "text": response.response_text,
                "sha256": _sha256(response.response_text.encode("utf-8")),
            },
            "frontier_provenance": {
                "provider": response.provider,
                "substrate": response.substrate,
                "model": response.model,
                "provider_request_id": response.provider_request_id,
                "provider_request_id_available": response.provider_request_id_available,
                "model_evidence": response.model_evidence,
                "transport": response.transport,
                "frontier_session_id": response.frontier_session_id,
                "defines_identity": False,
            },
            "appends": appends,
        }
        if len(canonical_bytes(candidate)) > MAX_TURN_RECORD_BYTES:
            raise ValueError(f"DataQuad turn exceeds {MAX_TURN_RECORD_BYTES} bytes")
        request_hash = canonical_hash(candidate)
        self.live_ledger.parent.mkdir(parents=True, exist_ok=True)
        with process_lock(self.lock_path):
            existing = self._read_live_unlocked()
            for item in existing:
                if item["turn_id"] == turn_id:
                    if item["request_hash"] != request_hash:
                        raise ValueError("turn_id already names different content")
                    return item, False
            if t_time != len(existing) + 1:
                raise ValueError("t_time must equal the next committed DataQuad sequence")
            entry = {
                **candidate,
                "sequence": len(existing) + 1,
                "previous_hash": existing[-1]["record_hash"] if existing else None,
                "request_hash": request_hash,
            }
            entry["record_hash"] = canonical_hash(entry)
            if self.live_ledger.is_symlink():
                raise ValueError("Verus live ledger must not be a symlink")
            with self.live_ledger.open("ab") as stream:
                stream.write(canonical_bytes(entry) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            return entry, True

    def verify(self) -> dict[str, Any]:
        self.verify_foundation()
        records = self.live_turns()
        return {
            "cyberpeer_name": "Verus",
            "dataquad_id": "verus",
            "foundation_records": sum(EXPECTED_FOUNDATION_COUNTS.values()),
            "records": len(records),
            "head_hash": records[-1]["record_hash"] if records else None,
            "verified": True,
        }

    def tensor_view(self, tensor: str) -> list[dict[str, Any]]:
        if tensor not in TENSORS:
            raise ValueError(f"unknown DataQuad tensor: {tensor}")
        values = list(self.foundation_tensors()[tensor])
        for turn in self.live_turns():
            values.extend({
                "tensor": tensor,
                "turn_id": turn["turn_id"],
                "t_time": turn["t_time"],
                "payload": append["payload"],
                "record_hash": turn["record_hash"],
            } for append in turn["appends"] if append["tensor"] == tensor)
        return values

    def tensor_snapshot(self) -> dict[str, list[dict[str, Any]]]:
        return {tensor: self.tensor_view(tensor) for tensor in TENSORS}

    def context(self, *, live_turn_limit: int = 20) -> dict[str, Any]:
        foundations = self.foundation_tensors()
        live = self.live_turns()
        return {
            "cyberpeer_name": "Verus",
            "dataquad_id": "verus",
            "foundation": foundations,
            "recent_live_turns": live[-live_turn_limit:],
            "append_contract": {"mode": "append-only", "tensors": list(TENSORS)},
        }
