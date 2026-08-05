from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest

from src.aegis_pod.orb_runtime import (
    load_json,
    run_fixture_attachment,
    run_rls_demonstration,
    validate_attachment,
)


ROOT = Path(__file__).resolve().parents[1]


class OrbRuntimeTest(unittest.TestCase):
    def test_validates_pod_orb_umbilical_attachment(self) -> None:
        pod = load_json(ROOT / "fixtures" / "local-cyberpeer-pod.json")
        orb = load_json(ROOT / "fixtures" / "rls-orb.json")
        umbilical = load_json(ROOT / "fixtures" / "rls-orb-umbilical.json")

        attachment = validate_attachment(ROOT, pod, orb, umbilical)

        self.assertEqual(attachment.pod_id, "local-cyberpeer-pod-fixture")
        self.assertEqual(attachment.orb_id, "rls-orb-fixture")
        self.assertEqual(attachment.umbilical_id, "rls-orb-fixture-umbilical")
        self.assertEqual(attachment.attachment_point, "processor")

    def test_demonstration_returns_visible_function_outputs(self) -> None:
        pod = load_json(ROOT / "fixtures" / "local-cyberpeer-pod.json")
        orb = load_json(ROOT / "fixtures" / "rls-orb.json")
        umbilical = load_json(ROOT / "fixtures" / "rls-orb-umbilical.json")
        attachment = validate_attachment(ROOT, pod, orb, umbilical)
        input_data = load_json(ROOT / "fixtures" / "rls-orb-input.json")

        result = run_rls_demonstration(ROOT, attachment, input_data)

        self.assertEqual(result["observable_events"], ["attached", "invoked", "completed"])
        self.assertIn("reflection_summary", result)
        self.assertIn("integration_signals", result)
        self.assertTrue(result["integration_signals"]["all_requested_tensors_available"])
        self.assertFalse(result["integration_signals"]["live_reach"])

    def test_fixture_attachment_writes_orb_reports(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "workspace"
            shutil.copytree(ROOT, temp_root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))

            health = run_fixture_attachment(temp_root)

            self.assertFalse(health["live_reach"])
            self.assertEqual(len(health["attachments"]), 1)
            output_path = temp_root / health["attachments"][0]["output_path"]
            self.assertTrue(output_path.exists())
            output = load_json(output_path)
            self.assertEqual(output["orb_id"], "rls-orb-fixture")


if __name__ == "__main__":
    unittest.main()
