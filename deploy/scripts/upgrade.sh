#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo "run as root" >&2; exit 2; fi
BUNDLE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
CURRENT=$(readlink -f /opt/aegis-ai-peers/current 2>/dev/null || true)
[[ -n "$CURRENT" ]] && printf '%s\n' "$CURRENT" > /opt/aegis-ai-peers/rollback-target
rollback_on_error() {
  status=$?
  trap - ERR
  set +e
  "$BUNDLE_ROOT/scripts/rollback.sh"
  exit "$status"
}
trap rollback_on_error ERR
SOURCE_COMMIT=${SOURCE_COMMIT:-UNKNOWN} RELEASE_ID=${RELEASE_ID:-$(date -u +%Y%m%dT%H%M%SZ)} "$BUNDLE_ROOT/scripts/install.sh"
for peer in lumin claude gemini grok; do
  systemctl restart "aegis-ai-peer@$peer.service"
done
"$BUNDLE_ROOT/scripts/health.sh"
trap - ERR
