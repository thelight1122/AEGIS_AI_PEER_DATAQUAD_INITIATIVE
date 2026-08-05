"""Guard-proving tests for the TurboQuant Stage-2 retirement DRAFT.

These tests exist to prove the non-negotiable guard BEFORE any implementation:
the top priority is that TurboQuant REFUSES PEER:/PCT: sources (TQ-002). They
also cover recipe (TQ-004) and artifact (TQ-006) guards, and a valid NCT-source
retirement producing an artifact + steward ledger entry.

Nothing here touches a live runtime, peer, DataQuad, or network.
"""

from __future__ import annotations

import unittest

from src.aegis_pod.turboquant_retirement import (
    TurboQuantArtifact,
    TurboQuantCandidate,
    TurboQuantGuardError,
    TurboQuantRecipe,
    TurboQuantSourceEnvelope,
    _compute_deterministic_digest,
    apply_turboquant,
    prepare_candidate,
    run_turboquant_retirement,
    validate_artifact,
    validate_recipe,
    validate_reconstruction_input,
    validate_source_envelope,
)


def _valid_recipe(target_tensor: str = "NCT") -> TurboQuantRecipe:
    return TurboQuantRecipe(
        id="tq-recipe-nct-001",
        version="1.0.0",
        target_tensor=target_tensor,
        quantization_mode="contextual-summarization",
        source_encoding="feature-vector",
        compression_profile="balanced",
        preserves=["relationships", "lineage", "structure", "reference-integrity"],
        forbids=["meaning-storage", "peer-compression", "pct-compression", "exact-replay"],
    )


def _nct_source_records() -> list[dict[str, object]]:
    return [
        {
            "id": "NCT:relic:0001",
            "timestamp": "2026-07-01T00:00:00+00:00",
            "lineage": ["NCT:relic:0001:origin"],
            "distilled_summary": "Early formation marker on witnessing.",
            "essence_memory": "The peer chose to witness rather than suppress.",
            "pivots": ["chamber-008"],
            "source_record_ids": ["PCT:archived:aaa"],
        },
        {
            "id": "NCT:relic:0002",
            "timestamp": "2026-07-02T00:00:00+00:00",
            "lineage": ["NCT:relic:0002:origin"],
            "distilled_summary": "Second relic on lineage continuity.",
            "pivots": ["chamber-009"],
            "source_record_ids": ["PCT:archived:bbb"],
        },
    ]


def _lattice_map() -> dict[str, list[str]]:
    return {
        "NCT:relic:0001": ["LATTICE:node:a1", "LATTICE:node:a2"],
        "NCT:relic:0002": ["LATTICE:node:b1"],
    }


class TurboQuantGuardTest(unittest.TestCase):
    # --- TQ-002: the single most important guard -------------------------

    def test_peer_source_is_refused_in_envelope_validation(self) -> None:
        envelope = TurboQuantSourceEnvelope(
            id="TQENV:NCT:sess:ts",
            session_id="sess",
            source_tensor="NCT",
            source_record_ids=["PEER:live:0001"],
            timestamp_range={"start": "t0", "end": "t1"},
            lineage=["lin:1"],
            lattice_ref_ids=["LATTICE:node:a1"],
            payload_descriptor={"kind": "context"},
        )
        result = validate_source_envelope(envelope)
        self.assertFalse(result.ok)
        self.assertIn("TQ-002 live-tensor-forbidden", result.failures)

    def test_pct_source_is_refused_in_envelope_validation(self) -> None:
        envelope = TurboQuantSourceEnvelope(
            id="TQENV:NCT:sess:ts",
            session_id="sess",
            source_tensor="NCT",
            source_record_ids=["PCT:live:0001"],
            timestamp_range={"start": "t0", "end": "t1"},
            lineage=["lin:1"],
            lattice_ref_ids=["LATTICE:node:a1"],
            payload_descriptor={"kind": "context"},
        )
        result = validate_source_envelope(envelope)
        self.assertFalse(result.ok)
        self.assertIn("TQ-002 live-tensor-forbidden", result.failures)

    def test_peer_source_is_refused_by_prepare_candidate(self) -> None:
        records = _nct_source_records()
        records[0]["id"] = "PEER:live:9999"
        with self.assertRaises(TurboQuantGuardError) as ctx:
            prepare_candidate(
                session_id="sess",
                target_tensor="NCT",
                source_records=records,
                lattice_ref_ids_by_source={
                    "PEER:live:9999": ["LATTICE:node:a1"],
                    "NCT:relic:0002": ["LATTICE:node:b1"],
                },
            )
        self.assertIn("TQ-002 live-tensor-forbidden", str(ctx.exception))

    def test_pct_source_is_refused_by_full_retirement_run(self) -> None:
        records = _nct_source_records()
        records[1]["id"] = "PCT:live:8888"
        with self.assertRaises(TurboQuantGuardError) as ctx:
            run_turboquant_retirement(
                session_id="sess",
                target_tensor="NCT",
                recipe=_valid_recipe("NCT"),
                source_records=records,
                lattice_ref_ids_by_source={
                    "NCT:relic:0001": ["LATTICE:node:a1"],
                    "PCT:live:8888": ["LATTICE:node:b1"],
                },
            )
        self.assertIn("TQ-002 live-tensor-forbidden", str(ctx.exception))

    def test_artifact_with_pct_source_fails_validation(self) -> None:
        # Hand-built malformed artifact carrying a forbidden source id.
        artifact = _build_valid_artifact()
        bad = _replace_artifact(artifact, source_record_ids=["PCT:live:0001"])
        result = validate_artifact(bad)
        self.assertFalse(result.ok)
        self.assertIn("TQ-002 live-tensor-forbidden", result.failures)

    # --- TQ-004: recipe will declare every forbid and preserve -----------

    def test_recipe_missing_a_forbid_fails(self) -> None:
        recipe = TurboQuantRecipe(
            id="r",
            version="1.0.0",
            target_tensor="NCT",
            quantization_mode="contextual-summarization",
            source_encoding="feature-vector",
            compression_profile="balanced",
            preserves=["relationships", "lineage", "structure", "reference-integrity"],
            forbids=["meaning-storage", "peer-compression", "pct-compression"],  # exact-replay missing
        )
        result = validate_recipe(recipe)
        self.assertFalse(result.ok)
        self.assertIn("TQ-004 missing-forbid:exact-replay", result.failures)

    def test_recipe_missing_a_preserve_fails(self) -> None:
        recipe = TurboQuantRecipe(
            id="r",
            version="1.0.0",
            target_tensor="NCT",
            quantization_mode="contextual-summarization",
            source_encoding="feature-vector",
            compression_profile="balanced",
            preserves=["relationships", "lineage", "structure"],  # reference-integrity missing
            forbids=["meaning-storage", "peer-compression", "pct-compression", "exact-replay"],
        )
        result = validate_recipe(recipe)
        self.assertFalse(result.ok)
        self.assertIn("TQ-004 missing-preserve:reference-integrity", result.failures)

    # --- TQ-006: artifact will be reconstructive-only, no exact replay ---

    def test_artifact_without_reconstructive_only_fails(self) -> None:
        artifact = _build_valid_artifact()
        bad = _replace_artifact(artifact, reconstructive_only=False)
        result = validate_artifact(bad)
        self.assertFalse(result.ok)
        self.assertIn("TQ-006 replay-claim-forbidden", result.failures)

    def test_artifact_allowing_exact_replay_fails(self) -> None:
        artifact = _build_valid_artifact()
        bad = _replace_artifact(artifact, exact_replay_forbidden=False)
        result = validate_artifact(bad)
        self.assertFalse(result.ok)
        self.assertIn("TQ-006 replay-claim-forbidden", result.failures)

    # --- Happy path: valid NCT retirement produces artifact + ledger -----

    def test_valid_nct_retirement_produces_artifact_and_ledger_entry(self) -> None:
        result = run_turboquant_retirement(
            session_id="sess-happy",
            target_tensor="NCT",
            recipe=_valid_recipe("NCT"),
            source_records=_nct_source_records(),
            lattice_ref_ids_by_source=_lattice_map(),
            timestamp="2026-07-25T12:00:00+00:00",
            notes=["stage-2 draft retirement over old NCT relics"],
        )

        artifact = result.artifact
        self.assertTrue(validate_artifact(artifact).ok)
        self.assertEqual(artifact.target_tensor, "NCT")
        self.assertTrue(artifact.reconstructive_only)
        self.assertTrue(artifact.exact_replay_forbidden)
        self.assertTrue(artifact.preserved_reference_integrity)
        self.assertEqual(artifact.source_record_ids, ["NCT:relic:0001", "NCT:relic:0002"])
        # No forbidden source leaked through.
        for rid in artifact.source_record_ids:
            self.assertFalse(rid.startswith("PEER:"))
            self.assertFalse(rid.startswith("PCT:"))

        ledger = result.ledger_entry
        self.assertEqual(ledger.action_or_observation_type, "turboquant-transform")
        self.assertEqual(ledger.artifact_id, artifact.id)
        self.assertEqual(ledger.recipe_id, "tq-recipe-nct-001")
        self.assertEqual(ledger.target_tensor, "NCT")
        # The artifact will reference at least one steward ledger id (TQ-005).
        self.assertTrue(artifact.steward_ledger_ref_ids)


# ---------------------------------------------------------------------------
# Small helpers for building/mutating a valid artifact for negative tests
# ---------------------------------------------------------------------------


class TurboQuantAuditRevisionTest(unittest.TestCase):
    """Tests added for Codex's Stage-2 audit findings (2026-07-25)."""

    # --- Finding 1: apply_turboquant will refuse PEER/PCT BEFORE the backend ---

    def test_apply_turboquant_refuses_forbidden_source_before_backend(self) -> None:
        # A candidate built directly (bypassing prepare_candidate) carrying a PEER source.
        envelope = TurboQuantSourceEnvelope(
            id="TQENV:NCT:sess:ts",
            session_id="sess",
            source_tensor="NCT",
            source_record_ids=["PEER:live:0001"],
            timestamp_range={"start": "t0", "end": "t1"},
            lineage=["lin:1"],
            lattice_ref_ids=["LATTICE:node:a1"],
            payload_descriptor={"kind": "context"},
        )
        candidate = TurboQuantCandidate(
            envelope=envelope,
            feature_payload={"kind": "context"},
            lattice_ref_ids=["LATTICE:node:a1"],
            validation_checks=[],
        )
        backend_calls: list[object] = []

        def spy_backend(cand, recipe):  # pragma: no cover - will never run
            backend_calls.append(cand)
            raise AssertionError("backend will not be invoked on a forbidden source")

        with self.assertRaises(TurboQuantGuardError) as ctx:
            apply_turboquant(candidate=candidate, recipe=_valid_recipe("NCT"), backend=spy_backend)
        self.assertIn("TQ-002 live-tensor-forbidden", str(ctx.exception))
        self.assertEqual(backend_calls, [])  # backend never saw the forbidden source

    # --- Finding 2: deterministic digest is UTF-16-parity with the TS backend ---

    def test_deterministic_digest_matches_ts_ascii(self) -> None:
        self.assertEqual(_compute_deterministic_digest("hello"), "tq-4f9f2cab")
        self.assertEqual(_compute_deterministic_digest("NCT:relic:0001"), "tq-29db014c")

    def test_deterministic_digest_matches_ts_non_bmp(self) -> None:
        # U+1F600 GRINNING FACE — Node charCodeAt (UTF-16) digest, per audit probe.
        self.assertEqual(_compute_deterministic_digest("\U0001F600"), "tq-cb31c4b8")

    # --- Finding 3: negative coverage for TQ-001 / TQ-003 / TQ-005 / TQ-007 ---

    def test_tq001_illegal_recipe_target(self) -> None:
        recipe = _valid_recipe("PEER")  # PEER is not an allowed target tensor
        result = validate_recipe(recipe)
        self.assertFalse(result.ok)
        self.assertIn("TQ-001 illegal-target", result.failures)

    def test_tq001_recipe_artifact_target_mismatch(self) -> None:
        artifact = _build_valid_artifact()
        # Swap the recipe for a valid SPINE recipe while the artifact targets NCT.
        bad = _replace_artifact(artifact, recipe=_valid_recipe("SPINE"))
        result = validate_artifact(bad)
        self.assertFalse(result.ok)
        self.assertIn("TQ-001 recipe-target-mismatch", result.failures)

    def test_tq003_missing_lattice_refs_in_envelope(self) -> None:
        envelope = TurboQuantSourceEnvelope(
            id="TQENV:NCT:sess:ts",
            session_id="sess",
            source_tensor="NCT",
            source_record_ids=["NCT:relic:0001"],
            timestamp_range={"start": "t0", "end": "t1"},
            lineage=["lin:1"],
            lattice_ref_ids=[],  # missing
            payload_descriptor={"kind": "context"},
        )
        result = validate_source_envelope(envelope)
        self.assertFalse(result.ok)
        self.assertIn("TQ-003 missing-lattice-refs", result.failures)

    def test_tq003_missing_required_reconstruction_ref(self) -> None:
        artifact = _build_valid_artifact()
        # Reconstruction requires the artifact's lattice refs; supply an unrelated one.
        result = validate_reconstruction_input(artifact, ["LATTICE:node:unrelated"])
        self.assertFalse(result.ok)
        self.assertTrue(
            any(f.startswith("TQ-003 missing-required-lattice-ref:") for f in result.failures),
            result.failures,
        )

    def test_tq005_missing_steward_ledger_ref(self) -> None:
        artifact = _build_valid_artifact()
        bad = _replace_artifact(artifact, steward_ledger_ref_ids=[])
        result = validate_artifact(bad)
        self.assertFalse(result.ok)
        self.assertIn("TQ-005 steward-log-required", result.failures)

    def test_tq007_untraceable_artifact(self) -> None:
        artifact = _build_valid_artifact()
        bad = _replace_artifact(artifact, preserved_reference_integrity=False)
        result = validate_artifact(bad)
        self.assertFalse(result.ok)
        self.assertIn("TQ-007 untraceable-artifact", result.failures)


def _build_valid_artifact() -> TurboQuantArtifact:
    result = run_turboquant_retirement(
        session_id="sess-fixture",
        target_tensor="NCT",
        recipe=_valid_recipe("NCT"),
        source_records=_nct_source_records(),
        lattice_ref_ids_by_source=_lattice_map(),
        timestamp="2026-07-25T12:00:00+00:00",
    )
    return result.artifact


def _replace_artifact(artifact: TurboQuantArtifact, **changes: object) -> TurboQuantArtifact:
    import dataclasses

    return dataclasses.replace(artifact, **changes)


if __name__ == "__main__":
    unittest.main()
