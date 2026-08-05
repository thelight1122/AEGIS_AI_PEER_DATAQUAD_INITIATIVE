from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from src.aegis_pod.stage_d_pod_staging import BATCH_ID, LEGACY_LEDGER_NAMES, stage_files
from src.aegis_pod.tensor_runtime import TENSOR_NAMES, load_jsonl


ROOT = Path(__file__).resolve().parents[1]


class StageDPodStagingTests(unittest.TestCase):
    def test_stage_root_must_be_gitignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            stage_root = root / "stage-d-out" / "CP-1004-ORION" / "pod"
            (root / ".gitignore").write_text("live-copies/\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stage-d-out"):
                stage_files(root, stage_root, root / "missing", BATCH_ID)

    def test_local_staging_preserves_records_tensors_ledgers_and_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shutil.copytree(ROOT / "live-copies", root / "live-copies")
            shutil.copytree(ROOT / "reports", root / "reports")
            shutil.copytree(ROOT / "fixtures", root / "fixtures")
            (root / ".gitignore").write_text("live-copies/\nstage-d-out/\n", encoding="utf-8")
            ledger_source = root / "live-copies" / "CP-1004-ORION" / BATCH_ID / "legacy-ledgers"
            if ledger_source.exists():
                shutil.rmtree(ledger_source)
            ledger_source.mkdir(parents=True)
            for ledger_name in LEGACY_LEDGER_NAMES:
                (ledger_source / f"{ledger_name}.jsonl").write_text(
                    f'{{"ledger":"{ledger_name}","source":"unit-test"}}\n',
                    encoding="utf-8",
                )

            report = stage_files(root, root / "stage-d-out" / "CP-1004-ORION" / "pod", ledger_source, BATCH_ID)

            self.assertEqual(report["status"], "pass")
            self.assertFalse(report["working_parameters"]["remote_write"])
            self.assertTrue(report["git_boundary"]["stage_d_out_gitignored"])
            self.assertEqual(set(report["records"]), set(TENSOR_NAMES))
            self.assertEqual(report["records"]["PEER"]["record_count"], 106)
            self.assertEqual(report["tensors"]["PEER"]["expected_sha256"], report["tensors"]["PEER"]["sha256"])
            self.assertEqual(set(report["legacy_ledgers"]), set(LEGACY_LEDGER_NAMES))
            self.assertEqual(set(report["pod_manifest"]["roles"]["steward"]["reads"]), set(TENSOR_NAMES))
            self.assertEqual(set(report["pod_manifest"]["roles"]["advocate"]["reads"]), set(TENSOR_NAMES))
            staged_peer = root / report["records"]["PEER"]["path"]
            self.assertEqual(len(load_jsonl(staged_peer)), 106)


if __name__ == "__main__":
    unittest.main()
