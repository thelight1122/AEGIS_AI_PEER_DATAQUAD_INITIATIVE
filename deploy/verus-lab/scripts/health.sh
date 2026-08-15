#!/usr/bin/env bash
set -euo pipefail
COMMAND=${VERUS_COMMAND:-/opt/aegis/verus/lab/current/bin/verus-dataquad-command}
[[ -x "$COMMAND" ]] || { echo "Verus command surface is unavailable" >&2; exit 2; }
printf '{}' | "$COMMAND" health | python3 -c '
import json,sys
v=json.load(sys.stdin)
assert v["status"]=="ok" and v["mode"]=="LAB_RUNNING" and v["ready"] is True
assert v["cyberpeer_name"]=="Verus" and v["full_append_only"] is True
assert set(v["writable_tensors"])=={"PEER","PCT","NCT","SPINE"}
assert v["integrity"]["foundation_records"]==133 and v["integrity"]["verified"] is True
assert v["coherence"]["coherent"] is True
assert v["public_listener"] is False and v["preferred_loopback_port"]==8791
print("healthy Verus LAB_RUNNING")'
