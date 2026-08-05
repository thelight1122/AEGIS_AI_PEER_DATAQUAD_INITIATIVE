from __future__ import annotations

from hashlib import sha256
from pathlib import Path

ORB_ID = "identity-field-builder-core"
_SOURCE_FILES = ("builder.py", "spine_mapping.py", "shadow_observation.py", "phase2_shadow.py")


def sha256_upper(value: str | bytes) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return sha256(data).hexdigest().upper()


def compute_runtime_hash() -> str:
    package_root = Path(__file__).resolve().parent
    source = "".join((package_root / name).read_text(encoding="utf-8") for name in _SOURCE_FILES)
    return sha256_upper(source)
