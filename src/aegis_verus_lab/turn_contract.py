"""Provider-neutral, bounded Verus turn contracts shared by all substrates."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping, Protocol

from aegis_peer_runtime.models import TENSORS


MAX_APPEND_INTENTS = 64
MAX_APPEND_PAYLOAD_BYTES = 32_768
MAX_RESPONSE_TEXT_BYTES = 262_144
MAX_PROMPT_BYTES = 262_144
MAX_CONTEXT_BYTES = 4_194_304
MAX_TURN_RECORD_BYTES = 1_048_576


def _json_size(value: Any, *, label: str) -> int:
    try:
        encoded = json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be finite JSON-serializable data") from error
    return len(encoded)


@dataclass(frozen=True, slots=True)
class AppendIntent:
    tensor: str
    payload: Mapping[str, Any]

    def validate(self) -> None:
        if self.tensor not in TENSORS:
            raise ValueError(f"unknown DataQuad tensor: {self.tensor}")
        if not isinstance(self.payload, Mapping):
            raise ValueError("append payload must be an object")
        if _json_size(dict(self.payload), label="append payload") > MAX_APPEND_PAYLOAD_BYTES:
            raise ValueError(f"append payload exceeds {MAX_APPEND_PAYLOAD_BYTES} bytes")


@dataclass(frozen=True, slots=True)
class FrontierTurnRequest:
    cyberpeer_name: str
    dataquad_id: str
    turn_id: str
    source_event_id: str
    frontier_session_id: str
    system_instructions: str
    prompt: str
    context: Mapping[str, Any]

    def validate(self) -> None:
        for field in ("cyberpeer_name", "dataquad_id", "turn_id", "source_event_id",
                      "frontier_session_id", "system_instructions", "prompt"):
            if not getattr(self, field).strip():
                raise ValueError(f"frontier request {field} is required")
        if len(self.prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ValueError(f"prompt exceeds {MAX_PROMPT_BYTES} bytes")
        if not isinstance(self.context, Mapping):
            raise ValueError("frontier context must be an object")
        if _json_size(dict(self.context), label="frontier context") > MAX_CONTEXT_BYTES:
            raise ValueError(f"frontier context exceeds {MAX_CONTEXT_BYTES} bytes")


@dataclass(frozen=True, slots=True)
class FrontierTurnResponse:
    response_text: str
    append_intents: tuple[AppendIntent, ...]
    provider: str
    substrate: str
    model: str
    provider_request_id: str | None
    frontier_session_id: str
    provider_request_id_available: bool = True
    model_evidence: str = "provider_response"
    transport: str = "anthropic_messages_api"

    def validate(self) -> None:
        for field in (
            "response_text", "provider", "substrate", "model",
            "frontier_session_id", "model_evidence", "transport",
        ):
            if not getattr(self, field).strip():
                raise ValueError(f"frontier response {field} is required")
        if self.provider_request_id_available:
            if not isinstance(self.provider_request_id, str) or not self.provider_request_id.strip():
                raise ValueError("frontier response provider_request_id is required when available")
        elif self.provider_request_id is not None:
            raise ValueError("unavailable provider_request_id must be null")
        if len(self.response_text.encode("utf-8")) > MAX_RESPONSE_TEXT_BYTES:
            raise ValueError(f"frontier response exceeds {MAX_RESPONSE_TEXT_BYTES} bytes")
        for intent in self.append_intents:
            intent.validate()
        if len(self.append_intents) > MAX_APPEND_INTENTS:
            raise ValueError(f"a frontier turn may append at most {MAX_APPEND_INTENTS} DataQuad records")


class FrontierAdapter(Protocol):
    def complete(self, request: FrontierTurnRequest) -> FrontierTurnResponse: ...
