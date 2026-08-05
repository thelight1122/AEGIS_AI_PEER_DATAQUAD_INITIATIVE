from pathlib import Path
import unittest

from src.aegis_pod.live_structural_vectors import build_live_structural_vectors, stage_c_path_gate


ROOT = Path(__file__).resolve().parents[1]


class LiveStructuralVectorsTest(unittest.TestCase):
    def test_builds_structural_non_semantic_vectors_from_real_orion_copy_when_present(self) -> None:
        live_root = ROOT / "live-copies" / "CP-1004-ORION"
        batch_id = "orion-live-copy-20260721T002600Z"
        if not (live_root / batch_id).exists():
            self.skipTest("verified Orion live copy is not present in this workspace")

        report = build_live_structural_vectors(ROOT, batch_id)

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["working_parameters"]["semantic_embedding_used"])
        self.assertTrue(report["working_parameters"]["structural_non_semantic_vectors"])
        self.assertEqual(report["label_contract"]["embedding_kind"], "structural-non-semantic")
        self.assertEqual(report["source_counts"]["total_records"], 351)
        self.assertEqual(report["stage_c_live_readiness_path_gate"]["status"], "pass")
        for tensor in report["tensors"].values():
            self.assertEqual(tensor["vector_label"], "structural_vector")
            self.assertEqual(tensor["embedding_kind"], "structural-non-semantic")
            self.assertFalse(tensor["semantic_embedding"])
            self.assertFalse(tensor["committed_to_git"])
            self.assertEqual(tensor["shape"][1:], [8, 4])
            self.assertTrue(tensor["output_path"].startswith("live-copies/"))
        self.assertTrue(report["git_boundary"]["live_derived_tensor_artifacts_gitignored"])
        self.assertTrue(report["git_boundary"]["tensor_output_root"].startswith("live-copies/"))
        self.assertEqual(report["stage_c_live_readiness_path_gate"]["status"], "pass")

    def test_stage_c_path_gate_fails_closed_for_test_only_paths(self) -> None:
        report = {
            "tensors": {
                "PEER": {
                    "output_path": "fixtures/tensor-records/PEER.structural-vector-tensor.json",
                }
            }
        }

        gate = stage_c_path_gate(report)

        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["blocked_paths"], ["fixtures/tensor-records/PEER.structural-vector-tensor.json"])


if __name__ == "__main__":
    unittest.main()
