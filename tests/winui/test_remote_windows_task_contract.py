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

    def test_dispatch_path_does_not_require_checkout(self):
        self.assertIn(
            "- name: Checkout pushed control or task branch\n"
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

    def test_legacy_remote_branch_path_remains_a_fallback(self):
        self.assertIn("- 'remote/**'", self.workflow)
        self.assertIn("- '.github/remote-task.ps1'", self.workflow)
        self.assertIn('".github\\remote-task.ps1"', self.workflow)
        self.assertIn(
            "startsWith(github.ref, 'refs/heads/remote/')",
            self.workflow,
        )

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
            self.assertIn("latest main + recent commits + recent main CI", text)
            self.assertIn("expected_main_sha", text)
        self.assertIn("two consecutive failures", self.efficiency)
        self.assertIn("circuit breaker", self.efficiency)
        self.assertIn("already on main", self.agents)
        self.assertIn("already merged and accepted", self.project)
        self.assertIn("one batched", self.project)


if __name__ == "__main__":
    unittest.main()
