#!/usr/bin/env bash
set -euo pipefail

RELEASE_ROOT=${1:-/opt/aegis/lumin/lab/current}

if [[ ! -f "$RELEASE_ROOT/release-manifest.json" ]]; then
  echo "Lumin release manifest is absent" >&2
  exit 2
fi

python3 - "$RELEASE_ROOT" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
manifest = json.loads((root / "release-manifest.json").read_text(encoding="utf-8"))
if manifest.get("activation_status") != "NOT_INSTALLED":
    raise SystemExit("Lumin release exceeded the NOT_INSTALLED gate")
if manifest.get("ring_4_writes_authorized") is not False:
    raise SystemExit("Lumin Ring 4 writes must remain unauthorized")
if manifest.get("rls_active") is not False:
    raise SystemExit("Lumin RLS must remain inactive")
completed = subprocess.run(
    [sys.executable, str(root / "bin" / "lumin-dataquad-command"), "health",
     "--release-root", str(root / "foundation")],
    text=True, capture_output=True, check=False,
)
if completed.returncode:
    raise SystemExit(completed.stderr or "Lumin Foundation health failed")
health = json.loads(completed.stdout)
if health.get("verified") is not True or health.get("ready") is not False:
    raise SystemExit("Lumin Foundation is not verified in inactive state")
print(json.dumps(health, sort_keys=True))
PY
