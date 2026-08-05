"""
orb_archive_relevance_core.engine — ArchiveRelevanceEngine

Solves a concrete, evidenced shortfall: when a peer's invariant SPINE record
count exceeds the context cap (advocate.py's AEGIS_SPINE_INVARIANT_CAP), a
flat file-order slice can silently exclude a record the current query is
explicitly asking about by name (e.g. "What is Axiom 11?"), with no signal
that it happened. Root-caused live on CP-1003-GABE, 2026-07-22: the real
Axiom 11 record existed, correctly flagged invariant, but sat past the cap
in file order; the model fabricated a plausible-sounding false answer rather
than reporting uncertainty.

Scope, deliberately narrow: this engine does not replace advocate.py's
relevance scoring for non-invariant SPINE, does not touch STM, does not touch
RLS's relation recording. It answers one question: given more invariant
records than the cap allows, which ones make the cut — and does an explicitly
named anchor referenced in the query win a guaranteed seat regardless of its
position in the file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Matches an explicit numbered/named anchor reference in a query, e.g.
# "Axiom 11", "axiom:11", "Axiom #11", "GATE: pipeline-order", "Imperative do-no-harm".
_NUMBERED_ANCHOR = re.compile(r"\baxiom\s*[:#]?\s*(\d+)\b", re.IGNORECASE)
_NAMED_ANCHOR = re.compile(r"\b(gate|imperative)\s*[:\s]+([a-z][a-z0-9\-]*)\b", re.IGNORECASE)


@dataclass
class InvariantRecord:
    """Minimal shape the engine needs — deliberately not the Pod's own
    SPINERecord, so this package stays dependency-free of core app models."""
    id: str
    label: str
    pattern: str = ""


@dataclass
class SelectionResult:
    selected_ids: list[str] = field(default_factory=list)
    excluded_ids: list[str] = field(default_factory=list)
    label_match_hit: str | None = None
    cap_overflow: bool = False


class ArchiveRelevanceEngine:
    @staticmethod
    def _label_matches_numbered(label: str, record_id: str, number: str) -> bool:
        prefix = f"{number}-"
        if label.lower().startswith(prefix):
            return True
        lowered_id = record_id.lower()
        return f"axiom:{number}-" in lowered_id or f"axiom:{number}:" in lowered_id

    @staticmethod
    def _label_matches_named(label: str, token: str) -> bool:
        return token.lower() in label.lower()

    @classmethod
    def _find_anchor_matches(
        cls, records: list[InvariantRecord], user_message: str
    ) -> tuple[list[InvariantRecord], str | None]:
        query = user_message or ""
        matched: list[InvariantRecord] = []
        match_desc: str | None = None

        m = _NUMBERED_ANCHOR.search(query)
        if m:
            number = m.group(1)
            matched = [r for r in records if cls._label_matches_numbered(r.label, r.id, number)]
            if matched:
                match_desc = f"axiom:{number}"

        if not matched:
            m2 = _NAMED_ANCHOR.search(query)
            if m2:
                token = m2.group(2)
                matched = [r for r in records if cls._label_matches_named(r.label, token)]
                if matched:
                    match_desc = f"{m2.group(1).lower()}:{token}"

        return matched, match_desc

    @classmethod
    def select_invariant_records(
        cls,
        records: list[InvariantRecord],
        user_message: str,
        cap: int,
    ) -> SelectionResult:
        """Select up to `cap` invariant records from `records` (assumed in
        file order), guaranteeing inclusion of any record whose label matches
        an explicit anchor reference in `user_message`, regardless of its
        position. Remaining budget is filled in original file order —
        identical to today's behavior for every record not explicitly named.
        The cap is a hard resource bound (context-flood prevention, per
        advocate.py's own comment) and is never exceeded, even by matches.
        """
        if len(records) <= cap:
            return SelectionResult(
                selected_ids=[r.id for r in records],
                excluded_ids=[],
                label_match_hit=None,
                cap_overflow=False,
            )

        promoted, match_desc = cls._find_anchor_matches(records, user_message)
        promoted = promoted[:cap]
        promoted_ids = {r.id for r in promoted}

        remaining_budget = max(cap - len(promoted), 0)
        filler = [r for r in records if r.id not in promoted_ids]
        selected_filler = filler[:remaining_budget]
        selected_filler_ids = {r.id for r in selected_filler}

        selected_ids = [r.id for r in promoted] + [r.id for r in selected_filler]
        excluded_ids = [
            r.id for r in records
            if r.id not in promoted_ids and r.id not in selected_filler_ids
        ]

        return SelectionResult(
            selected_ids=selected_ids,
            excluded_ids=excluded_ids,
            label_match_hit=match_desc,
            cap_overflow=True,
        )
