#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo "run as root" >&2; exit 2; fi
BUNDLE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
RELEASE_ID=${RELEASE_ID:?RELEASE_ID is required}
FRONTIER_MODEL=${FRONTIER_MODEL:?exact Anthropic FRONTIER_MODEL is required}
VERUS_PORT=${VERUS_PORT:-8791}
[[ "$RELEASE_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || { echo "invalid RELEASE_ID" >&2; exit 3; }
[[ "$FRONTIER_MODEL" =~ ^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$ ]] || { echo "invalid FRONTIER_MODEL" >&2; exit 3; }
[[ "$VERUS_PORT" =~ ^[0-9]+$ ]] && (( VERUS_PORT >= 1024 && VERUS_PORT <= 65535 )) || { echo "invalid VERUS_PORT" >&2; exit 3; }
if ss -H -ltn "sport = :$VERUS_PORT" | grep -q .; then
  echo "Verus loopback port is already in use; choose a distinct VERUS_PORT after read-only review." >&2
  exit 4
fi
python3 - "$BUNDLE_ROOT" <<'PY'
import hashlib, json, pathlib, sys
root=pathlib.Path(sys.argv[1])
manifest_path=root / "release-manifest.json"
manifest=json.load(manifest_path.open(encoding="utf-8"))
assert manifest["release_kind"] == "VERUS_CLAUDE_FIRST_LAB_PROMOTION"
assert manifest["cyberpeer_name"] == "Verus"
assert manifest["identity_variables"] == {"cyberpeer_name": "Verus"}
assert manifest["full_append_only_dataquad"] is True
assert manifest["credentials_included"] is False
for relative, expected in manifest["artifacts"].items():
    observed=hashlib.sha256((root / relative).read_bytes()).hexdigest().upper()
    assert observed == expected, f"release artifact hash mismatch: {relative}"
PY
INSTALL_ROOT=/opt/aegis/verus/lab
RELEASE_DIR="$INSTALL_ROOT/releases/$RELEASE_ID"
[[ ! -e "$RELEASE_DIR" ]] || { echo "release already exists: $RELEASE_DIR" >&2; exit 5; }
PRIOR_CURRENT=$(readlink -f "$INSTALL_ROOT/current" 2>/dev/null || true)
if systemctl is-active --quiet aegis-verus-lab.service; then PRIOR_SERVICE_ACTIVE=yes; else PRIOR_SERVICE_ACTIVE=no; fi
if systemctl is-enabled --quiet aegis-verus-lab.service; then PRIOR_SERVICE_ENABLED=yes; else PRIOR_SERVICE_ENABLED=no; fi
RECOVERY_DIR="/var/lib/aegis-verus-lab/install-recovery/$RELEASE_ID"
restore_or_pause_on_error() {
  status=$?
  trap - ERR
  set +e
  if [[ -n "$PRIOR_CURRENT" && -d "$PRIOR_CURRENT" ]]; then
    ln -sfn "$PRIOR_CURRENT" "$INSTALL_ROOT/current.restore"
    mv -Tf "$INSTALL_ROOT/current.restore" "$INSTALL_ROOT/current"
    if [[ -f "$RECOVERY_DIR/aegis-verus-lab.service" ]]; then
      install -o root -g root -m 0644 "$RECOVERY_DIR/aegis-verus-lab.service" /etc/systemd/system/aegis-verus-lab.service
    fi
    systemctl daemon-reload
    if [[ "$PRIOR_SERVICE_ENABLED" == yes ]]; then
      systemctl enable aegis-verus-lab.service
    else
      systemctl disable aegis-verus-lab.service
    fi
    if [[ "$PRIOR_SERVICE_ACTIVE" == yes ]]; then
      systemctl restart aegis-verus-lab.service
      if [[ -x "$PRIOR_CURRENT/scripts/health.sh" ]] && ! "$PRIOR_CURRENT/scripts/health.sh"; then
        systemctl stop aegis-verus-lab.service
        echo "Prior Verus release was restored but failed health; service paused safely." >&2
      fi
    else
      systemctl stop aegis-verus-lab.service
    fi
    echo "Verus install failed; prior release and service state restored." >&2
  else
    systemctl stop aegis-verus-lab.service
    systemctl disable aegis-verus-lab.service
    echo "Verus install failed; no prior release existed, so the service is paused and state is preserved." >&2
  fi
  exit "$status"
}
trap restore_or_pause_on_error ERR
identity=aegis-verus
getent group "$identity" >/dev/null || groupadd --system "$identity"
id "$identity" >/dev/null 2>&1 || useradd --system --gid "$identity" --home-dir /nonexistent --shell /usr/sbin/nologin "$identity"
install -d -o root -g root -m 0755 /opt/aegis /opt/aegis/verus "$INSTALL_ROOT" "$INSTALL_ROOT/releases"
install -d -o root -g "$identity" -m 0750 /etc/aegis-verus-lab
install -d -o "$identity" -g "$identity" -m 0700 /var/lib/aegis-verus-lab
install -d -o root -g root -m 0700 "$RECOVERY_DIR"
if [[ -f /etc/systemd/system/aegis-verus-lab.service ]]; then
  install -o root -g root -m 0600 /etc/systemd/system/aegis-verus-lab.service "$RECOVERY_DIR/aegis-verus-lab.service"
fi
install -d -o root -g root -m 0755 "$RELEASE_DIR"
cp -a "$BUNDLE_ROOT/." "$RELEASE_DIR/"
chown -R root:root "$RELEASE_DIR"
chmod 0755 "$RELEASE_DIR/bin/verus-dataquad-command"
if [[ ! -e /etc/aegis-verus-lab/verus.env ]]; then
  sed -e "s/SET_AT_ACTIVATION/$FRONTIER_MODEL/" -e "s/SET_PORT_AT_ACTIVATION/$VERUS_PORT/" \
    "$BUNDLE_ROOT/env/verus.env.template" > /etc/aegis-verus-lab/verus.env
  chown root:"$identity" /etc/aegis-verus-lab/verus.env
  chmod 0640 /etc/aegis-verus-lab/verus.env
fi
install -o root -g root -m 0644 "$BUNDLE_ROOT/systemd/aegis-verus-lab.service" /etc/systemd/system/aegis-verus-lab.service
ln -sfn "$RELEASE_DIR" "$INSTALL_ROOT/current.new"
mv -Tf "$INSTALL_ROOT/current.new" "$INSTALL_ROOT/current"
systemctl daemon-reload
systemctl enable --now aegis-verus-lab.service
VERUS_COMMAND="$RELEASE_DIR/bin/verus-dataquad-command" "$RELEASE_DIR/scripts/health.sh"
trap - ERR
echo "Installed Verus LAB release $RELEASE_ID; historical peer roots were not modified."
