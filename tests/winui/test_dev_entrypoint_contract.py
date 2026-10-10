"""Source-only contracts for the user-facing Windows entry points.

The underlying build scripts remain authoritative. These tests intentionally
check orchestration and fail-closed boundaries without requiring Windows.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


def batch(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8").replace("\r\n", "\n")


class DevEntrypointContract(unittest.TestCase):
    def test_command_dispatch_and_legacy_wrapper_reuse(self):
        fly = batch("fly.bat").lower()
        for action in ("help", "check", "build", "run", "test", "package", "clean"):
            self.assertIn(f'if /i "%action%"=="{action}" goto :{action}', fly)
        for wrapper in ("build.bat", "run.bat", "test.bat", "clean.bat", "package.bat"):
            self.assertIn(f'call "%root%{wrapper}"', fly)
        self.assertNotIn("git reset", fly)
        self.assertNotIn("git clean", fly)
        self.assertNotIn("git push", fly)

    def test_package_order_and_failure_stops(self):
        fly = batch("fly.bat").lower()
        start = fly.index("\n:package\n")
        end = fly.index("\n:package_failed\n", start)
        block = fly[start:end]
        stages = (
            'call "%root%clean.bat" build',
            'call "%root%build.bat" release',
            'python -x utf8 "%root%packaging\\provenance.py" --write',
            'python -x utf8 "%root%packaging\\provenance.py" --check',
            'call "%root%package.bat" release',
        )
        positions = [block.index(stage) for stage in stages]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(4, block.count("if errorlevel 1 goto :package_failed") - 1)
        # Exactly five guarded operations, not a best-effort pipeline.
        self.assertEqual(5, block.count("if errorlevel 1 goto :package_failed"))
        self.assertIn('set "rc=%errorlevel%"', fly)
        self.assertIn("exit /b %rc%", fly)

    def test_click_run_is_nonbuilding_and_preserves_error(self):
        launcher = batch("run.bat").lower()
        self.assertIn('set "config=%~1"', launcher)
        self.assertIn('if "%config%"=="" set "config=release"', launcher)
        self.assertIn('start "" "%exe%"', launcher)
        self.assertIn('if "%~1"=="" pause', launcher)
        self.assertIn("flyshellisolationhelper.exe", launcher)
        self.assertNotIn("call ", launcher)
        self.assertNotIn("build.cmd", launcher)

    def test_cleanup_propagates_deletion_failures(self):
        cleaner = batch("clean.bat").lower()
        self.assertIn('call :remove_build\nif errorlevel 1 exit /b 1', cleaner)
        self.assertIn('if exist "%~dp0out" exit /b 1', cleaner)
        self.assertIn('if exist "%~dp0.cache" exit /b 1', cleaner)
        self.assertGreaterEqual(cleaner.count("if errorlevel 1 exit /b 1"), 3)

    def test_documented_user_entry_point(self):
        readme = batch("README").lower()
        self.assertIn("fly.bat package", readme)
        self.assertIn("double-click", readme)
        self.assertIn("flyexplorer.exe", readme)


if __name__ == "__main__":
    unittest.main()
