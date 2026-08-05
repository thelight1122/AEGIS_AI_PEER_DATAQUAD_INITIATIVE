"""Bounded capability execution layer for the Phase 2 Pod sidecar.

The router authenticates and authorizes first, then invokes only the already
proven copy-backed observation/replay adapters. It has no mutation handlers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4
import importlib

try:
    from .copy_read_adapter import observe
    from .portal_contract import PortalDecision, authorize
    from .rls_replay_adapter import replay
    from .execution_ledger import append_record, build_record, sha256_file, sha256_value
except ImportError:  # Standalone staged files under the sidecar portal directory.
    from copy_read_adapter import observe
    from portal_contract import PortalDecision, authorize
    from rls_replay_adapter import replay
    from execution_ledger import append_record, build_record, sha256_file, sha256_value


class CapabilityRouter:
    def __init__(
        self,
        manifest: dict[str, Any],
        *,
        context_root: Path,
        context_hashes: Path,
        rls_source: Path,
        rls_hashes: Path,
        approved_root: Path,
        require_immutable: bool = True,
        evidence_ledger: Path | None = None,
    ) -> None:
        self.manifest = manifest
        self.context_root = context_root
        self.context_hashes = context_hashes
        self.rls_source = rls_source
        self.rls_hashes = rls_hashes
        self.approved_root = approved_root
        self.require_immutable = require_immutable
        self.evidence_ledger = evidence_ledger

    def _module_hash(self, module_name: str) -> str:
        module = importlib.import_module(module_name)
        return sha256_file(Path(module.__file__).resolve())

    def _denied(self, decision: PortalDecision) -> dict[str, Any]:
        return {
            "authorized": False,
            "method": decision.method,
            "reason": decision.reason,
            "action_executed": False,
            "mutation_performed": False,
        }

    def execute(
        self,
        *,
        method: str,
        bearer_token: str | None,
        query: str = "",
        limit: int = 20,
        reflection_mode: str | None = None,
        continuity_scope: str | None = None,
        request_id: str | None = None,
        caller: str = "portal_client",
    ) -> dict[str, Any]:
        request_id = request_id or str(uuid4())
        decision = authorize(
            self.manifest,
            method=method,
            bearer_token=bearer_token,
            limit=limit,
            reflection_mode=reflection_mode,
            continuity_scope=continuity_scope,
        )
        if not decision.allowed:
            result = self._denied(decision)
            result["request_id"] = request_id
            return result
        if method == "query_continuity" and continuity_scope != "observed":
            result = self._denied(PortalDecision(False, method, "admitted scope is not available to this router"))
            result["request_id"] = request_id
            return result

        if method == "retrieve_context":
            result = observe(self.context_root, self.context_hashes, query, limit, approved_root=self.approved_root, require_immutable=self.require_immutable)
        elif method == "retrieve_canon":
            result = observe(self.context_root, self.context_hashes, query, limit, approved_root=self.approved_root, require_immutable=self.require_immutable, tensors=("SPINE",))
        elif method == "query_continuity":
            result = observe(self.context_root, self.context_hashes, query, limit, approved_root=self.approved_root, require_immutable=self.require_immutable)
        elif method == "request_reflection":
            result = replay(self.rls_source, self.rls_hashes, self.approved_root, query, limit)
        else:
            return self._denied(PortalDecision(False, method, "no executable handler"))

        adapter_module = observe.__module__ if method != "request_reflection" else replay.__module__
        result_value = {
            "authorized": True,
            "request_id": request_id,
            "method": method,
            "action_executed": True,
            "mutation_performed": False,
            "experience_created": False,
            "result": result,
            "evidence": {
                "authorization": "passed",
                "caller": caller,
                "execution": "read_only_or_replay_only",
                "source_write": False,
                "pod_write": False,
                "dataquad_writeback": False,
                "frontier_connection": False,
                "router_sha256": self._module_hash(__name__),
                "adapter": adapter_module,
                "adapter_sha256": self._module_hash(adapter_module),
            },
        }
        result_value["evidence"]["result_sha256"] = sha256_value(result_value["result"])
        if method == "request_reflection":
            result_value["evidence"]["source_sha256"] = result["source"]["source_sha256"]
        else:
            result_value["evidence"]["source_sha256"] = result["source"]["tensor_hashes"]
        if self.evidence_ledger is not None:
            append_record(self.evidence_ledger, build_record(
                request_id=request_id,
                caller=caller,
                method=method,
                authorization="passed",
                adapter=adapter_module,
                router_sha256=result_value["evidence"]["router_sha256"],
                adapter_sha256=result_value["evidence"]["adapter_sha256"],
                source_sha256=result_value["evidence"]["source_sha256"],
                result_sha256=result_value["evidence"]["result_sha256"],
                mutation=False,
                admission=False,
                experience_created=False,
            ))
        return result_value
