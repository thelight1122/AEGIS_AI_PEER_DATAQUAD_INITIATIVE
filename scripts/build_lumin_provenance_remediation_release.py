"""Build a new immutable Lumin-only provenance-remediation release."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports" / "runtime" / "lumin-activation-release-20260818T221152Z"
ACTIVATION = ROOT / "deploy" / "lumin-lab" / "activation"
AUTHORITY = ROOT / "deploy" / "lumin-lab" / "correction" / "correction-authority.json"
ROLLBACK = "/opt/aegis/lumin/lab/releases/20260818T221152Z-5bdbaa4e"


class RemediationBuildRefused(RuntimeError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _utc(value: str) -> str:
    if not value.endswith("Z"):
        raise RemediationBuildRefused("release timestamp must end in Z")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise RemediationBuildRefused("release timestamp must be UTC")
    return value


def build_release(output: Path, *, released_at: str, source_commit: str = "WORKTREE") -> dict[str, object]:
    released_at = _utc(released_at)
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise RemediationBuildRefused(f"output must be absent or empty: {output}")
    old_manifest = json.loads((BASE / "release-manifest.json").read_text(encoding="utf-8"))
    for relative, expected in old_manifest["artifacts"].items():
        if _sha(BASE / relative) != expected:
            raise RemediationBuildRefused(f"base activation release drift: {relative}")
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if (
        authority.get("user_authorization") != "Authorized. Proceed"
        or authority.get("correction_of_record_hash")
        != "0A005A16DFA3ED7197319E38A3FEAD3715D488BC3945E070C32DD521C8D7AD19"
    ):
        raise RemediationBuildRefused("correction authority is not bound to the preserved shortfall")

    shutil.copytree(BASE, output, dirs_exist_ok=True)
    (output / "release-manifest.json").unlink()
    lib = output / "lib"
    shutil.rmtree(lib / "aegis_lumin_lab")
    shutil.copytree(
        ROOT / "src" / "aegis_lumin_lab", lib / "aegis_lumin_lab",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copy2(ACTIVATION / "env" / "lumin.env", output / "env" / "lumin.env")
    shutil.copy2(ACTIVATION / "scripts" / "verify-release.sh", output / "scripts" / "verify-release.sh")
    shutil.copy2(AUTHORITY, output / "foundation" / "correction-authority.json")

    artifacts = {
        str(path.relative_to(output)).replace("\\", "/"): _sha(path)
        for path in sorted(item for item in output.rglob("*") if item.is_file())
    }
    manifest = {
        "schema_version": "1.0.0",
        "release_kind": "LUMIN_PROVENANCE_REMEDIATION",
        "activation_status": "READY_TO_REMEDIATE_AND_REACTIVATE",
        "mode_after_activation": "LAB_RUNNING",
        "cyberpeer_name": "Lumin",
        "dataquad_id": "lumin",
        "identity_variables": {"cyberpeer_name": "Lumin"},
        "frontier_provenance": {
            "provider": "OpenAI", "substrate": "Codex/GPT",
            "model": None, "model_available": False,
            "model_evidence": "unavailable:not_exposed_by_codex_mcp_boundary",
            "defines_identity": False,
        },
        "frontier_transport": "codex_mcp_stdio_ssh",
        "source_commit": source_commit,
        "released_at": released_at,
        "full_append_only_dataquad": True,
        "rls_active": True,
        "public_listener": False,
        "credentials_included": False,
        "other_peer_state_included": False,
        "correction_of_record_hash": authority["correction_of_record_hash"],
        "rollback_release": ROLLBACK,
        "artifacts": artifacts,
    }
    (output / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--released-at", required=True)
    parser.add_argument("--source-commit", default="WORKTREE")
    args = parser.parse_args()
    manifest = build_release(args.output, released_at=args.released_at, source_commit=args.source_commit)
    print(json.dumps({"release": str(args.output.resolve()), "status": manifest["activation_status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
