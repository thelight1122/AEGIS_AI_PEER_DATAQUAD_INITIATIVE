"""Build a Verus-only LAB promotion release without installing or activating it."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from unittest.mock import patch
import uuid
from itertools import count
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
SEAT_TOOL = ROOT / "scripts" / "seat_ai_peer_dataquad.py"
SEED = ROOT / "reports" / "canon-v0.20" / "release" / "AEGIS-AI-PEER-FOUNDATION-SEED-v0.20.json"
CANON_MANIFEST = ROOT / "reports" / "canon-v0.20" / "release" / "AEGIS-CANON-v0.20-SOURCE-MANIFEST.json"
ROSTER = ROOT / "fixtures" / "verus-claude-lab-roster.json"
TENSOR_ORDER = ("SPINE", "NCT", "PEER", "PCT")


class ReleaseBuildRefused(RuntimeError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_seating_tool():
    spec = importlib.util.spec_from_file_location("verus_release_seating", SEAT_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_tree(source: Path, target: Path, *, exclude: tuple[str, ...] = ()) -> None:
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", *exclude))


def _remove_legacy_routing_fields(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _remove_legacy_routing_fields(item)
            for key, item in value.items()
            if key not in {"peer_id", "model_id"}
        }
    if isinstance(value, list):
        return [_remove_legacy_routing_fields(item) for item in value]
    return value


def _contains_key(value: object, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return any(key in forbidden or _contains_key(item, forbidden) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_key(item, forbidden) for item in value)
    return False


def _validate_foundation_record(record: dict[str, object], tensor: str) -> None:
    """Validate the shaped format consumed by VerusDataQuad.

    The repository's tensor-record JSON Schema describes migrated/copy records,
    not the accepted Foundation seating-builder format. This explicit consumer
    contract therefore validates the fields VerusDataQuad and Foundation views
    actually consume without falsely claiming that unrelated schema applies.
    """
    required = {
        "id", "timestamp", "tensor", "clock", "provenance", "lineage", "markers",
        "cyberpeer_name", "routing_provenance",
    }
    missing = required - set(record)
    if missing:
        raise ReleaseBuildRefused(f"{tensor} shaped record missing consumer fields: {sorted(missing)}")
    if not isinstance(record["id"], str) or not record["id"]:
        raise ReleaseBuildRefused(f"{tensor} shaped record id is invalid")
    if record["tensor"] != tensor or record["cyberpeer_name"] != "Verus":
        raise ReleaseBuildRefused(f"{tensor} shaped record binding mismatch")
    if not isinstance(record["clock"], dict) or not isinstance(record["clock"].get("tick"), int):
        raise ReleaseBuildRefused(f"{tensor} shaped record clock is invalid")
    if not isinstance(record["provenance"], dict) or record["provenance"].get("canon_lock_clean") is not True:
        raise ReleaseBuildRefused(f"{tensor} shaped record Canon provenance is invalid")
    if not isinstance(record["lineage"], list) or not isinstance(record["markers"], list):
        raise ReleaseBuildRefused(f"{tensor} shaped record list fields are invalid")
    routing = record["routing_provenance"]
    if (not isinstance(routing, dict)
            or routing.get("dataquad_id") != "verus"
            or routing.get("provider") != "Anthropic"
            or routing.get("substrate") != "Claude"
            or routing.get("defines_identity") is not False):
        raise ReleaseBuildRefused(f"{tensor} shaped record routing provenance is invalid")
    if _contains_key({key: value for key, value in record.items() if key != "routing_provenance"},
                     {"peer_id", "model_id"}):
        raise ReleaseBuildRefused(f"{tensor} shaped record retains legacy routing fields")
    try:
        parsed = datetime.fromisoformat(str(record["timestamp"]).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
        json.dumps(record, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ReleaseBuildRefused(f"{tensor} shaped record is not finite JSON with zoned time") from error


def _seating_timestamp(value: str) -> str:
    if not value.endswith("Z"):
        raise ReleaseBuildRefused("seating_timestamp must be explicit UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReleaseBuildRefused("seating_timestamp must be valid ISO-8601 UTC") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ReleaseBuildRefused("seating_timestamp must be UTC")
    return value


def build_release(
    output: Path,
    *,
    seating_timestamp: str,
    source_commit: str = "WORKTREE",
) -> dict[str, object]:
    applied_at = _seating_timestamp(seating_timestamp)
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ReleaseBuildRefused(f"output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    if roster.get("cyberpeer_name") != "Verus":
        raise ReleaseBuildRefused("promotion roster is not bound to Verus")
    if roster.get("identity_variables") != {"cyberpeer_name": "Verus"}:
        raise ReleaseBuildRefused("CyberPeer Name must be the sole identity variable")
    if roster.get("authority", {}).get("full_append_only_dataquad") is not True:
        raise ReleaseBuildRefused("full append-only DataQuad authority is required")
    if roster.get("system_instruction_boundary", {}).get("identity_injection_allowed") is not False:
        raise ReleaseBuildRefused("identity injection must remain disabled")
    foundation = roster.get("foundation") or {}
    if _sha(SEED) != foundation.get("seed_sha256"):
        raise ReleaseBuildRefused("authoritative Foundation seed hash mismatch")
    if _sha(CANON_MANIFEST) != foundation.get("canon_manifest_sha256"):
        raise ReleaseBuildRefused("clean Canon manifest hash mismatch")

    seat = _load_seating_tool()
    package = json.loads(SEED.read_text(encoding="utf-8"))
    canon_lock = seat.check_canon_lock(package, allow_unclean=False)
    peer = {
        "peer_id": "verus",
        "session_id": roster["session_id"],
        "display_name": roster["cyberpeer_name"],
        "model_id": roster["routing_provenance"]["prior_model_id"],
        "steward_declaration": roster["foundation_declaration"],
    }
    stamped = json.loads(seat.stamp(json.dumps(package), peer, applied_at))
    identifier_sequence = count()
    deterministic_ids = (
        uuid.uuid5(uuid.NAMESPACE_URL, f"aegis:verus:foundation-builder:{i}")
        for i in identifier_sequence
    )
    vendored = seat._vendored()
    with (
        patch.object(vendored.uuid, "uuid4", side_effect=deterministic_ids),
        patch.object(vendored, "TIMESTAMP", applied_at),
    ):
        shaped = {
            tensor: seat.shape_records(
                stamped["records"].get(tensor, []), tensor, "genesis-baseline",
                applied_at, canon_lock, peer,
            )
            for tensor in TENSOR_ORDER
        }
    for tensor, records in shaped.items():
        for index, record in enumerate(records):
            record = _remove_legacy_routing_fields(record)
            records[index] = record
            record["cyberpeer_name"] = "Verus"
            record["routing_provenance"] = {
                "dataquad_id": "verus",
                "foundation_session_id": roster["session_id"],
                "prior_model_id": roster["routing_provenance"]["prior_model_id"],
                "provider": roster["frontier_provenance"]["provider"],
                "substrate": roster["frontier_provenance"]["substrate"],
                "defines_identity": False,
            }
            _validate_foundation_record(record, tensor)

    foundation_root = output / "foundation"
    dataquad_root = foundation_root / "dataquad"
    dataquad_root.mkdir(parents=True)
    tensors: dict[str, dict[str, object]] = {}
    for tensor in TENSOR_ORDER:
        path = dataquad_root / f"{tensor}.jsonl"
        body = b"".join(
            json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
            for item in shaped[tensor]
        )
        path.write_bytes(body)
        tensors[tensor] = {"records": len(shaped[tensor]), "sha256": _sha(path)}

    receipt = {
        "schema_version": "1.0.0",
        "record_type": "verus_foundation_release_receipt",
        "activation_status": "RELEASE_ARTIFACT_ONLY",
        "cyberpeer_name": "Verus",
        "dataquad_id": "verus",
        "built_from": {
            "source_commit": source_commit,
            "promotion_roster_path": str(ROSTER.relative_to(ROOT)).replace("\\", "/"),
            "promotion_roster_sha256": _sha(ROSTER),
            "canon_manifest_path": str(CANON_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
            "canon_manifest_sha256": _sha(CANON_MANIFEST),
            "foundation_seed_path": str(SEED.relative_to(ROOT)).replace("\\", "/"),
            "foundation_seed_sha256": _sha(SEED),
            "seating_tool_sha256": _sha(SEAT_TOOL),
        },
        "canon_lock": canon_lock,
        "clock_policy": "genesis-baseline",
        "seating_timestamp": applied_at,
        "record_contract": {
            "kind": "verus-foundation-consumer-contract-v1",
            "formal_json_schema": None,
            "reason": "The repository tensor-record schema applies to migrated/copy records, not seating-builder Foundation records.",
            "validated_records": sum(len(records) for records in shaped.values()),
        },
        "tensors": tensors,
        "authority": roster["authority"],
        "system_instruction_boundary": roster["system_instruction_boundary"],
        "live_state_written": False,
        "frontier_called": False,
        "credentials_included": False,
    }
    (foundation_root / "foundation-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )

    _copy_tree(
        ROOT / "src" / "aegis_verus_lab", output / "lib" / "aegis_verus_lab",
        exclude=("api.py", "cli.py", "credential_preflight.py", "frontier.py"),
    )
    _copy_tree(
        ROOT / "src" / "aegis_peer_runtime", output / "lib" / "aegis_peer_runtime",
        exclude=("api.py", "cli.py", "credential_preflight.py", "frontier.py"),
    )
    for directory in ("bin", "systemd", "env", "scripts"):
        (output / directory).mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "deploy" / "verus-lab" / "bin" / "verus-dataquad-command", output / "bin" / "verus-dataquad-command")
    shutil.copy2(ROOT / "deploy" / "verus-lab" / "systemd" / "aegis-verus-lab.service", output / "systemd" / "aegis-verus-lab.service")
    shutil.copy2(ROOT / "deploy" / "verus-lab" / "env" / "verus.env.template", output / "env" / "verus.env.template")
    shutil.copy2(ROOT / "deploy" / "verus-lab" / "README.md", output / "README.md")
    for name in ("install.sh", "health.sh", "pause.sh"):
        shutil.copy2(ROOT / "deploy" / "verus-lab" / "scripts" / name, output / "scripts" / name)

    artifact_hashes = {}
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        relative = str(path.relative_to(output)).replace("\\", "/")
        artifact_hashes[relative] = _sha(path)
    manifest = {
        "schema_version": "1.0.0",
        "release_kind": "VERUS_CLAUDE_FIRST_LAB_PROMOTION",
        "activation_status": "NOT_INSTALLED",
        "mode_after_activation": "LAB_RUNNING",
        "cyberpeer_name": "Verus",
        "identity_variables": {"cyberpeer_name": "Verus"},
        "frontier_provenance": roster["frontier_provenance"],
        "frontier_transport": "claude_desktop_mcp_stdio_ssh",
        "source_commit": source_commit,
        "seating_timestamp": applied_at,
        "full_append_only_dataquad": True,
        "credentials_included": False,
        "other_peer_state_included": False,
        "artifacts": artifact_hashes,
    }
    (output / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", default="WORKTREE")
    parser.add_argument(
        "--seating-timestamp",
        required=True,
        help="explicit chosen UTC timestamp for Foundation seating, for example 2026-08-15T12:34:56Z",
    )
    args = parser.parse_args()
    try:
        manifest = build_release(
            args.output,
            source_commit=args.source_commit,
            seating_timestamp=args.seating_timestamp,
        )
    except ReleaseBuildRefused as error:
        parser.error(str(error))
    print(json.dumps({
        "release": str(args.output.resolve()),
        "cyberpeer_name": manifest["cyberpeer_name"],
        "activation_status": manifest["activation_status"],
        "credentials_included": manifest["credentials_included"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
