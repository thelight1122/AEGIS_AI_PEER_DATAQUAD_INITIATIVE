"""Canonical tensor taxonomy an Orb reasons about.

Mirrors core.dataquad.tensors.TensorKind (I:\\AEGIS-CYBERPEER-CORE) value-for-value.
A Pod's concrete TensorKind will remain duck-compatible with this (same string
values) so record.tensor comparisons hold across the SDK boundary — the SDK does
not import the Pod's enum, it defines the shared vocabulary independently.
"""
from __future__ import annotations

try:
    from enum import StrEnum
except ImportError:  # Python < 3.11 fallback, matches the Pod-side shim
    from enum import Enum

    class StrEnum(str, Enum):  # noqa: N818
        pass


class TensorKind(StrEnum):
    PEER = "PEER"
    PCT = "PCT"
    NCT = "NCT"
    SPINE = "SPINE"
