"""Regression tests for Remote Windows Task failure classification."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "winui" / "classify_remote_failure.py"
spec = importlib.util.spec_from_file_location("classify_remote_failure", MODULE_PATH)
assert spec is not None and spec.loader is not None
classifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classifier)


class RemoteFailureClassifierTests(unittest.TestCase):
    def test_explicit_category_wins_and_legacy_runtime_alias_is_normalized(self):
        self.assertEqual(
            "HARNESS_CONTRACT_FAILURE",
            classifier.classify(
                "subprocess.TimeoutExpired\nFAILURE_CATEGORY=HARNESS_CONTRACT_FAILURE"
            ),
        )
        self.assertEqual(
            "RUNTIME_REUSE_MISMATCH",
            classifier.classify("FAILURE_CATEGORY=REUSED_RUNTIME_MISMATCH"),
        )

    def test_installed_shutdown_timeout_is_not_unclassified(self):
        text = """
Traceback (most recent call last):
  File "tests/winui/test_installed_lifecycle.py", line 1, in launch_installed
subprocess.TimeoutExpired: Command ['C:\\owned\\flyExplorer.exe'] timed out after 16 seconds
AssertionError: owned installed app did not close within the accepted 16-second budget
"""
        self.assertEqual("INSTALLED_APP_SHUTDOWN_TIMEOUT", classifier.classify(text))

    def test_workflow_permission_and_powershell_failures_are_distinct(self):
        self.assertEqual(
            "WORKFLOW_DEFINITION_FAILURE",
            classifier.classify("Invalid workflow file; jobs=[]"),
        )
        self.assertEqual(
            "REPOSITORY_PERMISSION_FAILURE",
            classifier.classify("remote: Permission to owner/repo denied"),
        )
        self.assertEqual(
            "POWERSHELL_COMPATIBILITY_FAILURE",
            classifier.classify(
                "[System.IO.Path] does not contain a method named 'GetRelativePath'.\n"
                "FullyQualifiedErrorId : MethodNotFound"
            ),
        )

    def test_runtime_identity_mismatch_is_distinct(self):
        self.assertEqual(
            "RUNTIME_REUSE_MISMATCH",
            classifier.classify("expected digest: abc\nactual digest: def"),
        )

    def test_generic_subprocess_timeout_has_its_own_category(self):
        self.assertEqual(
            "SUBPROCESS_TIMEOUT_FAILURE",
            classifier.classify(
                "subprocess.TimeoutExpired: Command ['tool.exe'] timed out after 10 seconds"
            ),
        )

    def test_unknown_command_failure_remains_explicitly_unclassified(self):
        self.assertEqual(
            "COMMAND_FAILURE_UNCLASSIFIED",
            classifier.classify("mysterious native failure"),
        )


if __name__ == "__main__":
    unittest.main()
