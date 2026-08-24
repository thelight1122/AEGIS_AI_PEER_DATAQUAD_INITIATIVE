"""Codex/GPT/MCP seam for the Lumin DataQuad LAB."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from typing import Any, Callable, Mapping
import uuid

from .activation_dataquad import LuminDataQuad
from .turn_contract import (
    AppendIntent,
    FrontierTurnRequest,
    FrontierTurnResponse,
    PROVIDER_RETURNED_OPTIONAL,
    local_correlation_provenance,
)
from .instructions import operational_system_instructions
from aegis_peer_runtime.daemon import DaemonClient
from .runtime import LuminLabRuntime, _now


DESKTOP_TRANSPORT = "codex_mcp_stdio_ssh"
_LOCAL_ID_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class _DesktopOnlyAdapter:
    def complete(self, request):  # pragma: no cover - defensive boundary
        raise RuntimeError("Codex/GPT responses must arrive through the MCP commit tool")


def _correlation_id(
    *, turn_id: str, source_event_id: str | None,
    frontier_session_id: str | None, prompt: str,
) -> str:
    body = json.dumps({
        "cyberpeer_name": "Lumin",
        "turn_id": turn_id,
        "source_event_id": source_event_id,
        "frontier_session_id": frontier_session_id,
        "prompt": prompt,
        "transport": DESKTOP_TRANSPORT,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return "lumin-dataquad-correlation-" + hashlib.sha256(body).hexdigest()


def _optional_provider_id(value: str | None, *, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string or null")
    return value


def _new_local_token() -> str:
    return uuid.uuid4().hex


class DesktopLuminRuntime:
    """Two-phase Desktop turn boundary with DataQuad-first durable commit."""

    def __init__(
        self,
        dataquad: LuminDataQuad,
        *,
        model: str | None,
        clock: Callable[[], datetime] = _now,
        local_id_factory: Callable[[], str] = _new_local_token,
    ) -> None:
        if model is not None:
            raise ValueError("exact model must remain null when Codex MCP does not expose it")
        self.dataquad = dataquad
        self.model = model
        self._local_id_factory = local_id_factory
        self._core = LuminLabRuntime(dataquad, _DesktopOnlyAdapter(), clock=clock)
        self.temporal = self._core.temporal
        self.processor = self._core.processor
        self.rls = self._core.rls

    def begin_turn(
        self, *, prompt: str, source_event_id: str | None = None,
        frontier_session_id: str | None = None,
    ) -> dict[str, object]:
        source_event_id = _optional_provider_id(source_event_id, label="source_event_id")
        frontier_session_id = _optional_provider_id(
            frontier_session_id, label="frontier_session_id",
        )
        local_token = self._local_id_factory()
        if not isinstance(local_token, str) or _LOCAL_ID_TOKEN.fullmatch(local_token) is None:
            raise ValueError("DataQuad local identifier factory returned an invalid value")
        turn_id = f"lumin-local-turn-{local_token}"
        context = self.dataquad.context()
        surfaced_context = None
        try:
            _sock = str(self.dataquad.state_root / "daemons" / "processor.sock")
            _proc = DaemonClient(_sock)
            if _proc.available:
                surfaced_context = _proc.query("context", {
                    "prompt": prompt, "session_id": turn_id, "peer_id": "lumin",
                    "intent": "context_retrieval", "limit": 30,
                })
        except Exception as _exc:
            surfaced_context = {"surfaced": False, "error": str(_exc)[:256]}
        instructions = operational_system_instructions("Lumin")
        request = FrontierTurnRequest(
            cyberpeer_name="Lumin", dataquad_id="lumin", turn_id=turn_id,
            source_event_id=source_event_id, frontier_session_id=frontier_session_id,
            system_instructions=instructions, prompt=prompt, context=context,
            source_event_id_available=source_event_id is not None,
            frontier_session_id_available=frontier_session_id is not None,
        )
        request.validate()
        correlation_id = _correlation_id(
            turn_id=turn_id, source_event_id=source_event_id,
            frontier_session_id=frontier_session_id, prompt=prompt,
        )
        return {
            "mode": "LAB_RUNNING",
            "cyberpeer_name": "Lumin",
            "identity_variables": {"cyberpeer_name": "Lumin"},
            "dataquad_id": "lumin",
            "turn_id": turn_id,
            "correlation_id": correlation_id,
            "local_correlation": local_correlation_provenance(turn_id, correlation_id),
            "system_instructions": instructions,
            "work_request": prompt,
            "dataquad_context": context,
            "surfaced_context": surfaced_context,
            "append_contract": {"mode": "append-only", "tensors": ["PEER", "PCT", "NCT", "SPINE"]},
            "frontier_provenance": {
                "provider": "OpenAI", "substrate": "Codex/GPT",
                "model": None, "model_available": False,
                "model_evidence": "unavailable:not_exposed_by_codex_mcp_boundary",
                "transport": DESKTOP_TRANSPORT, "defines_identity": False,
                "provider_request_id_available": False,
                "source_event_id": source_event_id,
                "source_event_id_available": source_event_id is not None,
                "source_event_id_classification": PROVIDER_RETURNED_OPTIONAL,
                "frontier_session_id": frontier_session_id,
                "frontier_session_id_available": frontier_session_id is not None,
                "frontier_session_id_classification": PROVIDER_RETURNED_OPTIONAL,
            },
        }

    def commit_turn(
        self,
        *,
        correlation_id: str,
        turn_id: str,
        prompt: str,
        response_text: str,
        appends: list[Mapping[str, Any]],
        source_event_id: str | None = None,
        frontier_session_id: str | None = None,
    ) -> dict[str, object]:
        source_event_id = _optional_provider_id(source_event_id, label="source_event_id")
        frontier_session_id = _optional_provider_id(
            frontier_session_id, label="frontier_session_id",
        )
        expected = _correlation_id(
            turn_id=turn_id, source_event_id=source_event_id,
            frontier_session_id=frontier_session_id, prompt=prompt,
        )
        if correlation_id != expected:
            raise ValueError("Desktop turn correlation does not match the begun request")
        if not isinstance(appends, list):
            raise ValueError("appends must be a JSON array")
        intents: list[AppendIntent] = []
        for item in appends:
            if not isinstance(item, Mapping):
                raise ValueError("each append must be a JSON object")
            intent = AppendIntent(str(item.get("tensor", "")), item.get("payload", {}))
            intent.validate()
            intents.append(intent)
        response = FrontierTurnResponse(
            response_text=response_text,
            append_intents=tuple(intents),
            provider="OpenAI",
            substrate="Codex/GPT",
            model=None,
            provider_request_id=None,
            provider_request_id_available=False,
            model_available=False,
            model_evidence="unavailable:not_exposed_by_codex_mcp_boundary",
            transport=DESKTOP_TRANSPORT,
            frontier_session_id=frontier_session_id,
            frontier_session_id_available=frontier_session_id is not None,
        )
        response.validate()
        existing = self.dataquad.find_turn(turn_id)
        if existing is not None:
            expected_appends = [
                {"tensor": intent.tensor, "payload": dict(intent.payload)} for intent in intents
            ]
            observed_appends = [
                {"tensor": item["tensor"], "payload": dict(item["payload"])}
                for item in existing["appends"]
            ]
            provenance = existing["frontier_provenance"]
            if (
                existing["response"]["text"] != response_text
                or observed_appends != expected_appends
                or provenance.get("provider") != "OpenAI"
                or provenance.get("substrate") != "Codex/GPT"
                or provenance.get("model") is not None
                or provenance.get("model_available") is not False
                or provenance.get("provider_request_id") is not None
                or provenance.get("provider_request_id_available") is not False
                or provenance.get("transport") != DESKTOP_TRANSPORT
            ):
                raise ValueError("turn_id already names different Desktop response content")
        result = self._core.commit_response(
            turn_id=turn_id, source_event_id=source_event_id,
            frontier_session_id=frontier_session_id, prompt=prompt,
            response=response, allowed_substrates=("Codex/GPT",),
            source_event_id_available=source_event_id is not None,
            dataquad_correlation_id=correlation_id,
        )
        return {**result, "correlation_id": correlation_id, "transport": DESKTOP_TRANSPORT}

    def reconcile_committed_turns(self) -> dict[str, object]:
        self._core.reconcile_committed_turns()
        return self.health()

    def replay_turn(self, *, turn_id: str) -> dict[str, object]:
        entry = self.dataquad.find_turn(turn_id)
        if entry is None:
            raise ValueError("turn_id is not committed")
        self._core._materialize_derived(entry)
        return {
            "mode": "LAB_RUNNING", "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
            "turn_id": turn_id, "record_hash": entry["record_hash"],
            "response_text": entry["response"]["text"], "created": False,
            "frontier_provenance": entry["frontier_provenance"],
        }

    def query(
        self, *, prompt: str, limit: int = 30, intent: str = "context_retrieval",
    ) -> dict[str, object]:
        sock_path = str(self.dataquad.state_root / "daemons" / "processor.sock")
        client = DaemonClient(sock_path)
        if not client.available:
            raise ValueError("Processor daemon is not running — custodian query unavailable")
        result = client.query("context", {
            "prompt": prompt,
            "session_id": f"lumin-query-{uuid.uuid4().hex[:12]}",
            "peer_id": "lumin",
            "intent": intent,
            "limit": limit,
        })
        if "error" in result:
            raise ValueError(f"Processor daemon error: {result['error'][:256]}")
        return result.get("result", result)

    def query_and_record(
        self, *, prompt: str, response_text: str, limit: int = 30,
        intent: str = "context_retrieval", source_event_id: str | None = None,
        frontier_session_id: str | None = None,
    ) -> dict[str, object]:
        """Retrieve through the custodian pipeline, then append the completed turn.

        MCP cannot observe the host assistant's response after it returns a tool
        result.  The response is therefore an explicit second-phase argument;
        this helper makes the query/commit sequence atomic from the caller's
        perspective while retaining the existing append-only turn contract.
        """
        context = self.query(prompt=prompt, limit=limit, intent=intent)
        begun = self.begin_turn(
            prompt=prompt, source_event_id=source_event_id,
            frontier_session_id=frontier_session_id,
        )
        context_hash = hashlib.sha256(
            json.dumps(context, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False).encode("utf-8")
        ).hexdigest().upper()
        appends = [
            {"tensor": "PEER", "payload": {
                "kind": "interaction_user_context", "prompt": prompt,
                "query_context_sha256": context_hash,
            }},
            {"tensor": "PCT", "payload": {
                "kind": "interaction_response_context", "response": response_text,
                "query_context_sha256": context_hash,
            }},
            {"tensor": "NCT", "payload": {
                "kind": "query_context", "query_context_sha256": context_hash,
            }},
            {"tensor": "SPINE", "payload": {
                "kind": "interaction_provenance", "query_intent": intent,
                "query_context_sha256": context_hash,
            }},
        ]
        committed = self.commit_turn(
            correlation_id=str(begun["correlation_id"]),
            turn_id=str(begun["turn_id"]), prompt=prompt,
            response_text=response_text, appends=appends,
            source_event_id=source_event_id,
            frontier_session_id=frontier_session_id,
        )
        return {**committed, "query_context": context,
                "query_context_sha256": context_hash,
                "recording": "append_only_user_and_assistant_context"}

    def coherence(self) -> dict[str, object]:
        return self._core.coherence()

    def health(self) -> dict[str, object]:
        integrity = self.dataquad.verify()
        coherence = self.coherence()
        return {
            "status": "ok" if coherence["coherent"] else "degraded",
            "ready": coherence["coherent"],
            "mode": "LAB_RUNNING",
            "cyberpeer_name": "Lumin",
            "dataquad_id": "lumin",
            "full_append_only": True,
            "rls_active": True,
            "writable_tensors": ["PEER", "PCT", "NCT", "SPINE"],
            "transport": DESKTOP_TRANSPORT,
            "public_listener": False,
            "frontier_provenance": {
                "provider": "OpenAI", "substrate": "Codex/GPT", "model": None,
                "model_available": False,
                "model_evidence": "unavailable:not_exposed_by_codex_mcp_boundary",
                "provider_request_id_available": False, "defines_identity": False,
                "source_event_id": None, "source_event_id_available": False,
                "source_event_id_classification": PROVIDER_RETURNED_OPTIONAL,
                "frontier_session_id": None, "frontier_session_id_available": False,
                "frontier_session_id_classification": PROVIDER_RETURNED_OPTIONAL,
            },
            "local_correlation_policy": {
                "classification": "dataquad_owned_local_correlation",
                "provider_identifier": False,
                "defines_identity": False,
            },
            "historical_contract": {
                "pre_correction_operational_evidence": integrity["pre_correction_turns"],
                "canonical_v2_turns": integrity["canonical_v2_turns"],
                "canonical_first_v2_turn_pending": integrity["canonical_v2_turns"] == 0,
                "preservation": "append_only_do_not_rewrite",
            },
            "integrity": integrity,
            "coherence": coherence,
        }

