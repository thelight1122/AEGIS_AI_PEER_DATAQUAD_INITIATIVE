#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo "run as root" >&2; exit 2; fi
systemctl stop aegis-verus-lab.service
echo "Verus LAB paused. DataQuad and append-only evidence were preserved."
