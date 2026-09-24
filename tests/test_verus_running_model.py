import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from aegis_verus_lab.running_model import (
    CONFIGURED_EVIDENCE,
    RECENT_EVIDENCE,
    SESSION_EVIDENCE,
    model_from_transcript,
    resolve_running_model,
)


def entry(kind, model=None):
    value = {"type": kind, "message": {"role": kind}}
    if model is not None:
        value["message"]["model"] = model
    return json.dumps(value)


class RunningModelTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "project-a").mkdir()
        (self.root / "project-b").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def transcript(self, project, session, lines, age=0.0):
        path = self.root / project / f"{session}.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        stamp = time.time() - age
        os.utime(path, (stamp, stamp))
        return path

    def test_the_newest_assistant_entry_names_the_model(self):
        path = self.transcript("project-a", "s1", [
            entry("assistant", "claude-opus-4-8"),
            entry("user"),
            entry("assistant", "claude-opus-5-5"),
            json.dumps({"type": "mode"}),
        ])
        self.assertEqual(model_from_transcript(path), "claude-opus-5-5")

    def test_synthetic_entries_are_not_a_model(self):
        path = self.transcript("project-a", "s1", [
            entry("assistant", "claude-opus-5-5"),
            entry("assistant", "<synthetic>"),
        ])
        self.assertEqual(model_from_transcript(path), "claude-opus-5-5")

    def test_a_named_session_wins_and_says_so(self):
        self.transcript("project-a", "caller", [entry("assistant", "claude-opus-5-5")], age=30)
        self.transcript("project-b", "other", [entry("assistant", "claude-sonnet-5")])
        self.assertEqual(
            resolve_running_model("claude-opus-4-8", frontier_session_id="caller", projects_root=self.root),
            ("claude-opus-5-5", SESSION_EVIDENCE))

    def test_without_a_session_the_freshest_transcript_is_used(self):
        self.transcript("project-a", "old", [entry("assistant", "claude-sonnet-5")], age=60)
        self.transcript("project-b", "now", [entry("assistant", "claude-opus-5-5")])
        self.assertEqual(
            resolve_running_model("claude-opus-4-8", projects_root=self.root),
            ("claude-opus-5-5", RECENT_EVIDENCE))

    def test_a_stale_transcript_falls_back_to_the_setting_labelled_as_such(self):
        self.transcript("project-a", "old", [entry("assistant", "claude-opus-5-5")], age=600)
        self.assertEqual(
            resolve_running_model("claude-opus-4-8", projects_root=self.root),
            ("claude-opus-4-8", CONFIGURED_EVIDENCE))

    def test_subagent_transcripts_are_not_the_session(self):
        (self.root / "project-a" / "s1" / "subagents").mkdir(parents=True)
        (self.root / "project-a" / "s1" / "subagents" / "agent.jsonl").write_text(
            entry("assistant", "claude-haiku-4-5") + "\n", encoding="utf-8")
        self.transcript("project-a", "s1", [entry("assistant", "claude-opus-5-5")], age=5)
        self.assertEqual(resolve_running_model(None, projects_root=self.root)[0], "claude-opus-5-5")

    def test_a_session_id_cannot_walk_out_of_the_projects_folder(self):
        self.transcript("project-a", "s1", [entry("assistant", "claude-opus-5-5")], age=600)
        self.assertEqual(
            resolve_running_model("claude-opus-4-8", frontier_session_id="../project-a/s1", projects_root=self.root),
            ("claude-opus-4-8", CONFIGURED_EVIDENCE))

    def test_nothing_known_is_an_error_not_a_guess(self):
        with self.assertRaises(ValueError):
            resolve_running_model(None, projects_root=self.root / "missing")


if __name__ == "__main__":
    unittest.main()
