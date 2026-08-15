"""Claude Desktop/MCP seam for the Verus DataQuad LAB."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from typing import Any, Callable, Mapping
import uuid

from .dataquad import VerusDataQuad
from .turn_contract import (
    AppendIntent,
    FrontierTurnRequest,
    FrontierTurnResponse,
    PROVIDER_RETURNED_OPTIONAL,
    local_correlation_provenance,
)
from .instructions import operational_system_instructions
from .runtime import VerusLabRuntime, _now


DESKTOP_TRANSPORT = "claude_desktop_mcp_stdio_ssh"
_LOCAL_ID_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class _DesktopOnlyAdapter:
    def complete(self, request):  # pragma: no cover - defensive boundary
        raise RuntimeError("Claude Desktop responses must arrive through the MCP commit tool")


def _correlation_id(
    *, turn_id: str, source_event_id: str | None,
    frontier_session_id: str | None, prompt: str,
) -> str:
    body = json.dumps({
        "cyberpeer_name": "Verus",
        "turn_id": turn_id,
        "source_event_id": source_event_id,
        "frontier_session_id": frontier_session_id,
        "prompt": prompt,
        "transport": DESKTOP_TRANSPORT,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return "verus-dataquad-correlation-" + hashlib.sha256(body).hexdigest()


def _optional_provider_id(value: str | None, *, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string or null")
    return value


def _new_local_token() -> str:
    return uuid.uuid4().hex


class DesktopVerusRuntime:
    """Two-phase Desktop turn boundary with DataQuad-first durable commit."""

    def __init__(
        self,
        dataquad: VerusDataQuad,
        *,
        model: str,
        clock: Callable[[], datetime] = _now,
        local_id_factory: Callable[[], str] = _new_local_token,
    ) -> None:
        if not model.strip():
            raise ValueError("exact Claude Desktop model provenance is required")
        self.dataquad = dataquad
        self.model = model
        self._local_id_factory = local_id_factory
        self._core = VerusLabRuntime(dataquad, _DesktopOnlyAdapter(), clock=clock)
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
        turn_id = f"verus-local-turn-{local_token}"
        context = self.dataquad.context()
        instructions = operational_system_instructions("Verus")
        request = FrontierTurnRequest(
            cyberpeer_name="Verus", dataquad_id="verus", turn_id=turn_id,
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
            "cyberpeer_name": "Verus",
            "identity_variables": {"cyberpeer_name": "Verus"},
            "dataquad_id": "verus",
            "turn_id": turn_id,
            "correlation_id": correlation_id,
            "local_correlation": local_correlation_provenance(turn_id, correlation_id),
            "system_instructions": instructions,
            "work_request": prompt,
            "dataquad_context": context,
            "append_contract": {"mode": "append-only", "tensors": ["PEER", "PCT", "NCT", "SPINE"]},
            "frontier_provenance": {
                "provider": "Anthropic", "substrate": "Claude Desktop",
                "model": self.model, "model_evidence": "steward_confirmed_ui_selection",
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
            provider="Anthropic",
            substrate="Claude Desktop",
            model=self.model,
            provider_request_id=None,
            provider_request_id_available=False,
            model_evidence="steward_confirmed_ui_selection",
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
                or provenance.get("provider") != "Anthropic"
                or provenance.get("substrate") != "Claude Desktop"
                or provenance.get("model") != self.model
                or provenance.get("provider_request_id") is not None
                or provenance.get("provider_request_id_available") is not False
                or provenance.get("transport") != DESKTOP_TRANSPORT
            ):
                raise ValueError("turn_id already names different Desktop response content")
        result = self._core.commit_response(
            turn_id=turn_id, source_event_id=source_event_id,
            frontier_session_id=frontier_session_id, prompt=prompt,
            response=response, allowed_substrates=("Claude Desktop",),
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
            "mode": "LAB_RUNNING", "cyberpeer_name": "Verus", "dataquad_id": "verus",
            "turn_id": turn_id, "record_hash": entry["record_hash"],
            "response_text": entry["response"]["text"], "created": False,
            "frontier_provenance": entry["frontier_provenance"],
        }

    def coherence(self) -> dict[str, object]:
        return self._core.coherence()

    def health(self) -> dict[str, object]:
        integrity = self.dataquad.verify()
        coherence = self.coherence()
        return {
            "status": "ok" if coherence["coherent"] else "degraded",
            "ready": coherence["coherent"],
            "mode": "LAB_RUNNING",
            "cyberpeer_name": "Verus",
            "dataquad_id": "verus",
            "full_append_only": True,
            "writable_tensors": ["PEER", "PCT", "NCT", "SPINE"],
            "transport": DESKTOP_TRANSPORT,
            "public_listener": False,
            "preferred_loopback_port": 8791,
            "frontier_provenance": {
                "provider": "Anthropic", "substrate": "Claude Desktop", "model": self.model,
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
            "integrity": integrity,
            "coherence": coherence,
        }
