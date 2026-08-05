from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import shutil
import unittest

from src.aegis_pod.canon_housekeeping import circular_supersession_ids, evaluate_entry, run_housekeeping
from src.aegis_pod.verified_marker import load_json


ROOT = Path(__file__).resolve().parents[1]


class CanonHousekeepingTest(unittest.TestCase):
    def test_housekeeping_report_preserves_and_classifies_entries(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "workspace"
            shutil.copytree(ROOT, temp_root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))

            report = run_housekeeping(temp_root)

            self.assertFalse(report["working_parameters"]["files_deleted"])
            self.assertFalse(report["working_parameters"]["files_mutated"])
            self.assertFalse(report["working_parameters"]["live_reach"])
            self.assertEqual(report["summary"]["entries_evaluated"], 16)
            self.assertEqual(report["summary"]["superseded"], 10)
            self.assertEqual(report["summary"]["canonical"], 5)
            self.assertEqual(report["summary"]["open_question"], 1)
            self.assertEqual(report["summary"]["outside_parameters"], 0)
            self.assertIn(
                "Marking or auditing the superseded Canon copies in the Central Codex (I:\\)",
                report["working_parameters"]["outside_current_verified_surface"],
            )
            for entry in report["entries"]:
                self.assertTrue(entry["exists"])
                self.assertTrue(entry["hash_current"])
                if entry["status"] == "superseded":
                    self.assertTrue(entry["replacement_exists"])
                    self.assertTrue(entry["replacement_hash_current"])
                    self.assertTrue(entry["superseded_by"])
                self.assertTrue(entry["reason"])

    def test_missing_replacement_is_visible(self) -> None:
        manifest = load_json(ROOT / "fixtures" / "canon-housekeeping-manifest.json")
        entry = copy.deepcopy(next(item for item in manifest["entries"] if item["status"] == "superseded"))
        entry["superseded_by"] = "reports/runtime/missing-replacement.md"

        result = evaluate_entry(ROOT, entry)

        self.assertIn("replacement artifact is missing", result["outside_parameters"])
        self.assertFalse(result["replacement_exists"])

    def test_hash_change_is_visible(self) -> None:
        manifest = load_json(ROOT / "fixtures" / "canon-housekeeping-manifest.json")
        entry = copy.deepcopy(manifest["entries"][0])
        entry["source_hash"] = "0" * 64

        result = evaluate_entry(ROOT, entry)

        self.assertIn("source artifact hash changed", result["outside_parameters"])
        self.assertFalse(result["hash_current"])

    def test_self_supersession_is_visible(self) -> None:
        manifest = load_json(ROOT / "fixtures" / "canon-housekeeping-manifest.json")
        entry = copy.deepcopy(next(item for item in manifest["entries"] if item["status"] == "superseded"))
        entry["superseded_by"] = entry["path"]
        entry["replacement_hash"] = entry["source_hash"]

        result = evaluate_entry(ROOT, entry)

        self.assertIn("superseded entry points to itself", result["outside_parameters"])

    def test_outside_root_replacement_is_visible(self) -> None:
        manifest = load_json(ROOT / "fixtures" / "canon-housekeeping-manifest.json")
        entry = copy.deepcopy(next(item for item in manifest["entries"] if item["status"] == "superseded"))
        entry["superseded_by"] = "../outside.md"

        result = evaluate_entry(ROOT, entry)

        self.assertIn("replacement artifact path is outside root", result["outside_parameters"])

    def test_circular_supersession_chain_is_visible(self) -> None:
        entries = [
            {
                "entry_id": "a",
                "path": "a.md",
                "status": "superseded",
                "superseded_by": "b.md",
            },
            {
                "entry_id": "b",
                "path": "b.md",
                "status": "superseded",
                "superseded_by": "a.md",
            },
        ]

        self.assertEqual(circular_supersession_ids(entries), {"a", "b"})


if __name__ == "__main__":
    unittest.main()
