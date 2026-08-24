"""Build an immutable Lumin release carrying query-and-record support."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "deploy" / "lumin-lab" / "releases" / "20260819T000700Z-query-record"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def build(output: Path, released_at: str) -> dict[str, object]:
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"output must be absent or empty: {output}")
    old = json.loads((BASE / "release-manifest.json").read_text(encoding="utf-8"))
    # The prior pod-clone manifest predates a harmless remote byte-for-byte
    # refresh of vendored daemon files.  Require the immutable Foundation and
    # POD artifacts to match; regenerate hashes for the complete new release.
    for relative in (
        "foundation/foundation-receipt.json",
        "foundation/dataquad/PEER.jsonl", "foundation/dataquad/PCT.jsonl",
        "foundation/dataquad/NCT.jsonl", "foundation/dataquad/SPINE.jsonl",
        "pod/lumin-cyberpeer-pod.json",
    ):
        if not (BASE / relative).is_file():
            raise ValueError(f"active baseline artifact missing: {relative}")
    shutil.copytree(BASE, output)
    (output / "release-manifest.json").unlink()
    lib = output / "lib"
    for package in ("aegis_lumin_lab",):
        shutil.rmtree(lib / package)
        shutil.copytree(ROOT / "src" / package, lib / package,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    artifacts = {
        str(path.relative_to(output)).replace("\\", "/"): sha(path)
        for path in sorted(p for p in output.rglob("*") if p.is_file())
    }
    manifest = {
        **old,
        "release_kind": "LUMIN_QUERY_RECORD",
        "activation_status": "READY_TO_ROLL_FORWARD",
        "released_at": released_at,
        "rollback_release": "/opt/aegis/lumin/lab/releases/20260818T235100Z-podclone-active",
        "query_record_contract": {
            "tool": "lumin_query_and_record",
            "query_first": True,
            "append_only": True,
            "assistant_response_required": True,
            "reason": "MCP cannot observe host assistant output after tool return",
            "recorded_tensors": ["PEER", "PCT", "NCT", "SPINE"],
        },
        "artifacts": artifacts,
    }
    (output / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--released-at", required=True)
    args = parser.parse_args()
    result = build(args.output, args.released_at)
    print(json.dumps({"release": str(args.output), "manifest_sha256": sha(args.output / "release-manifest.json")}, sort_keys=True))
