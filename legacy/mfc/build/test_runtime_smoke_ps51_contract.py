"""Mutation-based isolated checks for the Windows PowerShell 5.1 smoke guard.

Run on any Python developer host:
    python -m unittest discover -s build -p "test_runtime_smoke_ps51_contract.py" -v

These are source-contract tests, not an actual Windows product launch.
"""
import unittest
from pathlib import Path

from validate_source_invariants import validate_runtime_smoke_ps51_contract


RUNTIME_SMOKE = Path(__file__).resolve().parent / "runtime_smoke.ps1"


class RuntimeSmokePowerShellCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = RUNTIME_SMOKE.read_text(encoding="utf-8")

    def test_current_script_keeps_windows_powershell_compatibility(self):
        self.assertEqual(validate_runtime_smoke_ps51_contract(self.source), [])

    def test_argumentlist_only_api_is_rejected(self):
        broken = self.source.replace(
            '$startInfo.Arguments = (',
            '$startInfo.ArgumentList.Add(',
            1,
        )
        self.assertTrue(validate_runtime_smoke_ps51_contract(broken))

    def test_unquoted_generated_paths_are_rejected(self):
        broken = self.source.replace(
            """'--conf_dir="{0}" "{1}"'""",
            """'--conf_dir={0} {1}'""",
            1,
        )
        self.assertTrue(validate_runtime_smoke_ps51_contract(broken))

    def test_unconditional_kill_bool_rejected(self):
        broken = self.source.replace(
            "Stop-SmokeProcessTree -Target $process",
            "$process.Kill($true)",
        )
        self.assertTrue(validate_runtime_smoke_ps51_contract(broken))

    def test_missing_powershell5_taskkill_fallback_rejected(self):
        broken = self.source.replace(
            "& $taskkill /T /F /PID $Target.Id",
            "$Target.Kill()",
            1,
        )
        self.assertTrue(validate_runtime_smoke_ps51_contract(broken))

    def test_missing_user_profile_protection_rejected(self):
        broken = self.source.replace(
            "if ($blockingUserState.Count -gt 0)",
            "if ($false)",
            1,
        )
        self.assertTrue(validate_runtime_smoke_ps51_contract(broken))


if __name__ == "__main__":
    unittest.main()
