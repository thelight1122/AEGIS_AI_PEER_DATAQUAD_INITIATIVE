from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.aegis_pod.copied_record_dry_run import run_dry_run
from src.aegis_pod.tensor_runtime import sha256_text, stable_json, verify_source_hash


ROOT = Path(__file__).resolve().parents[1]


class CopiedRecordDryRunTest(unittest.TestCase):
    def test_builds_manifest_without_migration_execution(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "manifest.json"
            manifest = run_dry_run(ROOT, output_path=output_path)

            self.assertTrue(output_path.exists())
            self.assertFalse(manifest["live_reach"])
            self.assertFalse(manifest["dry_run_result"]["migration_executed"])
            self.assertEqual(manifest["dry_run_result"]["target_records_written"], 0)
            self.assertEqual(manifest["source_counts"]["total_records"], 5)
            self.assertEqual(manifest["source_counts"]["outside_parameter_records"], 0)
            self.assertEqual(manifest["tensor_target_mapping"]["PEER"]["target_shape"], [2, 8, 4])
            self.assertEqual(manifest["tensor_target_mapping"]["PCT"]["target_shape"], [1, 8, 4])

    def test_manifest_reports_hash_verification_and_lineage_visibility(self) -> None:
        manifest = run_dry_run(ROOT)

        peer_hashes = [item for item in manifest["hash_preservation"]["records"] if item["tensor"] == "PEER"]
        self.assertEqual(len(peer_hashes), 2)
        counts = manifest["hash_preservation"]["verification_counts"]
        self.assertEqual(counts["mismatch"], 0)
        self.assertEqual(sum(counts.values()), 5)
        # Fixture records cite source files that are not in this workspace, so their
        # hashes will be reported as unverifiable rather than claimed preserved.
        self.assertTrue(all(
            item["verification"] == "unverifiable_source_absent" and item["preserved"] is None
            for item in manifest["hash_preservation"]["records"]
        ))
        peer_lineage = [item for item in manifest["lineage_continuity"]["records"] if item["tensor"] == "PEER"]
        self.assertEqual(peer_lineage[0]["continuity_status"], "root_record")
        self.assertEqual(peer_lineage[1]["continuity_status"], "continuous")
        self.assertEqual(manifest["lineage_continuity"]["broken_chain_count"], 0)

    def test_source_hash_verification_distinguishes_real_states(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_data = {"context": "source record", "thread": "hash check"}
            source_path = root / "fixtures" / "source-records" / "PCT" / "source-pct-0001.json"
            source_path.parent.mkdir(parents=True)
            source_path.write_text(stable_json(source_data), encoding="utf-8")
            relative = "fixtures/source-records/PCT/source-pct-0001.json"

            matching = {
                "source_hash": sha256_text(stable_json(source_data)),
                "lineage": {"source_path": relative},
            }
            self.assertEqual(verify_source_hash(matching, root)["verification"], "verified")
            self.assertIs(verify_source_hash(matching, root)["preserved"], True)

            mismatching = {"source_hash": "0" * 64, "lineage": {"source_path": relative}}
            self.assertEqual(verify_source_hash(mismatching, root)["verification"], "mismatch")
            self.assertIs(verify_source_hash(mismatching, root)["preserved"], False)

            absent = {"source_hash": "0" * 64, "lineage": {"source_path": "fixtures/missing.json"}}
            self.assertEqual(verify_source_hash(absent, root)["verification"], "unverifiable_source_absent")
            self.assertIsNone(verify_source_hash(absent, root)["preserved"])


if __name__ == "__main__":
    unittest.main()
