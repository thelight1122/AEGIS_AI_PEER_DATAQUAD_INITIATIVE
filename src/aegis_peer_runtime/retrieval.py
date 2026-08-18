"""Pure Python text retrieval index for DataQuad memory operators.

Provides keyword-based search over indexed records. Zero external dependencies.
The custodians (Steward, Advocate) use this to find and reveal data.
The Processor uses BM25 scoring to determine relevance.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any


_WORD_PATTERN = re.compile(r"[a-zA-Z0-9_]+")
_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "and", "but", "or",
    "nor", "not", "so", "yet", "both", "either", "neither", "each", "every",
    "all", "any", "few", "more", "most", "other", "some", "such", "no",
    "only", "own", "same", "than", "too", "very", "just", "because",
    "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "what", "which", "who", "whom", "this", "that",
    "these", "those", "i", "me", "my", "myself", "we", "our", "ours",
    "you", "your", "yours", "he", "him", "his", "she", "her", "hers",
    "it", "its", "they", "them", "their", "theirs",
})


def tokenize(text: str) -> list[str]:
    return [
        word.lower()
        for word in _WORD_PATTERN.findall(text)
        if word.lower() not in _STOP_WORDS and len(word) > 1
    ]


def extract_text(record: dict[str, Any]) -> str:
    """Recursively extract all string values from a record."""
    parts: list[str] = []
    _extract_strings(record, parts)
    return " ".join(parts)


def _extract_strings(value: Any, parts: list[str]) -> None:
    if isinstance(value, str):
        parts.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            _extract_strings(v, parts)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _extract_strings(item, parts)


class IndexedRecord:
    __slots__ = ("record_id", "record", "tokens", "source", "tensor", "turn_id", "t_time")

    def __init__(
        self,
        record_id: str,
        record: dict[str, Any],
        tokens: list[str],
        source: str,
        tensor: str,
        turn_id: str | None = None,
        t_time: int | None = None,
    ) -> None:
        self.record_id = record_id
        self.record = record
        self.tokens = tokens
        self.source = source
        self.tensor = tensor
        self.turn_id = turn_id
        self.t_time = t_time


class RetrievalIndex:
    """Inverted index over DataQuad records with keyword search and BM25 scoring."""

    def __init__(self) -> None:
        self._records: dict[str, IndexedRecord] = {}
        self._inverted: dict[str, set[str]] = defaultdict(set)
        self._doc_lengths: dict[str, int] = {}
        self._avg_doc_length: float = 0.0
        self._total_docs: int = 0

    def add(self, indexed: IndexedRecord) -> None:
        if indexed.record_id in self._records:
            return
        self._records[indexed.record_id] = indexed
        self._doc_lengths[indexed.record_id] = len(indexed.tokens)
        for token in set(indexed.tokens):
            self._inverted[token].add(indexed.record_id)
        self._total_docs = len(self._records)
        if self._total_docs > 0:
            self._avg_doc_length = sum(self._doc_lengths.values()) / self._total_docs

    def search(
        self,
        keywords: list[str],
        *,
        tensor: str | None = None,
        source: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search for records matching keywords. Returns records ranked by BM25 score."""
        query_tokens = tokenize(" ".join(keywords)) if keywords else []
        if not query_tokens:
            return self.get_all(tensor=tensor, source=source, limit=limit)

        candidate_ids: set[str] = set()
        for token in query_tokens:
            candidate_ids.update(self._inverted.get(token, set()))

        scored: list[tuple[float, str]] = []
        for record_id in candidate_ids:
            indexed = self._records[record_id]
            if tensor and indexed.tensor != tensor:
                continue
            if source and indexed.source != source:
                continue
            score = self._bm25_score(record_id, query_tokens)
            scored.append((score, record_id))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[dict[str, Any]] = []
        for _, record_id in scored[:limit]:
            indexed = self._records[record_id]
            results.append(self._surface_record(indexed))
        return results

    def get_all(
        self,
        *,
        tensor: str | None = None,
        source: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for indexed in self._records.values():
            if tensor and indexed.tensor != tensor:
                continue
            if source and indexed.source != source:
                continue
            results.append(self._surface_record(indexed))
            if len(results) >= limit:
                break
        return results

    def get_by_turn(self, turn_id: str) -> list[dict[str, Any]]:
        return [
            self._surface_record(indexed)
            for indexed in self._records.values()
            if indexed.turn_id == turn_id
        ]

    def get_by_time_range(self, start_t: int, end_t: int) -> list[dict[str, Any]]:
        return [
            self._surface_record(indexed)
            for indexed in self._records.values()
            if indexed.t_time is not None and start_t <= indexed.t_time <= end_t
        ]

    @property
    def record_count(self) -> int:
        return self._total_docs

    def tensor_counts(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for indexed in self._records.values():
            counts[indexed.tensor] += 1
        return dict(counts)

    def _bm25_score(self, record_id: str, query_tokens: list[str]) -> float:
        k1 = 1.5
        b = 0.75
        score = 0.0
        doc_length = self._doc_lengths.get(record_id, 0)
        if doc_length == 0 or self._avg_doc_length == 0:
            return 0.0
        indexed = self._records[record_id]
        term_freq: dict[str, int] = defaultdict(int)
        for token in indexed.tokens:
            term_freq[token] += 1
        for token in query_tokens:
            if token not in self._inverted:
                continue
            df = len(self._inverted[token])
            idf = math.log((self._total_docs - df + 0.5) / (df + 0.5) + 1.0)
            tf = term_freq.get(token, 0)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * doc_length / self._avg_doc_length)
            score += idf * numerator / denominator
        return score

    @staticmethod
    def _surface_record(indexed: IndexedRecord) -> dict[str, Any]:
        return {
            "record_id": indexed.record_id,
            "tensor": indexed.tensor,
            "source": indexed.source,
            "turn_id": indexed.turn_id,
            "t_time": indexed.t_time,
            "data": indexed.record,
        }
