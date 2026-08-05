"""Resolves the RLS engine class to actually invoke for a given peer.

This is the umbilical-driven dynamic resolution Stage 3 exists for: when a Pod's
pod-manifest.json declares an `rls-persistent-relations-core` attachment, its
Umbilical's `invocation.entrypoint` (a dotted path — already present in every
real Umbilical written tonight, but never read by anything until this module)
is resolved via aegis_pod_sdk.resolve_entrypoint and used directly, instead of
a hardcoded top-level import.

Falls back to the same default entrypoint when no Pod/manifest/umbilical is
present (legacy-mode peers, and any test fixture with no Pod contracts at all) —
so this never regresses non-Pod callers, it only makes the Pod-attached path
genuinely dynamic.
"""
from __future__ import annotations

import json
from pathlib import Path

from aegis_pod_sdk import resolve_entrypoint

from core.dataquad import pod as _pod
from core.dataquad.ledgers import DataQuadStore

ORB_ID = "rls-persistent-relations-core"
DEFAULT_ENTRYPOINT = "orb_rls_persistent_relations_core.engine.RecursiveLearningEngine"


def resolve_rls_engine_class(store: DataQuadStore, peer_id: str) -> type:
    entrypoint = DEFAULT_ENTRYPOINT

    if _pod.is_pod_mode():
        peer_root = store.peer_root(peer_id)
        manifest_path = _pod.pod_manifest_path(peer_root)
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            orb_entry = next(
                (o for o in manifest.get("orbs", []) if o.get("orb_id") == ORB_ID), None
            )
            if orb_entry:
                umbilical_str = str(orb_entry.get("umbilical", ""))
                umbilical_path = (
                    Path(umbilical_str)
                    if umbilical_str and Path(umbilical_str).is_absolute()
                    else peer_root / umbilical_str
                )
                if umbilical_str and umbilical_path.exists():
                    umbilical = json.loads(umbilical_path.read_text(encoding="utf-8"))
                    entrypoint = umbilical.get("invocation", {}).get("entrypoint", DEFAULT_ENTRYPOINT)

    return resolve_entrypoint(entrypoint)
