"""Task Scheduler boot entry for the Verus DataQuad daemon supervisor.

Run headless by pythonw.exe (no console). Puts the Verus src on sys.path, then
enters the supervisor's resident supervise loop (starts the four daemons if not
already up, restarts any that stop). Paths beyond src come from the peer config.
"""
import os
import sys

SRC = r"H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\src"
if SRC not in sys.path:
    sys.path.insert(0, SRC)
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("AEGIS_PEER_ID", "verus")
os.environ.setdefault("AEGIS_FRONTIER_MODEL", "claude-opus-4-8")

# RLS (P1). The canonical orb (shortfall_* + failure_*) goes ahead of the global
# editable install, which resolves to a stale failure-only copy under
# H:\AEGIS-POD-ARCHITECTURE. PYTHONPATH precedes .pth entries, so the daemons
# the supervisor launches import the canonical orb. Scoped to Verus only.
ORB = r"H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\packages\orb-rls-persistent-relations-core\src"
if ORB not in sys.path:
    sys.path.insert(0, ORB)
# The orb imports aegis_pod_sdk. Its global editable install points at
# H:\AEGIS-POD-ARCHITECTURE, which moved to G:, so use the in-repo copy instead.
SDK = r"H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\packages\aegis-pod-sdk\src"
if SDK not in sys.path:
    sys.path.insert(0, SDK)
os.environ["PYTHONPATH"] = os.pathsep.join([ORB, SDK, os.environ.get("PYTHONPATH", "")])
os.environ.setdefault("AEGIS_RLS_ACTIVE", "true")

from aegis_verus_lab.daemon_supervisor import main

raise SystemExit(main(["supervise"]))
