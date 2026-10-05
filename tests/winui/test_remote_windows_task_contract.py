"""Behavior-oriented contracts for Windows workflow orchestration."""
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

    def test_control_branch_and_manual_dispatch_share_one_execution_workflow(self):
        self.assertIn("workflow_call:", self.workflow)
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertIn("request_ref:", self.workflow)
        self.assertIn("request_branch:", self.workflow)
        self.assertNotIn("\n  push:", self.workflow)
        self.assertIn("Invoke-Expression $env:REMOTE_COMMAND", self.workflow)

    def test_request_model_separates_diagnostic_from_validation(self):
        self.assertIn("REMOTE_REQUEST_MODE", self.workflow)
        self.assertIn("REMOTE_VALIDATION_PLAN", self.workflow)
        self.assertIn('requestMode -notin @("diagnostic", "validation")', self.workflow)
        self.assertIn("Diagnostic requests must use configuration none.", self.workflow)
        self.assertIn("Validation requests must declare validation_plan.", self.workflow)

    def test_command_is_not_regex_inferred_back_into_validation_metadata(self):
        self.assertNotIn("$detectedStages", self.workflow)
        self.assertNotIn("$stageStatements", self.workflow)
        self.assertNotIn("command appears to run", self.workflow)
        self.assertNotIn("Duplicate validation fingerprint", self.workflow)
        self.assertNotIn("retry_revision", self.workflow)

    def test_validation_fingerprint_distinguishes_real_targets_and_harness(self):
        for token in (
            "$candidateSha",
            "$configuration",
            "$logicalUnit",
            "$uniquePlan",
            "$commandHash",
            "$harnessRevision",
        ):
            self.assertIn(token, self.workflow)
        self.assertIn("SHA256", self.workflow)
        self.assertIn("REMOTE_VALIDATION_FINGERPRINT", self.workflow)

    def test_stale_main_is_fail_closed_only_for_validation(self):
        self.assertIn(
            'if ($requestMode -eq "validation")',
            self.workflow,
        )
        self.assertIn("Stale validation request:", self.workflow)
        self.assertIn("DIAGNOSTIC_STALE_MAIN=ADVISORY", self.workflow)

    def test_static_preflight_is_change_scoped_and_covers_all_gui_harnesses(self):
        self.assertIn("$changedPaths", self.workflow)
        self.assertIn("check_python_static.py", self.workflow)
        self.assertIn("$infraChanged", self.workflow)
        self.assertIn("$harnessChanged", self.workflow)
        self.assertIn("'tests/winui/uia_polling.py'", self.workflow)
        self.assertIn("'tests/winui/test_*gui.py'", self.workflow)
        self.assertIn("git -C $temp diff --check", self.workflow)
        self.assertNotIn(r"tests\winui\${D}name", self.workflow)
        self.assertIn(r'tests\winui\$name', self.workflow)
        self.assertLess(
            self.workflow.index("- name: Static candidate preflight"),
            self.workflow.index("- name: Run remote shell command"),
        )

    def test_diagnostic_preflight_is_not_misreported_as_pass(self):
        self.assertIn(
            "inputs.request_ref != '' && env.REMOTE_REQUEST_MODE == 'validation'",
            self.workflow,
        )
        self.assertNotIn("STATIC_PREFLIGHT=SKIPPED_DIAGNOSTIC", self.workflow)
        self.assertIn("$validationPlan = @()", self.workflow)
        self.assertIn("validation_plan = $validationPlan", self.workflow)

    def test_gui_validation_has_explicit_runner_health_gate(self):
        self.assertIn("REMOTE_NEEDS_GUI_HEALTH", self.workflow)
        self.assertIn("- name: Runner health for GUI validation", self.workflow)
        self.assertIn("runner_health.py", self.workflow)
        self.assertIn(
            "env.REMOTE_NEEDS_GUI_HEALTH == 'true'",
            self.workflow,
        )
        self.assertLess(
            self.workflow.index("- name: Runner health for GUI validation"),
            self.workflow.index("- name: Run remote shell command"),
        )

    def test_workflow_does_not_blanket_block_same_revision_reruns(self):
        self.assertNotIn(
            "if: ${{ github.run_attempt == '1' }}",
            self.workflow,
        )
        self.assertNotIn(
            "if: ${{ github.run_attempt == '1' }}",
            self.windows_build,
        )

    def test_command_failure_keeps_machine_readable_evidence(self):
        self.assertIn("remote-command.log", self.workflow)
        self.assertIn("remote-command-error.txt", self.workflow)
        self.assertIn("Start-Transcript", self.workflow)
        self.assertIn("Stop-Transcript", self.workflow)
        self.assertIn("FAILURE_CATEGORY=([A-Z0-9_]+)", self.workflow)

    def test_structured_result_distinguishes_failure_layers(self):
        for stage in (
            "REQUEST_VALIDATION",
            "STATIC_PREFLIGHT",
            "RUNNER_HEALTH",
            "COMMAND",
        ):
            self.assertIn(stage, self.workflow)
        for category in (
            "REQUEST_SCHEMA_FAILURE",
            "HELPER_STATIC_FAILURE",
            "RUNNER_HEALTH_FAILURE",
            "PRODUCT_BUILD_FAILURE",
            "HARNESS_PROGRAMMING_FAILURE",
            "AUTOMATION_API_FAILURE",
            "AUTOMATION_DISCOVERY_FAILURE",
            "AUTOMATION_TIMEOUT_FAILURE",
            "TEST_ASSERTION_FAILURE",
            "COMMAND_FAILURE_UNCLASSIFIED",
        ):
            self.assertIn(category, self.workflow)
        self.assertIn('"skipped" { return "NOT_RUN" }', self.workflow)

    def test_scoped_runner_emits_failure_categories(self):
        for category in (
            "STRUCTURE_CONTRACT_FAILURE",
            "PRODUCT_SOURCE_CONTRACT_FAILURE",
            "HARNESS_CONTRACT_FAILURE",
            "INFRA_POLICY_CONTRACT_FAILURE",
            "HARNESS_DEPENDENCY_FAILURE",
            "PRODUCT_BUILD_FAILURE",
            "GUI_ACCEPTANCE_FAILURE",
        ):
            self.assertIn(f'"{category}"', self.run_checks)

    def test_windows_build_remains_manual_only(self):
        self.assertIn("on:\n  workflow_dispatch:", self.windows_build)
        self.assertNotIn("\n  push:", self.windows_build)
        self.assertIn('default: "release"', self.windows_build)

    def test_high_cost_fixture_policy_remains_outside_general_workflow(self):
        self.assertIn("8,000 files", self.profile)
        self.assertIn("20,000-entry", self.profile)
        self.assertNotIn("8,000", self.workflow)
        self.assertNotIn("20,000", self.workflow)


if __name__ == "__main__":
    unittest.main()
