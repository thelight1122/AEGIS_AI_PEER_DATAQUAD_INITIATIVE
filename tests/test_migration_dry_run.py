from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest

from src.aegis_pod.migration_dry_run import load_json, run_dry_run, validate_manifest


ROOT = Path(__file__).resolve().parents[1]


class MigrationDryRunTest(unittest.TestCase):
    def test_manifest_matches_local_tensor_spec(self) -> None:
        manifest = load_json(ROOT / "fixtures" / "migration-dry-run.json")

        conditions = validate_manifest(manifest, ROOT)

        self.assertEqual(conditions, [])

    def test_dry_run_writes_report_without_live_reach(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "workspace"
            shutil.copytree(ROOT, temp_root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))

            health = run_dry_run(temp_root)

            self.assertFalse(health["live_reach"])
            self.assertTrue(health["ready_for_independent_review"])
            report = load_json(temp_root / health["report_path"])
            self.assertEqual(set(report["tensors"]), {"PEER", "PCT", "NCT", "SPINE"})
            self.assertEqual(report["tensors"]["PEER"]["record_count"], 2)
            self.assertEqual(report["tensors"]["PEER"]["shape"], [2, 8, 4])
            self.assertTrue(all(link["chain_link_ok"] for link in report["tensors"]["PEER"]["lineage_links"]))


if __name__ == "__main__":
    unittest.main()
