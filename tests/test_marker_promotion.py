from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import shutil
import unittest

from src.aegis_pod.marker_promotion import evaluate_marker, load_json, run_promotion_evaluation


ROOT = Path(__file__).resolve().parents[1]


class MarkerPromotionTest(unittest.TestCase):
    def test_current_markers_remain_provisional_until_three_independent_reviewers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "workspace"
            shutil.copytree(ROOT, temp_root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))

            report = run_promotion_evaluation(temp_root)

            self.assertFalse(report["working_parameters"]["live_reach"])
            self.assertFalse(report["working_parameters"]["promotion_applied"])
            self.assertGreaterEqual(report["summary"]["markers_evaluated"], 3)
            self.assertEqual(report["summary"]["reviewed_recommendations"], 0)
            self.assertEqual(report["summary"]["verified_recommendations"], 0)
            for marker in report["markers"]:
                self.assertEqual(marker["current_trust_state"], "provisional")
                self.assertEqual(marker["recommended_trust_state"], "provisional")
                self.assertFalse(marker["thresholds"]["reviewed"]["eligible"])
                self.assertFalse(marker["thresholds"]["verified"]["eligible"])
                self.assertIn(
                    "requires at least 3 independent reviewers",
                    marker["thresholds"]["reviewed"]["blockers"],
                )
                self.assertIn(
                    "requires at least 5 independent reviewers",
                    marker["thresholds"]["verified"]["blockers"],
                )

    def test_missing_reviewer_keeps_marker_provisional(self) -> None:
        policy = load_json(ROOT / "fixtures" / "marker-promotion-policy.json")
        marker = load_json(ROOT / "reports" / "runtime" / "verified-markers" / "tensor_runtime-local-deterministic-fixture-tensor-runtime.verified-code-marker.json")
        marker["reviews"] = [review for review in marker["reviews"] if review["reviewer"] == "codex-local-runtime"]

        result = evaluate_marker(marker, policy, ROOT, "synthetic-marker.json")

        self.assertEqual(result["recommended_trust_state"], "provisional")
        self.assertIn("requires at least 3 independent reviewers", result["thresholds"]["reviewed"]["blockers"])

    def test_duplicate_builder_reviews_do_not_satisfy_independent_threshold(self) -> None:
        policy = load_json(ROOT / "fixtures" / "marker-promotion-policy.json")
        marker = load_json(ROOT / "reports" / "runtime" / "verified-markers" / "tensor_runtime-local-deterministic-fixture-tensor-runtime.verified-code-marker.json")
        marker["reviews"] = [marker["reviews"][0], copy.deepcopy(marker["reviews"][0]), marker["reviews"][1]]

        result = evaluate_marker(marker, policy, ROOT, "synthetic-marker.json")

        self.assertEqual(result["reviews"]["independent_reviewer_count"], 1)
        self.assertEqual(result["recommended_trust_state"], "provisional")
        self.assertIn("requires at least 3 independent reviewers", result["thresholds"]["reviewed"]["blockers"])

    def test_failed_command_blocks_reviewed_promotion(self) -> None:
        policy = load_json(ROOT / "fixtures" / "marker-promotion-policy.json")
        marker = load_json(ROOT / "reports" / "runtime" / "verified-markers" / "tensor_runtime-local-deterministic-fixture-tensor-runtime.verified-code-marker.json")
        marker["verification"]["commands"][0]["result"] = "fail"

        result = evaluate_marker(marker, policy, ROOT, "synthetic-marker.json")

        self.assertEqual(result["recommended_trust_state"], "provisional")
        self.assertIn("all verification commands will pass", result["thresholds"]["reviewed"]["blockers"])

    def test_stale_hash_blocks_reviewed_promotion(self) -> None:
        policy = load_json(ROOT / "fixtures" / "marker-promotion-policy.json")
        marker = load_json(ROOT / "reports" / "runtime" / "verified-markers" / "tensor_runtime-local-deterministic-fixture-tensor-runtime.verified-code-marker.json")
        marker["hashes"]["implementation_hash"] = "0" * 64

        result = evaluate_marker(marker, policy, ROOT, "synthetic-marker.json")

        self.assertEqual(result["recommended_trust_state"], "provisional")
        self.assertEqual(result["recommendation_reason"], "reset_to_provisional_required")
        stale_hash_blockers = [
            blocker for blocker in result["thresholds"]["reviewed"]["blockers"]
            if blocker.startswith("declared hashes are not current:")
        ]
        self.assertTrue(stale_hash_blockers)
        self.assertTrue(any("implementation_hash" in blocker for blocker in stale_hash_blockers))
        self.assertIn("target hash drift requires reset to provisional", result["thresholds"]["reviewed"]["blockers"])

    def test_drifted_verified_marker_resets_to_provisional(self) -> None:
        policy = load_json(ROOT / "fixtures" / "marker-promotion-policy.json")
        marker = load_json(ROOT / "reports" / "runtime" / "verified-markers" / "tensor_runtime-local-deterministic-fixture-tensor-runtime.verified-code-marker.json")
        marker["trust_state"] = "verified"
        marker["hashes"]["implementation_hash"] = "0" * 64

        result = evaluate_marker(marker, policy, ROOT, "synthetic-marker.json")

        self.assertEqual(result["current_trust_state"], "verified")
        self.assertEqual(result["recommended_trust_state"], "provisional")
        self.assertEqual(result["recommendation_reason"], "reset_to_provisional_required")

    def test_claim_boundary_and_live_reach_are_gates(self) -> None:
        policy = load_json(ROOT / "fixtures" / "marker-promotion-policy.json")
        marker = load_json(ROOT / "reports" / "runtime" / "verified-markers" / "orb-rls-orb-fixture.verified-code-marker.json")
        marker = copy.deepcopy(marker)
        marker["claim_boundary"]["outside_current_verified_surface"] = []
        marker["verification"]["live_reach"] = True

        result = evaluate_marker(marker, policy, ROOT, "synthetic-marker.json")

        self.assertEqual(result["recommended_trust_state"], "provisional")
        self.assertIn(
            "claim boundary will include demonstrates and outside_current_verified_surface",
            result["thresholds"]["reviewed"]["blockers"],
        )
        self.assertIn("live_reach is outside this local promotion policy", result["thresholds"]["reviewed"]["blockers"])

    def test_missing_evidence_path_blocks_reviewed_promotion(self) -> None:
        policy = load_json(ROOT / "fixtures" / "marker-promotion-policy.json")
        marker = load_json(ROOT / "reports" / "runtime" / "verified-markers" / "orb-rls-orb-fixture.verified-code-marker.json")
        marker["verification"]["evidence_paths"].append("reports/runtime/missing-evidence.json")

        result = evaluate_marker(marker, policy, ROOT, "synthetic-marker.json")

        self.assertEqual(result["recommended_trust_state"], "provisional")
        self.assertIn(
            "evidence paths are missing or outside root: reports/runtime/missing-evidence.json",
            result["thresholds"]["reviewed"]["blockers"],
        )


if __name__ == "__main__":
    unittest.main()
