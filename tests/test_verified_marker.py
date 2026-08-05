from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest

from src.aegis_pod.verified_marker import load_json, run_marker_build


ROOT = Path(__file__).resolve().parents[1]


class VerifiedMarkerTest(unittest.TestCase):
    def test_marker_build_writes_hash_bound_markers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "workspace"
            shutil.copytree(ROOT, temp_root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))

            health = run_marker_build(temp_root)

            self.assertFalse(health["live_reach"])
            self.assertEqual(len(health["markers"]), 2)
            for marker_summary in health["markers"]:
                marker_path = temp_root / marker_summary["path"]
                self.assertTrue(marker_path.exists())
                marker = load_json(marker_path)
                self.assertEqual(marker["trust_state"], "provisional")
                self.assertRegex(marker["standard_hash"], r"^[A-F0-9]{64}$")
                reviewers = {review["reviewer"] for review in marker["reviews"]}
                self.assertEqual(reviewers, {"codex-local-runtime", "claude-independent-review"})
                claude_review = next(review for review in marker["reviews"] if review["reviewer"] == "claude-independent-review")
                self.assertEqual(claude_review["result"], "no_blocking_objection")
                self.assertEqual(len(claude_review["evidence"]["message_hashes"]), 2)
                self.assertFalse(marker["verification"]["live_reach"])
                self.assertIn("claim_boundary", marker)
                self.assertEqual(
                    marker["working_parameters"]["pod_state_effect"],
                    "unchanged",
                )
                self.assertEqual(
                    {command["result"] for command in marker["verification"]["commands"]},
                    {"pass"},
                )

    def test_marker_targets_are_current_runtime_layers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "workspace"
            shutil.copytree(ROOT, temp_root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))

            health = run_marker_build(temp_root)
            targets = {item["target"]["kind"]: item["target"]["id"] for item in health["markers"]}

            self.assertEqual(targets["tensor_runtime"], "local-deterministic-fixture-tensor-runtime")
            self.assertEqual(targets["orb"], "rls-orb-fixture")


if __name__ == "__main__":
    unittest.main()
