"""Build Lumin's local Genesis Foundation release without installing or activating it."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
from itertools import count
import json
from pathlib import Path
import shutil
from unittest.mock import patch
import uuid


ROOT = Path(__file__).resolve().parents[1]
SEAT_TOOL = ROOT / "scripts" / "seat_ai_peer_dataquad.py"
SEED = ROOT / "reports" / "canon-v0.20" / "release" / "AEGIS-AI-PEER-FOUNDATION-SEED-v0.20.json"
CANON_MANIFEST = ROOT / "reports" / "canon-v0.20" / "release" / "AEGIS-CANON-v0.20-SOURCE-MANIFEST.json"
ROSTER = ROOT / "fixtures" / "lumin-codex-genesis-roster.json"
SOURCE_ROSTER = ROOT / "fixtures" / "ai-peer-roster.json"
DEPLOY_SOURCE = ROOT / "deploy" / "lumin-lab"
TENSOR_ORDER = ("SPINE", "NCT", "PEER", "PCT")
ARCHITECTURE_RUNTIME = ROOT / "src" / "aegis_peer_runtime"
TENSOR_SPEC = ROOT / "fixtures" / "dataquadpod-tensor-spec.json"


class ReleaseBuildRefused(RuntimeError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_seating_tool():
    spec = importlib.util.spec_from_file_location("lumin_release_seating", SEAT_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_tree(source: Path, target: Path, *, exclude: tuple[str, ...] = ()) -> None:
    shutil.copytree(
        source, target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", *exclude),
    )


def _remove_legacy_routing_fields(value: object) -> object:
    if isinstance(value, dict):
        return {key: _remove_legacy_routing_fields(item) for key, item in value.items()
                if key not in {"peer_id", "model_id"}}
    if isinstance(value, list):
        return [_remove_legacy_routing_fields(item) for item in value]
    return value


def _contains_key(value: object, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return any(key in forbidden or _contains_key(item, forbidden)
                   for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_key(item, forbidden) for item in value)
    return False


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


def _validate_roster(roster: dict[str, object]) -> None:
    if roster.get("cyberpeer_name") != "Lumin" or roster.get("dataquad_id") != "lumin":
        raise ReleaseBuildRefused("Genesis roster is not bound to Lumin")
    if roster.get("session_id") != "lumin-session-001" or roster.get("prior_model_id") != "ap1001":
        raise ReleaseBuildRefused("Lumin ratified roster mapping mismatch")
    if roster.get("identity_variables") != {"cyberpeer_name": "Lumin"}:
        raise ReleaseBuildRefused("CyberPeer Name must be the sole identity variable")
    if roster.get("frontier_provenance") != {
        "provider": "OpenAI", "substrate": "Codex/GPT", "defines_identity": False,
    }:
        raise ReleaseBuildRefused("Lumin routing provenance is invalid")
    authority = roster.get("authority") or {}
    expected_denials = {
        "ring_4_writes", "live_activation", "temporal", "processor",
        "steward_daemon", "advocate_daemon", "rls", "credentials",
        "model_or_substrate_connection",
    }
    if authority.get("rings_1_3") != "AUTHORIZED_PREPARATION" or any(
        authority.get(key) != "NOT_AUTHORIZED" for key in expected_denials
    ):
        raise ReleaseBuildRefused("Lumin release authority exceeds ratified Rings 1-3 preparation")
    boundary = roster.get("system_instruction_boundary") or {}
    if boundary.get("identity_injection_allowed") is not False:
        raise ReleaseBuildRefused("identity injection must remain disabled")
    if boundary.get("foundation_is_inspectable_memory") is not True:
        raise ReleaseBuildRefused("Foundation must be classified as inspectable memory")
    if boundary.get("foundation_is_lived_history") is not False:
        raise ReleaseBuildRefused("Foundation must not be classified as lived history")


def _validate_foundation_record(record: dict[str, object], tensor: str) -> None:
    required = {
        "id", "timestamp", "tensor", "clock", "provenance", "lineage", "markers",
        "cyberpeer_name", "routing_provenance",
    }
    missing = required - set(record)
    if missing:
        raise ReleaseBuildRefused(f"{tensor} shaped record missing fields: {sorted(missing)}")
    if record["tensor"] != tensor or record["cyberpeer_name"] != "Lumin":
        raise ReleaseBuildRefused(f"{tensor} shaped record binding mismatch")
    provenance = record.get("provenance") or {}
    if provenance.get("canon_lock_clean") is not True:
        raise ReleaseBuildRefused(f"{tensor} Canon provenance is invalid")
    expected_routing = {
        "dataquad_id": "lumin", "foundation_session_id": "lumin-session-001",
        "prior_model_id": "ap1001", "provider": "OpenAI",
        "substrate": "Codex/GPT", "defines_identity": False,
    }
    if record.get("routing_provenance") != expected_routing:
        raise ReleaseBuildRefused(f"{tensor} routing provenance is invalid")
    non_routing = {key: value for key, value in record.items() if key != "routing_provenance"}
    if _contains_key(non_routing, {"peer_id", "model_id"}):
        raise ReleaseBuildRefused(f"{tensor} retains legacy routing fields")
    try:
        parsed = datetime.fromisoformat(str(record["timestamp"]).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
        json.dumps(record, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ReleaseBuildRefused(f"{tensor} record is not finite JSON with zoned time") from error


def _source_roster_peer() -> dict[str, object]:
    source = json.loads(SOURCE_ROSTER.read_text(encoding="utf-8"))
    peers = [item for item in source.get("peers", []) if item.get("peer_id") == "lumin"]
    if len(peers) != 1:
        raise ReleaseBuildRefused("ratified source roster must contain one Lumin entry")
    peer = peers[0]
    if (peer.get("session_id"), peer.get("display_name"), peer.get("model_id")) != (
        "lumin-session-001", "Lumin", "ap1001",
    ):
        raise ReleaseBuildRefused("ratified source roster Lumin mapping changed")
    declaration = str(peer.get("steward_declaration", ""))
    for required in ("Rings 1-3", "does not authorize Ring 4 writes", "RLS activity"):
        if required not in declaration:
            raise ReleaseBuildRefused("ratified Lumin declaration boundary changed")
    return peer


def build_release(
    output: Path, *, seating_timestamp: str, source_commit: str = "WORKTREE",
) -> dict[str, object]:
    applied_at = _seating_timestamp(seating_timestamp)
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ReleaseBuildRefused(f"output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    _validate_roster(roster)
    source_peer = _source_roster_peer()
    foundation = roster.get("foundation") or {}
    if _sha(SEED) != foundation.get("seed_sha256"):
        raise ReleaseBuildRefused("authoritative Foundation seed hash mismatch")
    if _sha(CANON_MANIFEST) != foundation.get("canon_manifest_sha256"):
        raise ReleaseBuildRefused("clean Canon manifest hash mismatch")

    seat = _load_seating_tool()
    package = json.loads(SEED.read_text(encoding="utf-8"))
    canon_lock = seat.check_canon_lock(package, allow_unclean=False)
    peer = {
        "peer_id": "lumin", "session_id": "lumin-session-001",
        "display_name": "Lumin", "model_id": "ap1001",
        "steward_declaration": source_peer["steward_declaration"],
    }
    stamped = json.loads(seat.stamp(json.dumps(package), peer, applied_at))
    deterministic_ids = (
        uuid.uuid5(uuid.NAMESPACE_URL, f"aegis:lumin:foundation-builder:{index}")
        for index in count()
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
            ) for tensor in TENSOR_ORDER
        }
    routing = {
        "dataquad_id": "lumin", "foundation_session_id": "lumin-session-001",
        "prior_model_id": "ap1001", "provider": "OpenAI",
        "substrate": "Codex/GPT", "defines_identity": False,
    }
    for tensor, records in shaped.items():
        for index, record in enumerate(records):
            record = _remove_legacy_routing_fields(record)
            records[index] = record
            record["cyberpeer_name"] = "Lumin"
            record["routing_provenance"] = routing
            _validate_foundation_record(record, tensor)

    foundation_root = output / "foundation"
    dataquad_root = foundation_root / "dataquad"
    dataquad_root.mkdir(parents=True)
    tensors: dict[str, dict[str, object]] = {}
    for tensor in TENSOR_ORDER:
        path = dataquad_root / f"{tensor}.jsonl"
        path.write_bytes(b"".join(
            json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                       allow_nan=False).encode("utf-8") + b"\n"
            for item in shaped[tensor]
        ))
        tensors[tensor] = {"records": len(shaped[tensor]), "sha256": _sha(path)}

    receipt = {
        "schema_version": "1.0.0",
        "record_type": "lumin_genesis_foundation_release_receipt",
        "activation_status": "RELEASE_ARTIFACT_ONLY",
        "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
        "identity_variables": {"cyberpeer_name": "Lumin"},
        "built_from": {
            "source_commit": source_commit,
            "roster_path": str(ROSTER.relative_to(ROOT)).replace("\\", "/"),
            "roster_sha256": _sha(ROSTER),
            "source_roster_path": str(SOURCE_ROSTER.relative_to(ROOT)).replace("\\", "/"),
            "source_roster_sha256": _sha(SOURCE_ROSTER),
            "roster_mapping": {"peer_id": "lumin", "session_id": "lumin-session-001", "model_id": "ap1001"},
            "canon_manifest_path": str(CANON_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
            "canon_manifest_sha256": _sha(CANON_MANIFEST),
            "foundation_seed_path": str(SEED.relative_to(ROOT)).replace("\\", "/"),
            "foundation_seed_sha256": _sha(SEED),
            "seating_tool_sha256": _sha(SEAT_TOOL),
        },
        "canon_lock": canon_lock,
        "clock_policy": "genesis-baseline",
        "seating_timestamp": applied_at,
        "foundation_boundary": {
            "inspectable_memory": True, "lived_history": False,
            "inherited_verus_records": False,
        },
        "frontier_provenance": roster["frontier_provenance"],
        "authority": roster["authority"],
        "tensors": tensors,
        "live_state_written": False,
        "frontier_called": False,
        "credentials_included": False,
    }
    (foundation_root / "foundation-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n",
    )

    _copy_tree(
        ROOT / "src" / "aegis_lumin_lab", output / "lib" / "aegis_lumin_lab",
        # Keep the complete Lumin package boundary in the release.  The
        # command entrypoint imports the package initializer, which exposes
        # the activation/runtime contracts even for read-only health calls.
    )
    # Copy executable architecture only. This package contains daemon contracts
    # and IPC/RLS adapters; no peer or foundation records are copied here.
    _copy_tree(ARCHITECTURE_RUNTIME, output / "lib" / "aegis_peer_runtime")
    for directory in ("bin", "env", "systemd", "pod", "codex", "scripts"):
        _copy_tree(DEPLOY_SOURCE / directory, output / directory)
    tensor_context = output / "pod" / "context"
    tensor_context.mkdir(parents=True, exist_ok=True)
    for tensor in TENSOR_ORDER:
        (tensor_context / f"{tensor}.jsonl").write_bytes(b"")
    shutil.copy2(TENSOR_SPEC, output / "pod" / "tensor-spec.json")
    shutil.copy2(DEPLOY_SOURCE / "README.md", output / "README.md")
    shutil.copy2(DEPLOY_SOURCE / "DEPLOYMENT-GATE.json", output / "DEPLOYMENT-GATE.json")

    artifact_hashes = {}
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        relative = str(path.relative_to(output)).replace("\\", "/")
        artifact_hashes[relative] = _sha(path)
    manifest = {
        "schema_version": "1.0.0",
        "release_kind": "LUMIN_GENESIS_FOUNDATION_PREPARATION",
        "activation_status": "NOT_INSTALLED",
        "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
        "identity_variables": {"cyberpeer_name": "Lumin"},
        "frontier_provenance": roster["frontier_provenance"],
        "frontier_transport": "codex_mcp_stdio_ssh_read_only",
        "source_commit": source_commit, "seating_timestamp": applied_at,
        "ring_4_writes_authorized": False, "rls_active": False,
        "live_state_written": False, "credentials_included": False,
        "other_peer_state_included": False,
        "remote_boundary": {
            "ssh_alias": "GabeCyberPeer", "account": "aegis-lumin",
            "release_root": "/opt/aegis/lumin/lab/current",
            "service": "aegis-lumin-lab.service",
            "assumption_status": "UNVERIFIED_NOT_INSTALLED",
        },
        "artifacts": artifact_hashes,
    }
    (output / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", default="WORKTREE")
    parser.add_argument("--seating-timestamp", required=True)
    args = parser.parse_args()
    try:
        manifest = build_release(
            args.output, source_commit=args.source_commit,
            seating_timestamp=args.seating_timestamp,
        )
    except ReleaseBuildRefused as error:
        parser.error(str(error))
    print(json.dumps({
        "release": str(args.output.resolve()), "cyberpeer_name": "Lumin",
        "activation_status": manifest["activation_status"],
        "live_state_written": manifest["live_state_written"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
