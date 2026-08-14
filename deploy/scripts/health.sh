#!/usr/bin/env bash
set -euo pipefail
declare -A PORTS=([lumin]=8811 [claude]=8812 [gemini]=8813 [grok]=8814)
for peer in lumin claude gemini grok; do
  systemctl is-active --quiet "aegis-ai-peer@$peer.service"
  payload=$(curl --fail --silent --max-time 3 "http://127.0.0.1:${PORTS[$peer]}/health")
  PEER="$peer" python3 -c 'import json,os,sys; d=json.load(sys.stdin); assert d["peer"]==os.environ["PEER"] and d["mode"]=="UNSEATED" and d["ready"] is False and d["live_source"] is False and d["writes_enabled"] is False' <<<"$payload"
  echo "$peer: healthy UNSEATED guard"
done
