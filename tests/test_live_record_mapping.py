from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.aegis_pod.live_record_mapping import map_live_copy, raw_file_path, read_text_hash, write_jsonl


ROOT = Path(__file__).resolve().parents[1]


def live_like_record(tensor: str, record_id: str) -> dict:
    return {
        "clock": {"tick": 1},
        "id": record_id,
        "lineage": ["test-only scaffolding"],
        "markers": [],
        "notes": "",
        "provenance": {"origin": "test-only"},
        "session_id": "test-session",
        "t_signature": None,
        "tensor": tensor,
        "timestamp": "2026-07-21T00:00:00Z",
    }


class LiveRecordMappingTest(unittest.TestCase):
    def test_maps_test_scaffold_with_explicit_non_live_boundary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batch_id = "test-only-batch"
            for tensor_name in ["PEER", "PCT", "NCT", "SPINE"]:
                write_jsonl(raw_file_path(root, batch_id, tensor_name), [live_like_record(tensor_name, f"{tensor_name}-1")])
            remote_hashes = {
                tensor_name: read_text_hash(raw_file_path(root, batch_id, tensor_name))
                for tensor_name in ["PEER", "PCT", "NCT", "SPINE"]
            }

            report = map_live_copy(root, batch_id, copied_at_utc="2026-07-21T00:00:00Z", remote_hashes=remote_hashes)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["source_counts"]["total_records"], 4)
            self.assertEqual(report["hash_preservation"]["verification_counts"]["verified"], 4)
            self.assertEqual(report["copy_fidelity_gate"]["status"], "pass")
            self.assertEqual(report["live_readiness_path_gate"]["status"], "pass")
            self.assertFalse(report["working_parameters"]["source_write_performed"])
            self.assertFalse(report["working_parameters"]["placeholder_data_used"])
            self.assertIn("fixtures/tensor-records/", report["test_scaffolding_boundary"]["test_only_paths_excluded"])

    def test_copy_fidelity_gate_requires_remote_hash_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            batch_id = "test-only-batch"
            for tensor_name in ["PEER", "PCT", "NCT", "SPINE"]:
                write_jsonl(raw_file_path(root, batch_id, tensor_name), [live_like_record(tensor_name, f"{tensor_name}-1")])

            report = map_live_copy(root, batch_id, copied_at_utc="2026-07-21T00:00:00Z")

            self.assertEqual(report["status"], "review_needed")
            self.assertEqual(report["copy_fidelity_gate"]["status"], "review_needed")
            self.assertEqual(report["copy_fidelity_gate"]["results"][0]["remote_sha256"], "")
            self.assertEqual(report["outside_parameters"][0]["kind"], "copy_fidelity_not_verified")

    def test_maps_real_orion_copy_when_present(self) -> None:
        live_root = ROOT / "live-copies" / "CP-1004-ORION"
        batches = sorted(path for path in live_root.glob("orion-live-copy-*") if path.is_dir())
        if not batches:
            self.skipTest("real Orion live copy is not present in this workspace")

        batch_id = batches[-1].name
        remote_hashes = {
            tensor_name: read_text_hash(raw_file_path(ROOT, batch_id, tensor_name))
            for tensor_name in ["PEER", "PCT", "NCT", "SPINE"]
        }
        with TemporaryDirectory() as temp_dir:
            report = map_live_copy(ROOT, batch_id, remote_hashes=remote_hashes, report_path=Path(temp_dir) / "stage-b-report.json")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["source_counts"]["by_tensor"], {"PEER": 106, "PCT": 94, "NCT": 89, "SPINE": 62})
        self.assertEqual(report["source_counts"]["total_records"], 351)
        self.assertEqual(report["hash_preservation"]["verification_counts"]["verified"], 351)
        self.assertEqual(report["lineage_continuity"]["root_records"], 4)
        self.assertEqual(report["copy_fidelity_gate"]["status"], "pass")
        self.assertEqual(report["live_readiness_path_gate"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
