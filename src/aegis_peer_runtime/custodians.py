"""Disjoint authoritative tensor write scopes for AI Peer custodians."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


TENSORS = frozenset({"PEER", "PCT", "NCT", "SPINE"})


class ScopeViolation(PermissionError):
    pass


@dataclass(frozen=True)
class Custodian:
    name: str
    writable: frozenset[str]

    def authorize(self, changes: Mapping[str, object]) -> dict[str, object]:
        unknown = set(changes) - TENSORS
        forbidden = set(changes) - self.writable
        if unknown:
            raise ScopeViolation(f"unknown tensors: {sorted(unknown)}")
        if forbidden:
            raise ScopeViolation(f"{self.name} cannot write: {sorted(forbidden)}")
        return dict(changes)


STEWARD = Custodian("Steward", frozenset({"PCT", "NCT"}))
ADVOCATE = Custodian("Advocate", frozenset({"PEER", "SPINE"}))
