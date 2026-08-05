from __future__ import annotations

import hashlib
from pathlib import Path

ORB_ID = "memorysearch-record-grounding-core"
_SOURCE_FILES = ("policy.py", "provenance.py", "search.py")


def sha256_upper(value: str | bytes) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest().upper()


def compute_runtime_hash() -> str:
    package_root = Path(__file__).resolve().parent
    source = "".join((package_root / name).read_text(encoding="utf-8") for name in _SOURCE_FILES)
    return sha256_upper(source)
