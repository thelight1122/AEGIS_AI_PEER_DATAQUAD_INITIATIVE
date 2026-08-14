#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo "run as root" >&2; exit 2; fi
BUNDLE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
SOURCE_COMMIT=${SOURCE_COMMIT:-UNKNOWN}
RELEASE_ID=${RELEASE_ID:-$(date -u +%Y%m%dT%H%M%SZ)}
[[ "$RELEASE_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || { echo "invalid RELEASE_ID" >&2; exit 3; }
INSTALL_ROOT=/opt/aegis-ai-peers
RELEASE_DIR="$INSTALL_ROOT/releases/$RELEASE_ID"
PEERS=(lumin claude gemini grok)
install -d -o root -g root -m 0755 "$INSTALL_ROOT/releases" /etc/aegis-ai-peers
install -d -o root -g root -m 0755 "$RELEASE_DIR/bin"
install -o root -g root -m 0755 "$BUNDLE_ROOT/bin/aegis-ai-peer-unseated" "$RELEASE_DIR/bin/"
for peer in "${PEERS[@]}"; do
  identity="aegis-ai-peer-$peer"
  getent group "$identity" >/dev/null || groupadd --system "$identity"
  id "$identity" >/dev/null 2>&1 || useradd --system --gid "$identity" --home-dir /nonexistent --shell /usr/sbin/nologin "$identity"
  install -d -o "$identity" -g "$identity" -m 0700 "/var/lib/aegis-ai-peers/$peer"
  if [[ ! -e "/etc/aegis-ai-peers/$peer.env" ]]; then
    install -o root -g "$identity" -m 0640 "$BUNDLE_ROOT/env/$peer.env" "/etc/aegis-ai-peers/$peer.env"
  fi
done
install -o root -g root -m 0644 "$BUNDLE_ROOT/systemd/aegis-ai-peer@.service" /etc/systemd/system/
python3 "$BUNDLE_ROOT/scripts/render_manifest.py" --bundle "$BUNDLE_ROOT" --output "$RELEASE_DIR/deployment-manifest.json" --release "$RELEASE_ID" --commit "$SOURCE_COMMIT"
ln -sfn "$RELEASE_DIR" "$INSTALL_ROOT/current.new"
mv -Tf "$INSTALL_ROOT/current.new" "$INSTALL_ROOT/current"
systemctl daemon-reload
for peer in "${PEERS[@]}"; do systemctl enable --now "aegis-ai-peer@$peer.service"; done
echo "Installed UNSEATED release $RELEASE_ID"
