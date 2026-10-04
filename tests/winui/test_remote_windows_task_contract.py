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
        self.assertIn("$invalidatedEvidence.psobject.Properties |", self.workflow)
        self.assertIn("Where-Object { -not [string]::IsNullOrWhiteSpace($_) }", self.workflow)
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

    def test_long_run_guidance_defaults_to_three_minute_floor_with_explicit_monitoring_override(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("no earlier than three minutes", normalized)
            self.assertIn("30 seconds", normalized)
        self.assertIn("one final/blocking read", efficiency)
        self.assertIn("scheduled/automation", agents)
        self.assertIn("scheduled/automation", project)

    def test_pre_dispatch_lease_blocks_overlapping_remote_runs(self):
        texts = (
            " ".join(self.agents.split()),
            " ".join(self.efficiency.split()),
            " ".join(self.project.split()),
        )
        for normalized in texts:
            self.assertIn("before writing `requests/remote-shell/request.json`", normalized)
            self.assertIn("`queued`", normalized)
            self.assertIn("`pending`", normalized)
            self.assertIn("`in_progress`", normalized)
            self.assertIn("do not", normalized)
        self.assertIn("pre-dispatch", texts[0].lower())
        self.assertIn("pre-dispatch", texts[1].lower())
        self.assertIn("pre-dispatch", texts[2].lower())

    def test_remote_run_budget_stops_speculative_successors(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("one primary Windows validation run", normalized)
            self.assertIn("third Windows validation run", normalized)
            self.assertIn("explicit user approval", normalized)
        self.assertIn("Never queue a speculative successor", agents)
        self.assertIn("never queue a successor while its predecessor is active", efficiency)
        self.assertIn("Never queue speculative successors", project)

    def test_three_minute_rule_is_default_only_and_explicit_monitoring_is_bounded(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("no earlier than three minutes", normalized)
            self.assertIn("explicitly", normalized)
            self.assertIn("30 seconds", normalized)
        self.assertIn("anti-polling", agents)
        self.assertIn("anti-polling", efficiency)

    def test_expensive_large_folder_fixtures_are_final_acceptance_only(self):
        for text in (self.agents, self.efficiency, self.project):
            normalized = " ".join(text.split())
            self.assertIn("8,000+", normalized)
            self.assertIn("20,000+", normalized)
            self.assertIn("final acceptance", normalized)

    def test_guidance_prefers_request_slot_and_keeps_rdc_auxiliary(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        self.assertIn("`control/remote-shell` request slot", agents)
        self.assertIn("RDC or another desktop-control path is a supplementary tool", agents)
        self.assertIn("`control/remote-shell` request slot", efficiency)
        self.assertIn("RDC/desktop-control is supplementary", efficiency)

    def test_guidance_requires_request_metadata_preflight_before_push(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("preflight", normalized.lower())
            self.assertIn('configuration', normalized)
            self.assertIn('Debug', normalized)
            self.assertIn('Release', normalized)
            self.assertIn('invalidated_evidence', normalized)
        self.assertIn('validation_kind == ["none"]', agents)
        self.assertIn("before the control-branch commit", efficiency)
        self.assertIn("agent preflight defect", project.lower())

    def test_zero_run_preflight_blocks_avoidable_workflow_failures(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("zero-run preflight", normalized.lower())
            self.assertIn("preflight defect", normalized.lower())
            self.assertIn("branch", normalized.lower())
            self.assertIn("path", normalized.lower())
            self.assertIn("import", normalized.lower())
            self.assertIn("UIA", normalized)
        self.assertIn("do not create a workflow run", agents.lower())
        self.assertIn("PowerShell/JSON", agents)
        self.assertIn("syntax/import-path sanity", efficiency)
        self.assertIn("nonexistent branches", project)
        self.assertIn("pywinauto", project)

    def test_guidance_requires_whitespace_normalized_prose_contracts(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("normalize", normalized.lower())
            self.assertIn("whitespace", normalized.lower())
            self.assertIn("newline", normalized.lower())
        self.assertIn('" ".join(text.split())', agents)
        self.assertIn("Markdown", efficiency)

    def test_missing_github_connector_operation_falls_back_to_remote_shell(self):
        for text in (self.agents, self.efficiency, self.project):
            normalized = " ".join(text.split())
            self.assertIn("GitHub connector/API does not expose", normalized)
            self.assertIn("`control/remote-shell`", normalized)
        self.assertIn("missing connector method", " ".join(self.agents.split()))
        self.assertIn("Git/branch cleanup", " ".join(self.project.split()))

    def test_gui_input_failure_requires_layered_first_diagnostic(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("environment-gated", normalized)
            self.assertIn("event entry", normalized)
            self.assertIn("hit", normalized)
            self.assertIn("coordinates", normalized)
            self.assertIn("deltas", normalized)
        self.assertIn("where the signal stops", efficiency)
        self.assertIn("failing layer", project)
        self.assertIn("before changing the interaction strategy", agents)

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
