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
        cls.verification_profile = (
            ROOT / "docs/development/VERIFICATION_PROFILE.md"
        ).read_text(encoding="utf-8")
        cls.windows_build = (
            ROOT / ".github/workflows/windows-build.yml"
        ).read_text(encoding="utf-8")


    def test_dispatch_shell_requires_no_task_commit(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertIn("command:", self.workflow)
        self.assertIn("working_directory:", self.workflow)
        self.assertIn("FLYEXPLORER_CANONICAL_CHECKOUT: 'C:\\dev\\flyExplorer'", self.workflow)
        self.assertEqual(self.workflow.count("C:\\dev\\flyExplorer"), 1)
        self.assertNotIn("default: 'C:\\dev\\flyExplorer'", self.workflow)
        self.assertIn("$workdir = $env:FLYEXPLORER_CANONICAL_CHECKOUT", self.workflow)
        self.assertIn(
            "${{ env.FLYEXPLORER_CANONICAL_CHECKOUT }}\\logs\\remote-evidence",
            self.workflow,
        )
        self.assertIn("if: github.event_name == 'workflow_dispatch'", self.workflow)
        self.assertIn("Invoke-Expression $env:REMOTE_COMMAND", self.workflow)
        self.assertIn("Set-Location -LiteralPath $workdir", self.workflow)


    def test_request_slot_uses_dedicated_control_branch(self):
        self.assertIn("workflow_call:", self.workflow)
        self.assertIn("request_ref:", self.workflow)
        self.assertIn("request_branch:", self.workflow)
        self.assertNotIn("\n  push:", self.workflow)
        self.assertIn("ref: ${{ inputs.request_ref }}", self.workflow)
        self.assertIn("INPUT_REQUEST_BRANCH: ${{ inputs.request_branch }}", self.workflow)
        self.assertIn('Remote shell reusable workflow only accepts control/remote-shell requests.', self.workflow)
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

    def test_remote_stage_detection_matches_executions_not_incidental_filenames(self):
        self.assertIn(
            "Match executable invocations, not incidental filenames/variables.",
            self.workflow,
        )
        self.assertIn("$stageStatements =", self.workflow)
        self.assertIn("py_compile|compileall", self.workflow)
        self.assertIn(
            "Static Python syntax/import checks do not execute GUI/native/visual stages.",
            self.workflow,
        )
        self.assertIn(
            "tools/winui/validate_remote_request.py",
            " ".join((self.agents + self.efficiency + self.project).split()),
        )
        self.assertTrue(
            (ROOT / "tools/winui/validate_remote_request.py").is_file()
        )
        self.assertTrue(
            (ROOT / "tests/winui/test_gui_harness_contract.py").is_file()
        )


    def test_windows_job_has_static_candidate_fail_fast_gate(self):
        self.assertIn("- name: Static candidate preflight", self.workflow)
        self.assertIn("STATIC_CANDIDATE_PREFLIGHT=SKIP_NON_VALIDATION", self.workflow)
        self.assertIn("git worktree add --detach", self.workflow)
        self.assertIn("test_gui_harness_contract.py", self.workflow)
        self.assertIn("test_remote_request_preflight_contract.py", self.workflow)
        self.assertIn("test_remote_windows_task_contract.py", self.workflow)
        self.assertIn("STATIC_CANDIDATE_PREFLIGHT=PASS", self.workflow)
        self.assertLess(
            self.workflow.index("- name: Static candidate preflight"),
            self.workflow.index("- name: Run remote shell command"),
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
            self.assertIn("validation fingerprint", normalized)
            self.assertIn("retry_revision", normalized)
            self.assertIn("diagnosis-free", normalized)
        self.assertIn("FLYEXPLORER_DEFAULT_VALIDATION_RUN_BUDGET", self.workflow)


    def test_dispatch_path_does_not_require_checkout(self):
        self.assertIn(
            "- name: Checkout control branch request\n"
            "        if: inputs.request_ref != ''",
            self.workflow,
        )
        self.assertIn(
            "- name: Resolve dispatched shell inputs\n"
            "        if: github.event_name == 'workflow_dispatch'",
            self.workflow,
        )
        self.assertIn(
            "if: inputs.request_ref != '' || github.event_name == 'workflow_dispatch'",
            self.workflow,
        )

    def test_main_remote_workflow_is_the_single_execution_source(self):
        normalized = " ".join((self.agents + self.efficiency + self.project).split())
        self.assertIn("reusable workflow", normalized)
        self.assertIn("@main", normalized)
        self.assertIn("thin push trigger", normalized)
        self.assertIn("workflow_call:", self.workflow)
        self.assertNotIn("\n  push:", self.workflow)
        self.assertIn("Remote Windows Task implementation", self.verification_profile)

    def test_remote_shell_is_the_only_push_based_command_channel(self):
        self.assertNotIn("remote/**", self.workflow)
        self.assertNotIn("remote-task.ps1", self.workflow)
        self.assertNotIn("Run committed remote task", self.workflow)
        agents = " ".join(self.agents.split())
        self.assertIn("minimal control-plane tree", agents)
        self.assertIn("Do not create `remote/**` task branches", agents)


    def test_long_run_guidance_uses_configured_observation_intervals(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("FLYEXPLORER_ROUTINE_OBSERVATION_SECONDS", normalized)
            self.assertIn("FLYEXPLORER_ACTIVE_MONITOR_SECONDS", normalized)
            self.assertIn("short-interval", normalized)
        self.assertIn("FLYEXPLORER_ROUTINE_OBSERVATION_SECONDS:", self.workflow)
        self.assertIn("FLYEXPLORER_ACTIVE_MONITOR_SECONDS:", self.workflow)

    def test_result_dependent_runs_are_followed_to_completion(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("current user request", normalized)
            self.assertIn("blocking dependency", normalized)
            self.assertIn("through completion", normalized)
            self.assertIn("active monitoring", normalized.lower())
            self.assertIn("cadence", normalized.lower())
        self.assertIn(
            "Explicit active monitoring changes the observation cadence",
            agents,
        )
        self.assertIn(
            "Explicit active monitoring changes only the cadence",
            efficiency,
        )
        self.assertIn(
            "Explicit active monitoring changes cadence only",
            project,
        )


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


    def test_remote_run_budget_requires_new_hypothesis_and_evidence_need(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("FLYEXPLORER_DEFAULT_VALIDATION_RUN_BUDGET", normalized)
            self.assertIn("new failure hypothesis", normalized)
            self.assertIn("evidence need", normalized)
            self.assertIn("diagnosis-free", normalized)
        self.assertNotIn("third Windows validation run", agents)
        self.assertNotIn("third Windows validation run", efficiency)
        self.assertNotIn("third Windows validation run", project)


    def test_observation_policy_does_not_duplicate_interval_literals(self):
        for text in (self.agents, self.efficiency):
            normalized = " ".join(text.split())
            self.assertNotIn("three minutes", normalized)
            self.assertNotIn("30 seconds", normalized)
        project_discipline = self.project.split("### Remote-shell and CI discipline", 1)[1].split("### Source-contract hygiene", 1)[0]
        project_discipline = " ".join(project_discipline.split())
        self.assertNotIn("three minutes", project_discipline)
        self.assertNotIn("30 seconds", project_discipline)


    def test_high_cost_fixture_policy_uses_separate_profile(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project_discipline = self.project.split("### Remote-shell and CI discipline", 1)[1].split("### Source-contract hygiene", 1)[0]
        project_discipline = " ".join(project_discipline.split())
        for normalized in (agents, efficiency, project_discipline):
            self.assertIn("high-cost", normalized.lower())
            self.assertIn("VERIFICATION_PROFILE.md", normalized)
        self.assertNotIn("8,000+", agents)
        self.assertNotIn("20,000+", agents)
        self.assertNotIn("8,000+", efficiency)
        self.assertNotIn("20,000+", efficiency)
        self.assertIn("8,000 files", self.verification_profile)
        self.assertIn("20,000-entry", self.verification_profile)

    def test_expensive_e2e_requires_layered_failure_isolation(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            lowered = normalized.lower()
            self.assertIn("input -> event -> model -> projection", normalized)
            self.assertIn("final acceptance", lowered)
            self.assertIn("harness/fixture", lowered)
            self.assertIn("control-plane/environment", lowered)
            self.assertIn("smallest", lowered)
        self.assertIn("not the tool for discovering", agents)
        self.assertIn("pywinauto/UIA", efficiency)
        self.assertIn("final acceptance, not discovery", project.lower())


    def test_remote_settings_are_single_sourced_and_runner_serialization_is_conditional(self):
        for name in (
            "FLYEXPLORER_CANONICAL_CHECKOUT",
            "FLYEXPLORER_ROUTINE_OBSERVATION_SECONDS",
            "FLYEXPLORER_ACTIVE_MONITOR_SECONDS",
            "FLYEXPLORER_REMOTE_RUNNER_CAPACITY",
            "FLYEXPLORER_DEFAULT_VALIDATION_RUN_BUDGET",
        ):
            self.assertIn(name + ":", self.workflow)
            self.assertIn(name, self.verification_profile)
        for text in (self.agents, self.efficiency, self.project):
            self.assertNotIn("C:\\dev\\flyExplorer", text)
        combined = " ".join((self.agents + self.efficiency + self.project).split())
        self.assertIn("FLYEXPLORER_REMOTE_RUNNER_CAPACITY", combined)
        self.assertIn("re-evaluate", combined.lower())
        self.assertIn("concurrency", combined.lower())
        self.assertIn("group: flyexplorer-remote-windows-task", self.workflow)

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

    def test_zero_run_preflight_uses_canonical_local_guards_without_cloud_runner(self):
        agents = " ".join(self.agents.split())
        efficiency = " ".join(self.efficiency.split())
        project = " ".join(self.project.split())
        for normalized in (agents, efficiency, project):
            self.assertIn("tools/winui/validate_remote_request.py", normalized)
            self.assertIn("tests/winui/test_gui_harness_contract.py", normalized)
            self.assertIn("cloud", normalized.lower())
            self.assertIn("Windows VM", normalized)
        self.assertIn("Do not add a GitHub-hosted/cloud runner", agents)
        self.assertIn("do not add github-hosted/cloud compute", project.lower())
        self.assertIn("must not be deferred into a Windows VM task", efficiency)


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
