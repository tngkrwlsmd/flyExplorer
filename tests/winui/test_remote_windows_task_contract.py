from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RemoteWindowsTaskContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = (
            ROOT / ".github/workflows/remote-windows-task.yml"
        ).read_text(encoding="utf-8")
        cls.agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        cls.efficiency = (
            ROOT / "docs/development/AGENT_EFFICIENCY.md"
        ).read_text(encoding="utf-8")
        cls.project = (
            ROOT / ".agent-policy/PROJECT.md"
        ).read_text(encoding="utf-8")
        cls.windows_build = (
            ROOT / ".github/workflows/windows-build.yml"
        ).read_text(encoding="utf-8")

    def test_dispatch_shell_requires_no_task_commit(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertIn("command:", self.workflow)
        self.assertIn("working_directory:", self.workflow)
        self.assertIn("default: 'C:\\dev\\flyExplorer'", self.workflow)
        self.assertIn(
            "if: github.event_name == 'workflow_dispatch'",
            self.workflow,
        )
        self.assertIn("Invoke-Expression $env:REMOTE_COMMAND", self.workflow)
        self.assertIn("Set-Location -LiteralPath $workdir", self.workflow)

    def test_request_slot_uses_dedicated_control_branch(self):
        self.assertIn("- 'control/remote-shell'", self.workflow)
        self.assertIn("- 'requests/remote-shell/request.json'", self.workflow)
        self.assertIn(
            "github.ref_name == 'control/remote-shell'",
            self.workflow,
        )
        self.assertIn('"requests\\remote-shell\\request.json"', self.workflow)
        self.assertIn("Remote shell request_id is required.", self.workflow)
        self.assertIn("Get-Content -Raw -Encoding UTF8", self.workflow)
        self.assertIn("expected_main_sha", self.workflow)
        self.assertIn("git fetch origin main --no-tags --prune", self.workflow)
        self.assertIn("Stale remote shell request:", self.workflow)
        self.assertIn("REMOTE_EXPECTED_MAIN_SHA", self.workflow)
        self.assertIn("REMOTE_OBSERVED_MAIN_SHA", self.workflow)
        self.assertIn("REMOTE_SOURCE=control/remote-shell", self.workflow)

    def test_request_slot_requires_machine_checkable_validation_metadata(self):
        for token in (
            "candidate_sha",
            "logical_unit",
            "configuration",
            "validation_kind",
            "invalidated_evidence",
            "retry_reason",
            "retry_revision",
            "REMOTE_VALIDATION_FINGERPRINT",
        ):
            self.assertIn(token, self.workflow)
        self.assertIn("validation_kind must be a JSON array", self.workflow)
        self.assertIn(
            "command appears to run '$stage' validation",
            self.workflow,
        )
        self.assertIn(
            "git log --format=%H -- requests/remote-shell/request.json",
            self.workflow,
        )
        self.assertIn("Duplicate validation fingerprint", self.workflow)
        self.assertIn(
            "retry_reason/retry_revision are only valid",
            self.workflow,
        )

    def test_windows_workflows_skip_github_rerun_attempts(self):
        self.assertIn(
            "task:\n    if: ${{ github.run_attempt == '1' }}",
            self.workflow,
        )
        self.assertIn(
            "windows-vm:\n    if: ${{ github.run_attempt == '1' }}",
            self.windows_build,
        )

    def test_validation_churn_targets_are_documented(self):
        for text in (self.agents, self.efficiency, self.project):
            normalized = " ".join(text.split())
            self.assertIn("30-50", normalized)
            self.assertIn("validation fingerprint", normalized)
            self.assertIn("retry_revision", normalized)
        self.assertIn("<=2 validation runs per logical unit", " ".join(self.project.split()))

    def test_dispatch_path_does_not_require_checkout(self):
        self.assertIn(
            "- name: Checkout control branch request\n"
            "        if: github.event_name == 'push'",
            self.workflow,
        )
        self.assertIn(
            "- name: Resolve dispatched shell inputs\n"
            "        if: github.event_name == 'workflow_dispatch'",
            self.workflow,
        )
        self.assertIn(
            "github.event_name == 'workflow_dispatch' || "
            "github.ref_name == 'control/remote-shell'",
            self.workflow,
        )

    def test_remote_shell_is_the_only_push_based_command_channel(self):
        self.assertNotIn("remote/**", self.workflow)
        self.assertNotIn("remote-task.ps1", self.workflow)
        self.assertNotIn("Run committed remote task", self.workflow)
        agents = " ".join(self.agents.split())
        self.assertIn("minimal control-plane tree", agents)
        self.assertIn("Do not create `remote/**` task branches", agents)

    def test_long_run_guidance_allows_up_to_three_minutes_without_polling(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        self.assertIn("up to three minutes", agents)
        self.assertIn("up to three minutes", efficiency)
        self.assertIn("up to three minutes", project)
        self.assertIn("one final/blocking read", efficiency)

    def test_guidance_prefers_request_slot_and_keeps_rdc_auxiliary(self):
        self.assertIn(
            "`control/remote-shell` request slot",
            self.agents,
        )
        self.assertIn("RDC or another desktop-control path is a supplementary tool", self.agents)
        self.assertIn(
            "`control/remote-shell` request slot",
            self.efficiency,
        )
        self.assertIn("RDC/desktop-control is supplementary", self.efficiency)

    def test_resume_protocol_blocks_stale_rework_and_fixture_loops(self):
        for text in (self.agents, self.efficiency):
            normalized = " ".join(text.split())
            self.assertIn("latest main", normalized)
            self.assertIn("recent commits", normalized)
            self.assertIn("recent main CI", normalized)
            self.assertIn("expected_main_sha", normalized)
        efficiency = " ".join(self.efficiency.split())
        self.assertIn("Zero same-revision Actions retries", efficiency)
        self.assertIn("Do not retry a completed GitHub Actions run", efficiency)
        self.assertIn("already on main", self.agents)
        project_normalized = " ".join(self.project.split())
        self.assertIn("already merged and accepted", project_normalized)
        self.assertIn("persistent remote-shell checkout", project_normalized)

    def test_guidance_makes_windows_build_dispatch_only_and_non_retrying(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        self.assertIn("Same-revision Actions reruns are prohibited", agents)
        self.assertIn("manual-only build/acceptance gate", agents)
        self.assertIn("Normal main pushes must not start it", agents)
        self.assertIn("Never press rerun", agents)
        self.assertIn("do not rerun a failed job or workflow on that same SHA", efficiency)
        self.assertIn("Windows VM Build is dispatch-only", efficiency)
        self.assertIn("policy readiness/preflight check", efficiency)

    def test_windows_build_has_no_push_trigger(self):
        self.assertIn("on:\n  workflow_dispatch:", self.windows_build)
        self.assertNotIn("\n  push:", self.windows_build)
        self.assertIn('default: "release"', self.windows_build)
        self.assertNotIn("REQUESTED_VALIDATION_SCOPE", self.windows_build)
        self.assertNotIn("Resolve validation scope", self.windows_build)


if __name__ == "__main__":
    unittest.main()
