"""Behavior-oriented contracts for the reduced Windows validation workflow."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RemoteWindowsTaskContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = (
            ROOT / ".github/workflows/remote-windows-task.yml"
        ).read_text(encoding="utf-8")
        cls.windows_build = (
            ROOT / ".github/workflows/windows-build.yml"
        ).read_text(encoding="utf-8")
        cls.run_checks = (
            ROOT / "tools/winui/run_checks.py"
        ).read_text(encoding="utf-8")
        cls.profile = (
            ROOT / "docs/development/VERIFICATION_PROFILE.md"
        ).read_text(encoding="utf-8")

    def test_one_reusable_execution_workflow_and_read_only_token(self):
        self.assertIn("workflow_call:", self.workflow)
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("\n  push:", self.workflow)
        self.assertIn("actions: read", self.workflow)
        self.assertIn("contents: read", self.workflow)
        self.assertNotIn("actions: write", self.workflow)
        self.assertNotIn("contents: write", self.workflow)
        for obsolete in (
            "FLYEXPLORER_ROUTINE_OBSERVATION_SECONDS",
            "FLYEXPLORER_ACTIVE_MONITOR_SECONDS",
            "FLYEXPLORER_RESULT_DEPENDENT_MAX_WAIT_SECONDS",
            "FLYEXPLORER_REMOTE_RUNNER_CAPACITY",
            "FLYEXPLORER_DEFAULT_VALIDATION_RUN_BUDGET",
            "FLYEXPLORER_REMOTE_EVIDENCE_DIR",
        ):
            self.assertNotIn(obsolete, self.workflow)

    def test_request_model_is_small_diagnostic_or_validation(self):
        for token in (
            "REMOTE_REQUEST_MODE",
            "REMOTE_VALIDATION_PLAN",
            "REMOTE_CANDIDATE_SHA",
            "REMOTE_LOGICAL_UNIT",
        ):
            self.assertIn(token, self.workflow)
        self.assertIn('requestMode -notin @("diagnostic", "validation")', self.workflow)
        self.assertIn("Diagnostic requests must use configuration none.", self.workflow)
        self.assertIn("Validation requests must declare validation_plan.", self.workflow)
        for removed in (
            "REMOTE_VALIDATION_FINGERPRINT",
            "REMOTE_RETRY_SCOPE",
            "REMOTE_REUSE_RUN_ID",
            "REMOTE_REUSED_TARGETS",
            "FOCUSED_REUSE_DIFF",
            "remote_evidence_policy.py",
            "GH_EVIDENCE_TOKEN",
        ):
            self.assertNotIn(removed, self.workflow)

    def test_stale_main_is_fail_closed_only_for_validation(self):
        self.assertIn('if ($requestMode -eq "validation")', self.workflow)
        self.assertIn("Stale validation request:", self.workflow)
        self.assertIn("DIAGNOSTIC_STALE_MAIN=ADVISORY", self.workflow)

    def test_static_preflight_delegates_to_change_scoped_fast_runner(self):
        preflight = self.workflow.index("- name: Static candidate preflight")
        command = self.workflow.index("- name: Run remote shell command")
        block = self.workflow[preflight:command]
        self.assertIn("git worktree add --detach", block)
        self.assertIn("run_checks.py", block)
        self.assertIn(" fast --before ", block)
        self.assertNotIn("$infraChanged", block)
        self.assertNotIn("$harnessChanged", block)
        self.assertLess(preflight, command)

    def test_gui_validation_has_explicit_runner_health_gate(self):
        self.assertIn("REMOTE_NEEDS_GUI_HEALTH", self.workflow)
        self.assertIn("- name: Runner health for GUI validation", self.workflow)
        self.assertIn("runner_health.py", self.workflow)

    def test_classifier_fallback_and_result_writer_are_bounded(self):
        self.assertIn("classify_remote_failure.py", self.workflow)
        self.assertIn("REMOTE_OBSERVED_MAIN_SHA", self.workflow)
        self.assertIn("refs/remotes/origin/main", self.workflow)
        self.assertIn("RESULT_CLASSIFIER_FALLBACK=current-main", self.workflow)
        self.assertIn("COMMAND_FAILURE_UNCLASSIFIED", self.workflow)
        self.assertEqual(
            1, self.workflow.count("- name: Write structured remote result")
        )
        self.assertEqual(1, self.workflow.count("- name: Upload remote evidence"))
        self.assertEqual(1, self.workflow.count("REMOTE_RESULT="))

    def test_structured_result_separates_request_static_health_and_command(self):
        for stage in (
            "REQUEST_VALIDATION",
            "STATIC_PREFLIGHT",
            "RUNNER_HEALTH",
            "COMMAND",
        ):
            self.assertIn(stage, self.workflow)
        self.assertNotIn("EVIDENCE_POLICY", self.workflow)
        for category in (
            "REQUEST_SCHEMA_FAILURE",
            "HELPER_STATIC_FAILURE",
            "RUNNER_HEALTH_FAILURE",
        ):
            self.assertIn(category, self.workflow)

    def test_command_failure_keeps_machine_readable_evidence(self):
        for token in (
            "remote-command.log",
            "remote-command-error.txt",
            "Start-Transcript",
            "Stop-Transcript",
            "remote-result.json",
        ):
            self.assertIn(token, self.workflow)

    def test_fast_runner_and_full_cost_are_distinct(self):
        self.assertIn('"fast"', self.run_checks)
        self.assertIn("affected_areas", self.run_checks)
        self.assertIn("FAST_CHECKS_COMPLETE=PASS", self.run_checks)
        self.assertIn("configurations = [\"Release\"]", self.run_checks)
        self.assertIn("--include-debug", self.run_checks)
        self.assertIn("targeted GUI", self.run_checks)

    def test_windows_build_remains_manual_only(self):
        self.assertIn("on:\n  workflow_dispatch:", self.windows_build)
        self.assertNotIn("\n  push:", self.windows_build)
        self.assertIn('default: "release"', self.windows_build)

    def test_high_cost_fixture_policy_stays_outside_general_remote_workflow(self):
        self.assertIn("8,000 files", self.profile)
        self.assertIn("20,000-entry", self.profile)
        self.assertNotIn("8,000", self.workflow)
        self.assertNotIn("20,000", self.workflow)


if __name__ == "__main__":
    unittest.main()
