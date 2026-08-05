from pathlib import Path
from dataclasses import replace
from tempfile import TemporaryDirectory
import unittest

from src.aegis_pod.tensor_runtime import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_METADATA_DIMENSION,
    compute_tensor,
    duplicate_record_ids,
    load_jsonl,
    parse_record,
    run_fixture_build,
)


ROOT = Path(__file__).resolve().parents[1]


class TensorRuntimeTest(unittest.TestCase):
    def test_computes_tensor_from_source_records(self) -> None:
        raw = load_jsonl(ROOT / "fixtures" / "tensor-records" / "PEER.jsonl")
        records = [parse_record(item, "PEER") for item in raw]

        tensor = compute_tensor(records, "PEER")

        self.assertEqual(tensor["shape"], [2, DEFAULT_EMBEDDING_DIMENSION, DEFAULT_METADATA_DIMENSION])
        self.assertEqual(tensor["pod_id"], "local-cyberpeer-pod-fixture")
        self.assertEqual(tensor["tensor_spec_id"], "dataquadpod-core-tensor-spec-0.1.0")
        self.assertEqual(tensor["dtype"], "float32")
        self.assertEqual(tensor["axis_order"], ["record", "embedding", "metadata"])
        self.assertEqual([axis["name"] for axis in tensor["axis_definitions"]], ["record", "embedding", "metadata"])
        self.assertEqual(
            [slot["name"] for slot in tensor["metadata_slots"]],
            ["embedding_value", "body_length_signal", "timestamp_position_signal", "verification_signal"],
        )
        self.assertEqual(len(tensor["values"]), 2)
        self.assertEqual(len(tensor["values"][0]), DEFAULT_EMBEDDING_DIMENSION)
        self.assertEqual(len(tensor["values"][0][0]), DEFAULT_METADATA_DIMENSION)
        self.assertEqual(tensor["record_index"][0]["record_id"], "fixture-peer-0001")
        self.assertEqual(tensor["record_index"][0]["source_record_id"], "source-peer-0001")
        self.assertEqual(tensor["record_index"][0]["source_hash_scope"], "normalized_source_record")
        self.assertEqual(tensor["record_index"][0]["copy_batch_id"], "fixture-copy-batch-0001")
        self.assertEqual(tensor["values"][0][0], [0.92549, 0.068, 0.17, 0.0])
        self.assertEqual(tensor["values"][1][0], [0.564706, 0.079, 0.644, 0.0])

    def test_source_hash_changes_numeric_output(self) -> None:
        raw = load_jsonl(ROOT / "fixtures" / "tensor-records" / "PEER.jsonl")
        record = parse_record(raw[0], "PEER")
        changed = replace(record, source_hash="changed-source-hash")

        original_tensor = compute_tensor([record], "PEER")
        changed_tensor = compute_tensor([changed], "PEER")

        self.assertNotEqual(original_tensor["values"], changed_tensor["values"])

    def test_duplicate_record_ids_are_visible(self) -> None:
        raw = load_jsonl(ROOT / "fixtures" / "tensor-records" / "PCT.jsonl")
        record = parse_record(raw[0], "PCT")

        self.assertEqual(duplicate_record_ids([record, record]), ["fixture-pct-0001"])

    def test_fixture_build_writes_all_tensor_outputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir) / "tensors"
            health = run_fixture_build(ROOT, output_root=output_root)

            self.assertFalse(health["live_reach"])
            self.assertEqual(set(health["tensors"]), {"PEER", "PCT", "NCT", "SPINE"})
            for tensor_name, info in health["tensors"].items():
                output_path = ROOT / info["output_path"] if not Path(info["output_path"]).is_absolute() else Path(info["output_path"])
                if not output_path.exists():
                    output_path = output_root / f"{tensor_name}.tensor.json"
                self.assertTrue(output_path.exists(), tensor_name)
                self.assertEqual(info["shape"][1:], [DEFAULT_EMBEDDING_DIMENSION, DEFAULT_METADATA_DIMENSION])


if __name__ == "__main__":
    unittest.main()
