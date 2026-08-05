"""Tests for the Pod-facing MemorySearch entrypoint (Claude's slice): the result -> packet
mapper. Validates the returned packet against contracts/memorysearch-packet.schema.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "orb-memorysearch-record-grounding-core" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from orb_memorysearch_record_grounding_core import ground_record_claim


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _records():
    return _load(ROOT / "fixtures" / "memorysearch-records.json")


def _policy():
    return _load(ROOT / "fixtures" / "memorysearch-policy.json")


def _packet_schema():
    return _load(ROOT / "contracts" / "memorysearch-packet.schema.json")


def test_not_a_record_claim_returns_none():
    packet = ground_record_claim("Who are you becoming in this moment?", _records(), _policy())
    assert packet is None


def test_verified_packet_is_schema_valid_and_carries_citations():
    packet = ground_record_claim(
        "What is NCT according to the Canon in your DataQuad?", _records(), _policy()
    )
    assert packet is not None
    jsonschema.validate(packet, _packet_schema())
    assert packet["grounding_status"] == "verified_retrieval"
    assert packet["cited_records"], "verified packet needs at least one runtime-authored citation"
    assert all(c["match_confidence"] in {"high", "medium", "low"} for c in packet["cited_records"])
    assert packet["twitness_event"]["record_search_performed"] is True
    # provenance is runtime-authored, present on the verified path
    assert len(packet["twitness_event"]["orb_runtime_hash"]) == 64


def test_no_verified_record_packet_is_schema_valid_and_blocks_reconstruction():
    packet = ground_record_claim(
        "What is ZCT according to the Canon in your DataQuad?", _records(), _policy()
    )
    assert packet is not None
    jsonschema.validate(packet, _packet_schema())
    # empty-result path returns a PACKET, not None
    assert packet["grounding_status"] == "search_performed_no_verified_record"
    assert packet["cited_records"] == []
    assert "do not present reconstruction as record-grounded" in packet["prompt_block"].lower()
    assert packet["twitness_event"]["record_search_performed"] is True
