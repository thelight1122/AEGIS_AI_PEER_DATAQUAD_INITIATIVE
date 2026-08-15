"""Provider-neutral frontier turn contract and an Anthropic Messages adapter."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
import urllib.request
import urllib.error

from aegis_peer_runtime.models import TENSORS
from .turn_contract import (
    MAX_APPEND_INTENTS, MAX_APPEND_PAYLOAD_BYTES, MAX_CONTEXT_BYTES,
    MAX_PROMPT_BYTES, MAX_RESPONSE_TEXT_BYTES, MAX_TURN_RECORD_BYTES,
    AppendIntent, FrontierAdapter, FrontierTurnRequest, FrontierTurnResponse,
)


class FrontierError(RuntimeError):
    """A bounded Frontier boundary failure safe for HTTP classification."""


class FrontierAuthenticationError(FrontierError):
    pass


class FrontierRateLimitError(FrontierError):
    pass


class FrontierUnavailableError(FrontierError):
    pass


class FrontierProtocolError(FrontierError):
    pass


class SecretLoader(Protocol):
    def load(self) -> str: ...


@dataclass(frozen=True, slots=True)
class FileSecretLoader:
    path: Path

    def load(self) -> str:
        path = Path(self.path)
        if path.is_symlink() or not path.is_file():
            raise FrontierAuthenticationError("Frontier credential is unavailable")
        value = path.read_text(encoding="utf-8").strip()
        if not value:
            raise FrontierAuthenticationError("Frontier credential is unavailable")
        return value


class AnthropicMessagesAdapter:
    """Translate the neutral contract to Anthropic Messages at the last boundary."""

    API_VERSION = "2023-06-01"
    ENDPOINT = "https://api.anthropic.com/v1/messages"

    def __init__(
        self,
        *,
        model: str,
        secret_loader: SecretLoader,
        max_tokens: int = 4096,
        transport: Callable[[urllib.request.Request], Mapping[str, Any]] | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("the exact runtime Anthropic model identifier is required")
        self.model = model
        self.secret_loader = secret_loader
        self.max_tokens = max_tokens
        self.transport = transport or self._urlopen

    @staticmethod
    def _urlopen(request: urllib.request.Request) -> Mapping[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                value = json.load(response)
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise FrontierAuthenticationError("Frontier authentication rejected") from error
            if error.code == 429:
                raise FrontierRateLimitError("Frontier rate limited the request") from error
            if error.code >= 500:
                raise FrontierUnavailableError("Frontier service is unavailable") from error
            raise FrontierProtocolError("Frontier rejected the request") from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise FrontierUnavailableError("Frontier network is unavailable") from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise FrontierProtocolError("Frontier returned invalid JSON") from error
        if not isinstance(value, dict):
            raise FrontierProtocolError("Frontier response must be an object")
        return value

    def complete(self, request: FrontierTurnRequest) -> FrontierTurnResponse:
        request.validate()
        credential = self.secret_loader.load()
        tool = {
            "name": "complete_verus_turn",
            "description": "Return the response and zero or more append-only DataQuad records.",
            "input_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["response_text", "dataquad_appends"],
                "properties": {
                    "response_text": {"type": "string", "minLength": 1},
                    "dataquad_appends": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["tensor", "payload"],
                            "properties": {
                                "tensor": {"type": "string", "enum": list(TENSORS)},
                                "payload": {"type": "object"},
                            },
                        },
                    },
                },
            },
        }
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": request.system_instructions,
            "messages": [{
                "role": "user",
                "content": json.dumps({
                    "turn_id": request.turn_id,
                    "source_event_id": request.source_event_id,
                    "frontier_session_id": request.frontier_session_id,
                    "dataquad_context": request.context,
                    "work_request": request.prompt,
                }, sort_keys=True, separators=(",", ":")),
            }],
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": "complete_verus_turn"},
        }
        wire = urllib.request.Request(
            self.ENDPOINT,
            data=json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": credential,
                "anthropic-version": self.API_VERSION,
            },
            method="POST",
        )
        try:
            raw = self.transport(wire)
        except FrontierError:
            raise
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise FrontierAuthenticationError("Frontier authentication rejected") from error
            if error.code == 429:
                raise FrontierRateLimitError("Frontier rate limited the request") from error
            if error.code >= 500:
                raise FrontierUnavailableError("Frontier service is unavailable") from error
            raise FrontierProtocolError("Frontier rejected the request") from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise FrontierUnavailableError("Frontier network is unavailable") from error
        try:
            if not isinstance(raw, Mapping):
                raise ValueError("response is not an object")
            blocks = raw.get("content")
            if not isinstance(blocks, list):
                raise ValueError("response content is not a list")
            chosen = next((item for item in blocks if isinstance(item, dict)
                           and item.get("type") == "tool_use"
                           and item.get("name") == "complete_verus_turn"), None)
            if chosen is None or not isinstance(chosen.get("input"), dict):
                raise ValueError("required tool input is absent")
            value = chosen["input"]
            appends = value.get("dataquad_appends")
            if not isinstance(appends, list) or any(not isinstance(item, dict) for item in appends):
                raise ValueError("dataquad_appends is invalid")
            result = FrontierTurnResponse(
                response_text=value.get("response_text", ""),
                append_intents=tuple(AppendIntent(item.get("tensor", ""), item.get("payload", {}))
                                     for item in appends),
                provider="Anthropic",
                substrate="Claude",
                model=str(raw.get("model") or self.model),
                provider_request_id=str(raw.get("id") or ""),
                frontier_session_id=request.frontier_session_id,
            )
            result.validate()
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise FrontierProtocolError("Frontier response violated the structured turn contract") from error
