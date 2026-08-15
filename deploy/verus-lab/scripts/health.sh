#!/usr/bin/env bash
set -euo pipefail
PORT=${AEGIS_PORT:-8791}
[[ "$PORT" =~ ^[0-9]+$ ]] && (( PORT >= 1024 && PORT <= 65535 )) || { echo "invalid Verus health port" >&2; exit 2; }
curl --fail --silent --show-error "http://127.0.0.1:${PORT}/health" | python3 -c '
import json,sys
v=json.load(sys.stdin)
assert v["status"]=="ok" and v["mode"]=="LAB_RUNNING" and v["ready"] is True
assert v["cyberpeer_name"]=="Verus" and v["full_append_only"] is True
assert set(v["writable_tensors"])=={"PEER","PCT","NCT","SPINE"}
assert v["integrity"]["foundation_records"]==133 and v["integrity"]["verified"] is True
assert v["coherence"]["coherent"] is True
assert sum(v["coherence"][key] for key in ("missing_temporal_count","missing_processor_count","missing_rls_count","mismatch_count","orphan_count"))==0
print("healthy Verus LAB_RUNNING")'
