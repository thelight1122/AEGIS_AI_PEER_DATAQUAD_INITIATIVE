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
from aegis_peer_runtime.daemon import DaemonClient
from .runtime import VerusLabRuntime, _now


DESKTOP_TRANSPORT = "claude_desktop_mcp_stdio_ssh"
_LOCAL_ID_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


_FRONTIER_TEXT_BUDGET = 1200
_FRONTIER_MAX_SURFACED_RECORDS = 12
_FRONTIER_LIVE_TURN_LIMIT = 6

# The fields the RLS orb scorer itself reads, in its order.
_SCORED_FIELDS = (
    "present_state", "working_context", "distilled_summary", "essence_memory", "pattern",
)


def _clip(value: object, budget: int = _FRONTIER_TEXT_BUDGET) -> str:
    text = value if isinstance(value, str) else str(value)
    if len(text) <= budget:
        return text
    return text[:budget] + f"... [clipped, {len(text)} chars]"


def _record_text(data: dict[str, object]) -> str:
    payload = data.get("payload")
    flat = {**data, **payload} if isinstance(payload, dict) else data
    parts = [str(flat[field]) for field in _SCORED_FIELDS if flat.get(field)]
    if not parts:
        for fallback in ("prompt_context", "response_context"):
            if flat.get(fallback):
                parts.append(str(flat[fallback]))
    return " ".join(parts)


def _project_dataquad_context(context: dict[str, object]) -> dict[str, object]:
    """Bounded view of the DataQuad context for the frontier.

    begin_turn returns on every turn. Returning the whole foundation and twenty
    full turn records puts roughly a third of a megabyte on the wire each time,
    past what the frontier will accept as a single tool result. Nothing is lost:
    verus_read_context still returns the context in full on request.
    """
    foundation = context.get("foundation")
    counts = (
        {tensor: len(records) for tensor, records in foundation.items()}
        if isinstance(foundation, dict) else {}
    )
    turns = context.get("recent_live_turns")
    turns = turns[-_FRONTIER_LIVE_TURN_LIMIT:] if isinstance(turns, list) else []
    recent = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        prompt = turn.get("prompt")
        response = turn.get("response")
        recent.append({
            "turn_id": turn.get("turn_id"),
            "t_time": turn.get("t_time"),
            "observed_at": turn.get("observed_at"),
            "record_hash": turn.get("record_hash"),
            "prompt": _clip(prompt.get("text", "") if isinstance(prompt, dict) else prompt),
            "response": _clip(response.get("text", "") if isinstance(response, dict) else response),
        })
    return {
        "cyberpeer_name": context.get("cyberpeer_name"),
        "dataquad_id": context.get("dataquad_id"),
        "append_contract": context.get("append_contract"),
        "contract_qualifications": context.get("contract_qualifications"),
        "foundation_record_counts": counts,
        "recent_live_turns": recent,
        "projection": {
            "bounded": True,
            "live_turns_shown": len(recent),
            "full_context_via": "verus_read_context",
        },
    }


_FOUNDATION_REF = re.compile(r"^foundation:([A-Z]+):(\d+)$")


def _foundation_body(record_id: str, context: object) -> dict[str, object]:
    """Resolve a foundation ref against the context already in hand.

    Selected refs are scored across every record; the custodian blocks only
    carry the most recent thirty. A selection the frontier cannot read is not a
    selection, so foundation bodies are resolved positionally from the context.
    """
    match = _FOUNDATION_REF.match(record_id)
    if not match or not isinstance(context, dict):
        return {}
    foundation = context.get("foundation")
    if not isinstance(foundation, dict):
        return {}
    records = foundation.get(match.group(1))
    index = int(match.group(2))
    if not isinstance(records, list) or index >= len(records):
        return {}
    record = records[index]
    return record if isinstance(record, dict) else {}


def _project_surfaced_context(surfaced: object, context: object = None) -> object:
    """Bounded view of the RLS retrieval for the frontier.

    The orb scores every record and preserves every rejection in the DataQuad —
    that is the evidence and it stays whole. What the frontier needs back is what
    the orb selected, not the raw custodian dumps and two hundred rejected refs.
    """
    if not isinstance(surfaced, dict):
        return surfaced
    result = surfaced.get("result")
    if not isinstance(result, dict):
        return surfaced

    bodies: dict[str, dict[str, object]] = {}
    for side in ("advocate", "steward"):
        block = result.get(side)
        if not isinstance(block, dict):
            continue
        for item in block.get("records", []) or []:
            if isinstance(item, dict) and isinstance(item.get("data"), dict):
                bodies[str(item.get("record_id"))] = item["data"]

    rls = result.get("rls") if isinstance(result.get("rls"), dict) else {}
    session = rls.get("session") if isinstance(rls.get("session"), dict) else {}
    selected = []
    for ref in (session.get("selected_refs") or [])[:_FRONTIER_MAX_SURFACED_RECORDS]:
        if not isinstance(ref, dict):
            continue
        record_id = str(ref.get("record_id"))
        data = bodies.get(record_id) or _foundation_body(record_id, context)
        selected.append({
            "record_id": record_id,
            "tensor": ref.get("tensor"),
            "relevance": ref.get("relevance"),
            "reason": ref.get("reason"),
            "turn_id": data.get("turn_id"),
            "t_time": data.get("t_time"),
            "text": _clip(_record_text(data)) if data else None,
            "body_resolved": bool(data),
        })

    relations = result.get("relations") if isinstance(result.get("relations"), dict) else {}
    temporal = result.get("temporal") if isinstance(result.get("temporal"), dict) else {}
    return {
        "assembled": result.get("assembled"),
        "rls_active": result.get("rls_active"),
        "turn_count": result.get("turn_count"),
        "prompt_keywords": result.get("prompt_keywords"),
        "rls": {
            "rls_id": rls.get("rls_id"),
            "executed": rls.get("executed"),
            "failure_is_data": rls.get("failure_is_data"),
            "failure_reason": session.get("failure_reason"),
            "selected_count": rls.get("selected_count"),
            "rejected_count": rls.get("rejected_count"),
            "created_pct_record_id": rls.get("created_pct_record_id"),
            "session_id": session.get("session_id"),
            "intent": session.get("intent"),
        },
        "selected": selected,
        "custodian_counts": {
            "advocate": (result.get("advocate") or {}).get("count"),
            "steward": (result.get("steward") or {}).get("count"),
            "temporal_observations": temporal.get("found"),
            "shared_turns": len(relations.get("shared_turns") or []),
        },
        "projection": {
            "bounded": True,
            "selected_shown": len(selected),
            "max_selected_shown": _FRONTIER_MAX_SURFACED_RECORDS,
            "text_budget": _FRONTIER_TEXT_BUDGET,
            "note": "full RLS session, raw custodian records, and every rejected ref are preserved in the DataQuad",
        },
    }


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
        surfaced_context = None
        try:
            _sock = str(self.dataquad.state_root / "daemons" / "processor.sock")
            _proc = DaemonClient(_sock)
            if _proc.available:
                surfaced_context = _proc.query("context", {
                    "prompt": prompt, "session_id": turn_id, "peer_id": "verus",
                    "intent": "context_retrieval", "limit": 30,
                })
        except Exception as _exc:
            surfaced_context = {"surfaced": False, "error": str(_exc)[:256]}
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
            "dataquad_context": _project_dataquad_context(context),
            "surfaced_context": _project_surfaced_context(surfaced_context, context),
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

    def query(
        self, *, prompt: str, limit: int = 30, intent: str = "context_retrieval",
    ) -> dict[str, object]:
        sock_path = str(self.dataquad.state_root / "daemons" / "processor.sock")
        client = DaemonClient(sock_path)
        if not client.available:
            raise ValueError("Processor daemon is not running — custodian query unavailable")
        result = client.query("context", {
            "prompt": prompt,
            "session_id": f"verus-query-{uuid.uuid4().hex[:12]}",
            "peer_id": "verus",
            "intent": intent,
            "limit": limit,
        })
        if "error" in result:
            raise ValueError(f"Processor daemon error: {result['error'][:256]}")
        return result.get("result", result)

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
            "historical_contract": {
                "pre_correction_operational_evidence": integrity["pre_correction_v1_turns"],
                "canonical_v2_turns": integrity["canonical_v2_turns"],
                "canonical_first_v2_turn_pending": integrity["canonical_v2_turns"] == 0,
                "preservation": "append_only_do_not_rewrite",
            },
            "integrity": integrity,
            "coherence": coherence,
        }
