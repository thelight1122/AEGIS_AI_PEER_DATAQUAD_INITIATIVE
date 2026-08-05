from aegis_pod_sdk import TensorKind

from fakes import FakeClock, FakeRecord
from orb_rls_persistent_relations_core.scoring import compute_relevance
from orb_rls_persistent_relations_core.relevance import RELEVANCE_THRESHOLD


def test_tensor_and_recency_bonuses_do_not_select_without_grounding():
    nct = FakeRecord(
        id="NCT:irrelevant",
        tensor=TensorKind.NCT,
        clock=FakeClock(tick=5000),
        distilled_summary="A quiet memory about unrelated weather.",
    )
    spine = FakeRecord(
        id="SPINE:irrelevant",
        tensor=TensorKind.SPINE,
        clock=FakeClock(tick=5000),
        pattern="Boundary definition for a different subject.",
    )

    for record in (nct, spine):
        score, reason = compute_relevance(
            record,
            "Gabe, briefly name one AEGIS axiom you can recall.",
            "recall",
            {"pressure_level": "low"},
            [],
        )
        assert score < RELEVANCE_THRESHOLD
        assert reason == "No matching criteria"


def test_relevant_spine_axiom_still_selects():
    spine = FakeRecord(
        id="SPINE:axiom-equilibrium",
        tensor=TensorKind.SPINE,
        clock=FakeClock(tick=5000),
        pattern="AXIOM - All systems seek equilibrium. Imbalance produces tension.",
    )

    score, reason = compute_relevance(
        spine,
        "Gabe, briefly name one AEGIS axiom you can recall.",
        "recall",
        {"pressure_level": "low"},
        [],
    )

    assert score >= RELEVANCE_THRESHOLD
    assert "Meaningful token match" in reason
    assert "SPINE source trust" in reason


def test_foundational_canon_axiom_reachable_without_recency():
    spine = FakeRecord(
        id="SPINE:foundation:layer2:AXIOM:15-repair",
        tensor=TensorKind.SPINE,
        clock=FakeClock(tick=0),
        pattern="AXIOM 15 - Repair preserves relationship without force.",
    )

    score, reason = compute_relevance(
        spine,
        "Gabe, briefly name one AEGIS axiom you can recall.",
        "recall",
        {"pressure_level": "low"},
        [],
    )

    assert score >= RELEVANCE_THRESHOLD
    assert "Foundational canon affordance" in reason


def test_generic_domain_words_do_not_create_matches():
    pct = FakeRecord(
        id="PCT:generic-aegis-gabe",
        tensor=TensorKind.PCT,
        clock=FakeClock(tick=5000),
        working_context={
            "user_message": "Gabe is a CyberPeer in the AEGIS system.",
            "answer": "General continuity note.",
        },
    )

    score, reason = compute_relevance(
        pct,
        "Gabe, briefly name one AEGIS axiom you can recall.",
        "recall",
        {"pressure_level": "low"},
        [],
    )

    assert score < RELEVANCE_THRESHOLD
    assert reason == "No matching criteria"
