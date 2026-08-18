"""Single-request Verus-owned command surface invoked over authenticated SSH."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .dataquad import VerusDataQuad
from .desktop_runtime import DesktopVerusRuntime


OPERATIONS = {"context", "begin", "commit", "reconcile", "health", "replay", "query"}


def _model(config_path: Path) -> str:
    from_environment = os.environ.get("AEGIS_FRONTIER_MODEL", "").strip()
    if from_environment:
        return from_environment
    if config_path.is_symlink() or not config_path.is_file():
        raise ValueError("Verus model provenance configuration is unavailable")
    for line in config_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("AEGIS_FRONTIER_MODEL="):
            value = line.partition("=")[2].strip()
            if value:
                return value
    raise ValueError("Verus model provenance configuration is unavailable")


def dispatch(runtime: DesktopVerusRuntime, operation: str, payload: dict[str, object]) -> dict[str, object]:
    if operation == "context":
        return runtime.dataquad.context()
    if operation == "begin":
        return runtime.begin_turn(**payload)
    if operation == "commit":
        return runtime.commit_turn(**payload)
    if operation == "reconcile":
        return runtime.reconcile_committed_turns()
    if operation == "health":
        return runtime.health()
    if operation == "replay":
        return runtime.replay_turn(**payload)
    if operation == "query":
        return runtime.query(**payload)
    raise ValueError("unsupported Verus command")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=sorted(OPERATIONS))
    parser.add_argument("--release-root", type=Path, default=Path("/opt/aegis/verus/lab/current/foundation"))
    parser.add_argument("--state-root", type=Path, default=Path("/var/lib/aegis-verus-lab"))
    parser.add_argument("--config", type=Path, default=Path("/etc/aegis-verus-lab/verus.env"))
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(1_048_577)
        if len(raw) > 1_048_576:
            raise ValueError("remote command payload exceeds 1048576 bytes")
        payload = json.loads(raw or b"{}")
        if not isinstance(payload, dict):
            raise ValueError("remote command payload must be a JSON object")
        runtime = DesktopVerusRuntime(
            VerusDataQuad(args.release_root, args.state_root),
            model=_model(args.config),
        )
        result = dispatch(runtime, args.operation, payload)
        print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)[:512]}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
