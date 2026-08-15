"""Claude Desktop/MCP seam for the Verus DataQuad LAB."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from typing import Any, Callable, Mapping

from .dataquad import VerusDataQuad
from .turn_contract import AppendIntent, FrontierTurnRequest, FrontierTurnResponse
from .instructions import operational_system_instructions
from .runtime import VerusLabRuntime, _now


DESKTOP_TRANSPORT = "claude_desktop_mcp_stdio_ssh"


class _DesktopOnlyAdapter:
    def complete(self, request):  # pragma: no cover - defensive boundary
        raise RuntimeError("Claude Desktop responses must arrive through the MCP commit tool")


def _correlation_id(
    *, turn_id: str, source_event_id: str, frontier_session_id: str, prompt: str,
) -> str:
    body = json.dumps({
        "cyberpeer_name": "Verus",
        "turn_id": turn_id,
        "source_event_id": source_event_id,
        "frontier_session_id": frontier_session_id,
        "prompt": prompt,
        "transport": DESKTOP_TRANSPORT,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return "verus-" + hashlib.sha256(body).hexdigest()


class DesktopVerusRuntime:
    """Two-phase Desktop turn boundary with DataQuad-first durable commit."""

    def __init__(
        self,
        dataquad: VerusDataQuad,
        *,
        model: str,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        if not model.strip():
            raise ValueError("exact Claude Desktop model provenance is required")
        self.dataquad = dataquad
        self.model = model
        self._core = VerusLabRuntime(dataquad, _DesktopOnlyAdapter(), clock=clock)
        self.temporal = self._core.temporal
        self.processor = self._core.processor
        self.rls = self._core.rls

    def begin_turn(
        self, *, turn_id: str, source_event_id: str, frontier_session_id: str, prompt: str,
    ) -> dict[str, object]:
        context = self.dataquad.context()
        instructions = operational_system_instructions("Verus")
        request = FrontierTurnRequest(
            cyberpeer_name="Verus", dataquad_id="verus", turn_id=turn_id,
            source_event_id=source_event_id, frontier_session_id=frontier_session_id,
            system_instructions=instructions, prompt=prompt, context=context,
        )
        request.validate()
        return {
            "mode": "LAB_RUNNING",
            "cyberpeer_name": "Verus",
            "identity_variables": {"cyberpeer_name": "Verus"},
            "dataquad_id": "verus",
            "correlation_id": _correlation_id(
                turn_id=turn_id, source_event_id=source_event_id,
                frontier_session_id=frontier_session_id, prompt=prompt,
            ),
            "system_instructions": instructions,
            "work_request": prompt,
            "dataquad_context": context,
            "append_contract": {"mode": "append-only", "tensors": ["PEER", "PCT", "NCT", "SPINE"]},
            "frontier_provenance": {
                "provider": "Anthropic", "substrate": "Claude Desktop",
                "model": self.model, "model_evidence": "steward_confirmed_ui_selection",
                "transport": DESKTOP_TRANSPORT, "defines_identity": False,
                "provider_request_id_available": False,
            },
        }

    def commit_turn(
        self,
        *,
        correlation_id: str,
        turn_id: str,
        source_event_id: str,
        frontier_session_id: str,
        prompt: str,
        response_text: str,
        appends: list[Mapping[str, Any]],
    ) -> dict[str, object]:
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
            },
            "integrity": integrity,
            "coherence": coherence,
        }
