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

    def test_dispatch_path_does_not_require_checkout(self):
        self.assertIn(
            "- name: Checkout remote task branch\n"
            "        if: github.event_name == 'push'",
            self.workflow,
        )
        self.assertIn(
            "- name: Run committed remote task\n"
            "        if: github.event_name == 'push'",
            self.workflow,
        )

    def test_legacy_remote_branch_path_remains_a_fallback(self):
        self.assertIn("- 'remote/**'", self.workflow)
        self.assertIn("- '.github/remote-task.ps1'", self.workflow)
        self.assertIn('".github\\remote-task.ps1"', self.workflow)

    def test_guidance_prefers_repository_dispatch_and_keeps_rdc_auxiliary(self):
        self.assertIn(
            "prefer this repository's `Remote Windows Task` workflow_dispatch shell",
            self.agents,
        )
        self.assertIn("RDC or another desktop-control path is a supplementary tool", self.agents)
        self.assertIn(
            "prefer this repository's `Remote Windows Task` workflow_dispatch shell",
            self.efficiency,
        )
        self.assertIn("RDC/desktop-control is supplementary", self.efficiency)


if __name__ == "__main__":
    unittest.main()
