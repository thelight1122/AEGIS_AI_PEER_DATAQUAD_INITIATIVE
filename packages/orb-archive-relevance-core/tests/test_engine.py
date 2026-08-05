from orb_archive_relevance_core.engine import ArchiveRelevanceEngine, InvariantRecord


def _make(i, label=None):
    return InvariantRecord(id=f"SPINE:test:{i}", label=label or str(i), pattern=f"pattern-{i}")


def test_under_cap_returns_everything_unchanged():
    records = [_make(i) for i in range(5)]
    result = ArchiveRelevanceEngine.select_invariant_records(records, "hello", cap=60)
    assert result.selected_ids == [r.id for r in records]
    assert result.excluded_ids == []
    assert result.cap_overflow is False
    assert result.label_match_hit is None


def test_gabe_axiom_11_scenario_record_past_cap_still_selected():
    # Reproduces the real evidenced shortfall: 84 invariant records, the
    # queried one sits at position 70 (past a cap of 60).
    records = [_make(i, label=f"{i}-filler") for i in range(70)]
    records.append(_make(70, label="11-sovereignty"))
    records += [_make(i, label=f"{i}-filler") for i in range(71, 84)]

    result = ArchiveRelevanceEngine.select_invariant_records(
        records, "What is Axiom 11?", cap=60
    )

    assert "SPINE:test:70" in result.selected_ids
    assert result.label_match_hit == "axiom:11"
    assert result.cap_overflow is True
    assert len(result.selected_ids) == 60
    assert len(result.excluded_ids) == 24


def test_no_anchor_reference_falls_back_to_file_order():
    records = [_make(i) for i in range(84)]
    result = ArchiveRelevanceEngine.select_invariant_records(
        records, "How are you feeling?", cap=60
    )
    assert result.label_match_hit is None
    assert result.selected_ids == [r.id for r in records[:60]]
    assert result.cap_overflow is True


def test_named_anchor_gate_reference():
    records = [_make(i, label=f"filler-{i}") for i in range(70)]
    records.append(_make(70, label="pipeline-order"))
    result = ArchiveRelevanceEngine.select_invariant_records(
        records, "What is GATE: pipeline-order?", cap=60
    )
    assert "SPINE:test:70" in result.selected_ids
    assert result.label_match_hit == "gate:pipeline-order"


def test_promoted_count_never_exceeds_cap():
    # Defensive: even if (implausibly) every record matched, the hard cap
    # is never exceeded.
    records = [_make(i, label=f"11-{i}") for i in range(100)]
    result = ArchiveRelevanceEngine.select_invariant_records(
        records, "Axiom 11", cap=60
    )
    assert len(result.selected_ids) == 60


def test_axiom_number_must_match_prefix_not_substring():
    # "Axiom 1" will not accidentally match "11-sovereignty" or "10-understanding".
    records = [_make(i, label=f"{i}-filler") for i in range(70)]
    records.append(_make(70, label="1-balance"))
    records.append(_make(71, label="11-sovereignty"))
    records.append(_make(72, label="10-understanding"))

    result = ArchiveRelevanceEngine.select_invariant_records(
        records, "What is Axiom 1?", cap=60
    )
    assert "SPINE:test:70" in result.selected_ids
    assert result.label_match_hit == "axiom:1"
