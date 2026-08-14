#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo "run as root" >&2; exit 2; fi
TARGET_FILE=/opt/aegis-ai-peers/rollback-target
[[ -f "$TARGET_FILE" ]] || { echo "no rollback target" >&2; exit 3; }
TARGET=$(cat "$TARGET_FILE")
[[ "$TARGET" == /opt/aegis-ai-peers/releases/* && -d "$TARGET" ]] || { echo "invalid rollback target" >&2; exit 4; }
ln -sfn "$TARGET" /opt/aegis-ai-peers/current.new
mv -Tf /opt/aegis-ai-peers/current.new /opt/aegis-ai-peers/current
for peer in lumin claude gemini grok; do systemctl restart "aegis-ai-peer@$peer.service"; done
"$(dirname "${BASH_SOURCE[0]}")/health.sh"
echo "Rolled back to $TARGET"
