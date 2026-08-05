"""Generic helpers with zero Pod-specific coupling — safe to own canonically in the
SDK rather than duplicate. Mirror core.dataquad.pod.stable_json/sha256_upper exactly
(same sort_keys/separators/hexdigest-upper convention) so hashes computed on either
side of the SDK boundary remain comparable."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_upper(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()
