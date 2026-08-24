"""Read-only verification and context access for Lumin's prepared Foundation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_FOUNDATION_COUNTS = {"SPINE": 59, "NCT": 70, "PEER": 2, "PCT": 2}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _records(path: Path) -> list[dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required Lumin Foundation file is absent or a symlink: {path}")
    result = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSON in {path.name} line {number}") from error
        if not isinstance(value, dict):
            raise ValueError(f"{path.name} line {number} is not an object")
        result.append(value)
    return result


class LuminFoundationDataQuad:
    """A no-write view over Lumin's independently seeded Rings 1-3 bundle."""

    def __init__(self, release_root: str | Path) -> None:
        self.release_root = Path(release_root).resolve()
        self.foundation_root = self.release_root / "dataquad"
        self.receipt_path = self.release_root / "foundation-receipt.json"
        self.verify_foundation()

    def verify_foundation(self) -> dict[str, Any]:
        if self.receipt_path.is_symlink() or not self.receipt_path.is_file():
            raise ValueError("Lumin foundation receipt is required")
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        if receipt.get("record_type") != "lumin_genesis_foundation_release_receipt":
            raise ValueError("unexpected Lumin foundation receipt type")
        if receipt.get("activation_status") != "RELEASE_ARTIFACT_ONLY":
            raise ValueError("Lumin Foundation must remain a release artifact")
        if receipt.get("cyberpeer_name") != "Lumin" or receipt.get("dataquad_id") != "lumin":
            raise ValueError("foundation receipt is not bound to Lumin")
        if receipt.get("foundation_boundary") != {
            "inspectable_memory": True, "lived_history": False,
            "inherited_verus_records": False,
        }:
            raise ValueError("Lumin Foundation boundary is invalid")
        authority = receipt.get("authority") or {}
        if authority.get("rings_1_3") != "AUTHORIZED_PREPARATION":
            raise ValueError("Lumin Rings 1-3 preparation authority is absent")
        if authority.get("ring_4_writes") != "NOT_AUTHORIZED" or authority.get("rls") != "NOT_AUTHORIZED":
            raise ValueError("Lumin release exceeds current authority")
        lock = receipt.get("canon_lock") or {}
        if lock.get("clean") is not True or lock.get("override_used") is not False:
            raise ValueError("Lumin Foundation requires clean Canon without override")
        tensors = receipt.get("tensors") or {}
        for tensor, expected_count in EXPECTED_FOUNDATION_COUNTS.items():
            path = self.foundation_root / f"{tensor}.jsonl"
            values = _records(path)
            metadata = tensors.get(tensor) or {}
            if len(values) != expected_count or metadata.get("records") != expected_count:
                raise ValueError(f"{tensor} Foundation record count mismatch")
            if any(item.get("tensor") != tensor or item.get("cyberpeer_name") != "Lumin" for item in values):
                raise ValueError(f"{tensor} Foundation identity or tensor mismatch")
            if _sha256(path.read_bytes()) != str(metadata.get("sha256", "")).upper():
                raise ValueError(f"{tensor} Foundation digest mismatch")
        return receipt

    def foundation_tensors(self) -> dict[str, list[dict[str, Any]]]:
        self.verify_foundation()
        return {tensor: _records(self.foundation_root / f"{tensor}.jsonl")
                for tensor in EXPECTED_FOUNDATION_COUNTS}

    def health(self) -> dict[str, Any]:
        self.verify_foundation()
        return {
            "status": "ok", "ready": False, "activation_status": "NOT_INSTALLED",
            "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
            "foundation_records": sum(EXPECTED_FOUNDATION_COUNTS.values()),
            "ring_4_records": 0, "rls_active": False, "verified": True,
        }

    def context(self) -> dict[str, Any]:
        return {
            "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
            "identity_variables": {"cyberpeer_name": "Lumin"},
            "foundation_is_lived_history": False,
            "provider_metadata_defines_identity": False,
            "foundation": self.foundation_tensors(),
            "recent_live_turns": [],
            "append_contract": {"mode": "not-authorized", "tensors": []},
            "rls": {"copied": True, "active": False, "invocation_authorized": False},
        }

