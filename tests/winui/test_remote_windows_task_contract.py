"""Regression guard: retired VM workflows must not silently return."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "docs/operations/windows-runner-retirement.md"
MANIFEST = ROOT / "docs/operations/windows-runner-retirement-manifest.json"


class RetiredRunnerRoutingContract(unittest.TestCase):
    def test_retired_source_runner_workflows_are_absent(self):
        for filename in ("windows-build.yml", "remote-windows-task.yml"):
            with self.subTest(filename=filename):
                self.assertFalse((ROOT / ".github/workflows" / filename).exists())

    def test_central_request_route_is_explicit_and_manual(self):
        guidance = ARCHIVE.read_text(encoding="utf-8")
        self.assertIn("tngkrwlsmd/personal-control-plane", guidance)
        self.assertIn("central-flyexplorer-ci.yml", guidance)
        self.assertIn("project_id=desktop-a", guidance)
        self.assertIn("commit_sha=<40-character-main-SHA>", guidance)
        self.assertIn("scope=release", guidance)
        self.assertIn("No exact equivalent", guidance)
        self.assertIn("GUI worker needs an unlocked logged-in Windows desktop", guidance)

    def test_runner_archive_is_metadata_only(self):
        archive = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(1, archive["schema_version"])
        self.assertTrue(archive["old_runner"]["folder_preserved"])
        self.assertEqual("evidence/remote-windows",
                         archive["preserved_git_evidence"]["branch"])
        self.assertFalse(archive["old_runner"]["registered"])
        for checkout in archive["checkouts"]:
            self.assertEqual(0, checkout["tracked_changes"])
        self.assertNotIn("credentials", json.dumps(archive).lower().replace(
            "runner identity/credentials/tokens", ""))


if __name__ == "__main__":
    unittest.main()
