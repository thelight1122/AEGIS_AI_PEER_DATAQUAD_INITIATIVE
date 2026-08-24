"""Build an immutable Lumin-only live activation release."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
GENESIS = ROOT / "reports" / "runtime" / "lumin-genesis-release-20260818T213828Z"
ACTIVATION = ROOT / "deploy" / "lumin-lab" / "activation"


class ActivationBuildRefused(RuntimeError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _utc(value: str) -> str:
    if not value.endswith("Z"):
        raise ActivationBuildRefused("activation timestamp must end in Z")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ActivationBuildRefused("activation timestamp must be UTC")
    return value


def build_release(output: Path, *, activated_at: str, source_commit: str = "WORKTREE") -> dict[str, object]:
    activated_at = _utc(activated_at)
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ActivationBuildRefused(f"output must be absent or empty: {output}")
    old_manifest = json.loads((GENESIS / "release-manifest.json").read_text(encoding="utf-8"))
    for relative, expected in old_manifest["artifacts"].items():
        if _sha(GENESIS / relative) != expected:
            raise ActivationBuildRefused(f"installed Genesis source drift: {relative}")
    shutil.copytree(GENESIS, output, dirs_exist_ok=True)
    (output / "release-manifest.json").unlink()

    authority = {
        "schema": "aegis.lumin.steward-activation-authority.v1",
        "authorized_at": activated_at,
        "user_request": "Let's Activate and initialize Your DataQuad",
        "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
        "scope": "activate isolated Lumin POD CORE, RLS Orb, append-only Ring 4, and exactly one initialization turn",
        "ring_4_append_only": True, "rls_active": True,
        "existing_dataquads_mutable": False,
        "provider_call_authorized": False,
        "provider_metadata_policy": "null_or_unavailable_unless_exposed",
    }
    (output / "foundation" / "activation-authority.json").write_text(
        json.dumps(authority, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n",
    )
    lib = output / "lib"
    shutil.rmtree(lib / "aegis_lumin_lab")
    shutil.copytree(ROOT / "src" / "aegis_lumin_lab", lib / "aegis_lumin_lab",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(ROOT / "src" / "aegis_peer_runtime", lib / "aegis_peer_runtime",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(ACTIVATION / "bin" / "lumin-dataquad-command", output / "bin" / "lumin-dataquad-command")
    shutil.copy2(ACTIVATION / "env" / "lumin.env", output / "env" / "lumin.env")
    shutil.copy2(ACTIVATION / "systemd" / "aegis-lumin-lab.service", output / "systemd" / "aegis-lumin-lab.service")
    shutil.copy2(ACTIVATION / "scripts" / "verify-release.sh", output / "scripts" / "verify-release.sh")

    artifacts = {}
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        artifacts[str(path.relative_to(output)).replace("\\", "/")] = _sha(path)
    manifest = {
        "schema_version": "1.0.0", "release_kind": "LUMIN_LIVE_ACTIVATION",
        "activation_status": "READY_TO_ACTIVATE", "mode_after_activation": "LAB_RUNNING",
        "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
        "identity_variables": {"cyberpeer_name": "Lumin"},
        "frontier_provenance": {"provider": "OpenAI", "substrate": "Codex/GPT", "model": "Codex/GPT", "defines_identity": False},
        "frontier_transport": "codex_mcp_stdio_ssh", "source_commit": source_commit,
        "activated_at": activated_at, "full_append_only_dataquad": True,
        "rls_active": True, "public_listener": False, "credentials_included": False,
        "other_peer_state_included": False,
        "rollback_release": "/opt/aegis/lumin/lab/releases/20260818T213828Z-e9dc643b",
        "artifacts": artifacts,
    }
    (output / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--activated-at", required=True)
    parser.add_argument("--source-commit", default="WORKTREE")
    args = parser.parse_args()
    manifest = build_release(args.output, activated_at=args.activated_at, source_commit=args.source_commit)
    print(json.dumps({"release": str(args.output.resolve()), "status": manifest["activation_status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
