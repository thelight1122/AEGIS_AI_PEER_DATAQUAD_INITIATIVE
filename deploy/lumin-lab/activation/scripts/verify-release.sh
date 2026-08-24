#!/usr/bin/env bash
set -euo pipefail

RELEASE_ROOT=${1:?explicit Lumin release root required}
python3 - "$RELEASE_ROOT" <<'PY'
import hashlib, json, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
manifest = json.loads((root / "release-manifest.json").read_text(encoding="utf-8"))
if manifest.get("release_kind") not in {"LUMIN_LIVE_ACTIVATION", "LUMIN_PROVENANCE_REMEDIATION"}:
    raise SystemExit("not a Lumin activation/remediation release")
if manifest.get("full_append_only_dataquad") is not True or manifest.get("rls_active") is not True:
    raise SystemExit("Lumin activation authorities are absent")
expected = manifest["artifacts"]
actual = {
    str(path.relative_to(root)).replace("\\", "/")
    for path in root.rglob("*") if path.is_file() and path.name != "release-manifest.json"
}
if actual != set(expected):
    raise SystemExit("release artifact set mismatch")
for relative, digest in expected.items():
    observed = hashlib.sha256((root / relative).read_bytes()).hexdigest().upper()
    if observed != digest:
        raise SystemExit(f"release digest mismatch: {relative}")
print(json.dumps({"verified": True, "artifacts": len(expected)}, sort_keys=True))
PY
