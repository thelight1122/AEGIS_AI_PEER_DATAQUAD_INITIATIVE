#!/bin/sh
set -eu

# Private first-activation route: MCP stdio travels through SSH; the Portal
# credential is read locally on the VM and is never placed in arguments.
TOKEN_FILE=/home/aegisadmin/.config/aegis/portal-gateway.token
export AEGIS_PORTAL_TOKEN="$(cat "$TOKEN_FILE")"
export AEGIS_PORTAL_URL=http://127.0.0.1:8092
export PYTHONPATH=/opt/cyberpeer-pod/portals/phase2
exec /usr/bin/python3 /opt/cyberpeer-pod/portals/phase2/mcp_gateway.py
