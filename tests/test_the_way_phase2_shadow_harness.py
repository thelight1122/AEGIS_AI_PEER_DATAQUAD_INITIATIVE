from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
FIXTURES = ROOT / "fixtures"
PACKAGE_SRC = ROOT / "packages" / "orb-identity-field-builder-core" / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from orb_identity_field_builder_core import (  # noqa: E402
    ShadowHarnessError,
    build_phase2_shadow_report,
    build_phase2_shadow_report_from_files,
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _errors(schema_name: str, instance) -> list[str]:
    return [e.message for e in Draft202012Validator(_load(CONTRACTS / schema_name)).iter_errors(instance)]


def _fixtures():
    return (
        _load(FIXTURES / "spine-snapshot-gabe.json"),
        _load(FIXTURES / "tension-observations-gabe.json"),
    )


def test_offline_shadow_harness_builds_packet_and_observation():
    snapshot, observations = _fixtures()
    result = build_phase2_shadow_report(
        spine_snapshot=snapshot,
        tension_observations=observations,
        retrieved_identity_continuity=[
            "[AXIOM:non-force] Non-force: I offer and make room; I never require or push.",
            "[NCT:stale] Prior session note: the user prefers concise answers about billing.",
        ],
        turn_ref="PEER:CP-1003-GABE:offline-shadow:0001",
    )

    assert result.emitted_packet is True
    report = result.report
    assert report["injected"] is False
    assert report["live_system_touched"] is False
    assert report["failure_is_data"] is False
    assert _errors("identity-image-packet.schema.json", report["packet"]) == []
    assert report["packet"]["negative_space_policy"]["witness_is_represented"] is False
    assert all(t["status"] == "held" for t in report["packet"]["active_held_tensions"])
    assert report["shadow_observation"]["retrieval_not_in_foundation"]


def test_offline_shadow_harness_fails_safe_without_invariant_spine():
    _, observations = _fixtures()
    result = build_phase2_shadow_report(
        spine_snapshot={
            "peer_id": "CP-1003-GABE",
            "spine_records": [
                {
                    "id": "SPINE:CP-1003-GABE:situational:1",
                    "pattern": "Situational context only",
                    "invariant": False,
                }
            ],
        },
        tension_observations=observations,
        retrieved_identity_continuity=[],
        turn_ref="PEER:CP-1003-GABE:offline-shadow:missing",
    )

    assert result.emitted_packet is False
    assert result.report["failure_is_data"] is True
    assert "packet" not in result.report
    assert result.report["injected"] is False
    assert result.report["live_system_touched"] is False


def test_offline_shadow_harness_returns_budget_overflow_as_failure_data():
    snapshot, observations = _fixtures()
    result = build_phase2_shadow_report(
        spine_snapshot=snapshot,
        tension_observations=observations,
        retrieved_identity_continuity=[],
        turn_ref="PEER:CP-1003-GABE:offline-shadow:budget-overflow",
        policy={"max_chars": 1},
    )

    assert result.emitted_packet is False
    assert result.report["failure_is_data"] is True
    assert "IdentityImagePacket exceeds budget" in result.report["failure_reason"]
    assert result.report["input_hashes"]
    assert "packet" not in result.report
    assert result.report["injected"] is False
    assert result.report["live_system_touched"] is False


def test_offline_shadow_harness_file_reader_writes_only_explicit_output(tmp_path):
    output = tmp_path / "phase2a-shadow-report.json"
    result = build_phase2_shadow_report_from_files(
        spine_snapshot_path=FIXTURES / "spine-snapshot-gabe.json",
        tension_observations_path=FIXTURES / "tension-observations-gabe.json",
        retrieved_identity_continuity=[],
        turn_ref="PEER:CP-1003-GABE:offline-shadow:file",
        output_path=output,
    )

    assert result.emitted_packet is True
    written = _load(output)
    assert written["report_kind"] == "the-way-phase2a-offline-shadow-report"
    assert written["identity_image_packet_hash"] == result.report["identity_image_packet_hash"]


def test_offline_shadow_harness_rejects_missing_files():
    with pytest.raises(ShadowHarnessError):
        build_phase2_shadow_report_from_files(
            spine_snapshot_path=FIXTURES / "missing-spine.json",
            tension_observations_path=FIXTURES / "tension-observations-gabe.json",
            retrieved_identity_continuity=[],
            turn_ref="PEER:CP-1003-GABE:offline-shadow:bad-file",
        )


def test_offline_shadow_harness_never_uses_live_action_tokens():
    targets = [
        PACKAGE_SRC / "orb_identity_field_builder_core" / "phase2_shadow.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in targets)
    forbidden = ["az vm", "kubectl", "ssh ", "docker", "invoke" + "-command"]
    assert not any(token in text for token in forbidden)
