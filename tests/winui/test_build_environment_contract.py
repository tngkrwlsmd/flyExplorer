"""Build-environment, fixture, packaging, and profile-safety contracts."""
from pathlib import Path
import importlib.util
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "winui"))
from profile_guard import (
    LEGACY_NAMES,
    assert_legacy_profile_unchanged,
    snapshot_legacy_profile,
)

TEMPLATES = [
    ROOT / "app/winui/flyExplorer.project-template.xml",
    ROOT / "app/winui/helper/FlyShellIsolationHelper.project-template.xml",
    ROOT / "tests/winui/m19/FlyM19NativeContracts.project-template.xml",
    ROOT / "tests/winui/m20/FlyM20StateContracts.project-template.xml",
    ROOT / "tests/winui/m21/FlyM21NativeContracts.project-template.xml",
    ROOT / "tests/winui/m22/FlyM22ShellTransferContracts.project-template.xml",
    ROOT / "tests/winui/m23/FlyM23NativeContracts.project-template.xml",
    ROOT / "packaging/installer/flyExplorerSetup.project-template.xml",
]
NS = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}


class BuildEnvironmentContract(unittest.TestCase):
    def test_canonical_projects_are_v145_sdk26100_only(self):
        for path in TEMPLATES:
            self.assertTrue(path.is_file(), path)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("v143", text, path)
            root = ET.fromstring(text)
            toolsets = {
                node.text for node in root.findall(".//m:PlatformToolset", NS)
            }
            self.assertEqual(toolsets, {"v145"}, path)
            sdk = {
                node.text
                for node in root.findall(
                    ".//m:WindowsTargetPlatformVersion", NS)
            }
            self.assertEqual(sdk, {"10.0.26100.0"}, path)

    def test_app_requires_vs18_without_old_fallback(self):
        text = TEMPLATES[0].read_text(encoding="utf-8")
        self.assertIn(
            "<MinimumVisualStudioVersion>18.0</MinimumVisualStudioVersion>",
            text)
        self.assertNotIn("$(VisualStudioVersion)' &lt; '18.0", text)

    def test_resolver_requires_msbuild18_v145_and_sdk26100(self):
        body = (ROOT / "tools/winui/resolve_msbuild.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('REQUIRED_MSBUILD_MAJOR = 18', body)
        self.assertIn('REQUIRED_TOOLSET = "v145"', body)
        self.assertIn('REQUIRED_SDK = "10.0.26100.0"', body)
        self.assertIn('"-version"', body)
        self.assertIn("cl.exe", body)
    def test_native_fixture_builds_use_shared_msbuild_resolver(self):
        for milestone in ("m19", "m20", "m21", "m22", "m23"):
            body = (
                ROOT / f"tests/winui/{milestone}/build.cmd"
            ).read_text(encoding="utf-8")
            self.assertIn("tools\\winui\\resolve_msbuild.py", body)
            self.assertNotIn("Visual Studio\\18\\Community", body)
    def test_m19_native_fixture_sources_resolve_to_app(self):
        template = TEMPLATES[2]
        root = ET.fromstring(template.read_text(encoding="utf-8"))
        entries = [
            node.attrib["Include"]
            for node in root.findall(".//m:ClCompile", NS)
            if "Include" in node.attrib
        ]
        wanted = [
            item for item in entries
            if "m19_workspace.cpp" in item or "m19_search.cpp" in item
        ]
        self.assertEqual(len(wanted), 2)
        for rel in wanted:
            path = (
                template.parent / Path(rel.replace("\\", "/"))
            ).resolve()
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.parent, (ROOT / "app/winui").resolve())

    def test_gui_dependencies_are_exactly_pinned(self):
        lines = [
            item.strip()
            for item in (
                ROOT / "tests/winui/requirements-gui.txt"
            ).read_text(encoding="utf-8").splitlines()
            if item.strip() and not item.startswith("#")
        ]
        self.assertEqual(
            lines,
            ["pywinauto==0.6.9", "Pillow==13.0.0", "psutil==7.2.2"],
        )
    def test_policy_batch_gate_propagates_validator_failure(self):
        body = (ROOT / "test.bat").read_text(encoding="utf-8")
        self.assertIn('if /I "%STAGE%"=="policy" goto :policy', body)
        self.assertIn(":policy", body)
        self.assertIn(
            'python -X utf8 "%~dp0tools\\policy\\run_policy_checks.py"\n'
            'exit /b %ERRORLEVEL%',
            body,
        )
        self.assertNotIn('if /I "%STAGE%"=="policy" (', body)

    def test_owned_gui_actions_timeout_scale_is_bounded(self):
        gui = (ROOT / "tests/winui/test_shell_gui.py").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'GUI_TIMEOUT_SCALE=1.5 if os.environ.get("GITHUB_ACTIONS")=="true" else 1.0',
            gui,
        )
        normalized = "".join(gui.split())
        self.assertIn(
            "seconds=timeout*GUI_TIMEOUT_SCALE",
            normalized,
        )
        self.assertIn("interval=.13", normalized)

    def test_full_ci_gui_budget_preserves_focused_limits_and_cleanup_reserve(self):
        sys.path.insert(0, str(ROOT / "tools" / "winui"))
        from run_checks import gui_command, GUI_CHAIN_BUDGET_ENV

        inherited = {GUI_CHAIN_BUDGET_ENV: "999"}
        for ci in (True, False):
            env = {**inherited, "GITHUB_ACTIONS": "true" if ci else "false"}
            for area, expected in (("all", 390 if ci else 260),
                                   ("startup-integrated", 260), ("search", 260),
                                   ("core", 260), ("folder-tree", 150)):
                with self.subTest(ci=ci, area=area):
                    cmd, child, limit = gui_command(area, "Release", env)
                    self.assertEqual(expected, limit)
                    self.assertEqual("test_shell_gui.py", Path(cmd[-1]).name)
                    if ci and area == "all":
                        self.assertEqual("350", child[GUI_CHAIN_BUDGET_ENV])
                        self.assertEqual(40, limit-int(child[GUI_CHAIN_BUDGET_ENV]))
                        self.assertEqual("YES", child["FLY_EP05_EXPLORER_HANDOFF"])
                    else:
                        self.assertNotIn(GUI_CHAIN_BUDGET_ENV, child)
                    self.assertEqual("999", env[GUI_CHAIN_BUDGET_ENV])

    def test_ci_full_gui_calibration_is_bounded_and_scope_isolated(self):
        sys.path.insert(0, str(ROOT / "tools" / "winui"))
        from run_checks import full_gui_ci_timeout, gui_command, GUI_CHAIN_BUDGET_ENV

        for measured, expected in ((None, 390), (0, 390), (64.2, 390),
                                   (65, 390), (164.8, 928), (195, 940),
                                   (300, 840), (750, 390)):
            with self.subTest(measured=measured):
                self.assertEqual(expected, full_gui_ci_timeout(measured))
        for invalid in (-1, float("nan"), float("inf"), 750.1, 751):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                full_gui_ci_timeout(invalid)
        key = GUI_CHAIN_BUDGET_ENV
        for ci in (False, True):
            env = {key: "9999", "GITHUB_ACTIONS": str(ci).lower()}
            for area, expected in (("all", 928 if ci else 260),
                                   ("startup-integrated", 260), ("search", 260),
                                   ("core", 260), ("folder-tree", 150),
                                   ("window-tabs", 260), ("shortcuts", 150),
                                   ("filter-preset", 150)):
                with self.subTest(ci=ci, area=area):
                    _, child, limit = gui_command(
                        area, "Release", env, focused_elapsed_seconds=164.8)
                    self.assertEqual(expected, limit)
                    if ci and area == "all":
                        self.assertEqual(str(limit - 40), child[key])
                    else:
                        self.assertNotIn(key, child)
                    self.assertEqual("9999", env[key])

    def test_full_ci_gui_measures_only_successful_focused_probes(self):
        from types import SimpleNamespace
        sys.path.insert(0, str(ROOT / "tools" / "winui"))
        import run_checks

        focus = {"gui-window-tabs-Release": 59.7, "gui-shortcuts-Release": 39.5,
                 "gui-filter-preset-Release": 36.3, "gui-folder-tree-Release": 29.3}
        key = run_checks.GUI_CHAIN_BUDGET_ENV
        for fail_label, too_slow, expected in (
                (None, False, 0), ("gui-filter-preset-Release", False, 7),
                (None, True, 1)):
            with self.subTest(fail_label=fail_label, too_slow=too_slow):
                now = [0.0]
                calls = []

                def run(label, cmd, timeout, env, tag):
                    calls.append((label, timeout, env.copy()))
                    now[0] += (751 if too_slow and label == "gui-window-tabs-Release"
                               else focus.get(label, 1))
                    return 7 if label == fail_label else 0

                with patch.object(run_checks, "execute", side_effect=run), patch.object(
                        run_checks, "fail", side_effect=lambda category, rc: rc), patch.object(
                        run_checks, "time", SimpleNamespace(monotonic=lambda: now[0])):
                    self.assertEqual(expected, run_checks.run_gui(
                        "all", "Release", {"GITHUB_ACTIONS": "true", key: "9999"}, "tag"))
                if expected == 0:
                    self.assertEqual(6, len(calls))
                    self.assertEqual(("gui-all-Release", 928), calls[-1][:2])
                    self.assertEqual("888", calls[-1][2][key])
                    self.assertTrue(all(key not in x[2] for x in calls[1:-1]))
                else:
                    self.assertNotIn("gui-all-Release", [x[0] for x in calls])

    def test_integrated_gui_deadline_caps_wait_and_refuses_late_success(self):
        import ast
        from types import SimpleNamespace
        gui = (ROOT / "tests/winui/test_shell_gui.py").read_text(encoding="utf-8")
        functions = [node for node in ast.parse(gui).body
                     if isinstance(node, ast.FunctionDef)
                     and node.name in ("remaining_chain_seconds", "eventually")]
        self.assertEqual(2, len(functions))
        clock = [10.0]
        calls = []

        def wait(fn, label, *, seconds, interval):
            calls.append((seconds, interval))
            return fn()

        namespace = {"time": SimpleNamespace(monotonic=lambda: clock[0]),
                     "GUI_TIMEOUT_SCALE": 1.5, "GUI_CHAIN_DEADLINE": None,
                     "wait_until": wait}
        exec(compile(ast.Module(body=functions, type_ignores=[]),
                     "owned GUI deadline", "exec"), namespace)
        eventually = namespace["eventually"]
        self.assertEqual("ready", eventually(lambda: "ready", "normal", 8))
        self.assertEqual((12, .13), calls[-1])
        namespace["GUI_CHAIN_DEADLINE"] = 40
        self.assertTrue(eventually(lambda: True, "within budget", 8))
        self.assertEqual((12, .13), calls[-1])
        namespace["GUI_CHAIN_DEADLINE"] = 15
        self.assertTrue(eventually(lambda: True, "remaining budget", 8))
        self.assertEqual((5, .13), calls[-1])
        clock[0] = 15
        with self.assertRaisesRegex(AssertionError, "deadline exhausted"):
            eventually(lambda: self.fail("expired predicate executed"), "expired", 8)
        self.assertEqual(3, len(calls))
        clock[0] = 14

        def late():
            clock[0] = 16
            return True

        with self.assertRaisesRegex(AssertionError, "deadline exhausted"):
            eventually(late, "late success", 8)
        self.assertEqual((1, .13), calls[-1])

    def test_hard_gui_timeout_is_not_success_or_confirmed_cleanup(self):
        sys.path.insert(0, str(ROOT / "tools" / "winui"))
        import run_checks
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Windows venv launchers can leave the actual interpreter holding
            # the inherited log handle after the launcher is killed. Use the
            # real CPython child for this isolated, dependency-free timeout test.
            child_python = Path(sys._base_executable)
            self.assertTrue(child_python.is_file(), "base interpreter unavailable")
            with patch.object(run_checks, "ROOT", root), patch.object(
                    run_checks, "LOGS", root / "logs"):
                code = run_checks.execute(
                    "gui-timeout-contract", [str(child_python), "-c", "import time; time.sleep(2)"],
                    .1, os.environ.copy(), "owned")
            self.assertEqual(124, code)
            body = (root / "logs/owned-gui-timeout-contract.log").read_text("utf-8")
            self.assertIn("TIMEOUT: bounded local subprocess terminated", body)
            self.assertIn("HARD_TIMEOUT_SECONDS=0.1 CLEANUP_NOT_CONFIRMED", body)

    def test_owned_gui_startup_wait_covers_supervisor_retry_budget(self):
        gui = (ROOT / "tests/winui/test_shell_gui.py").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '"UI-independent native core/helper was not active at startup",18',
            gui,
        )

    def test_full_gui_handoff_collapses_owned_m19_panels_only(self):
        # The normal runner strips inherited fault/diagnostic flags.
        # The full suite must set its M19->M20 handoff flag itself.
        sys.path.insert(0, str(ROOT / "tools" / "winui"))
        from run_checks import gui_command

        candidate = {"FLY_M20_OWNED_COLLAPSE_M19_PANELS": "YES"}
        cmd, full_env, _ = gui_command("all", "Release", {})
        self.assertIn("test_shell_gui.py", str(cmd[-1]))
        self.assertEqual("YES", full_env["FLY_M20_OWNED_COLLAPSE_M19_PANELS"])
        for scope in ("core", "shell", "search", "file-operations", "window-tabs"):
            _, scoped, _ = gui_command(scope, "Release", candidate)
            self.assertNotIn("FLY_M20_OWNED_COLLAPSE_M19_PANELS", scoped, scope)

    def test_retained_failure_collector_is_bounded(self):
        # The former source-repository workflow is retired; the collector
        # remains available for controlled source-side diagnosis.
        collector = (
            ROOT / "tools/winui/collect_ci_failure_artifacts.py"
        ).read_text(encoding="utf-8")
        self.assertIn('LOGS / "winui-scoped"', collector)
        self.assertIn('LOGS / "phase6-winui"', collector)
        self.assertIn('"flyexplorer.exe"', collector)
        self.assertIn("MAX_FILE_BYTES", collector)
        self.assertNotIn("os.environ.items()", collector)

    def test_fresh_profile_guard_preserves_absence_and_existing_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "fxfile" / "conf"
            root.mkdir(parents=True)
            (root / LEGACY_NAMES[0]).write_bytes(b"existing-user-setting")
            profile, state = snapshot_legacy_profile(root)
            self.assertEqual(profile, root)
            self.assertEqual(sum(v is not None for v in state.values()), 1)
            assert_legacy_profile_unchanged(profile, state)

            created = root / LEGACY_NAMES[1]
            created.write_bytes(b"must-be-detected")
            with self.assertRaises(AssertionError):
                assert_legacy_profile_unchanged(profile, state)


class WinUIToolchainPreflight(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "resolve_msbuild", ROOT / "tools/winui/resolve_msbuild.py")
        self.resolver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.resolver)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.fixture = Path(temp.name)
        self.install = self.fixture / "VS18"
        self.vc = self.install / "MSBuild/Microsoft/VC/v180"
        self.msbuild = self.install / "MSBuild/Current/Bin/MSBuild.exe"
        self.store = self.vc / "Application Type/Windows Store/10.0"
        for relative in (
            "MSBuild/Current/Bin/MSBuild.exe",
            "MSBuild/Microsoft/VC/v180/Platforms/x64/PlatformToolsets/v145/Toolset.props",
            "VC/Tools/MSVC/14.51.0/bin/Hostx64/x64/cl.exe",
        ):
            self.touch(self.install / relative)
        version = self.install / "VC/Auxiliary/Build/Microsoft.VCToolsVersion.default.txt"
        self.touch(version)
        version.write_text("14.51.0", encoding="utf-8")
        for relative in (
            "Include/10.0.26100.0/um/Windows.h",
            "Lib/10.0.26100.0/um/x64/kernel32.lib",
            "bin/10.0.26100.0/x64/rc.exe",
        ):
            self.touch(self.fixture / "Windows Kits/10" / relative)
        environment = patch.dict(os.environ, {"ProgramFiles(x86)": str(self.fixture)})
        environment.start()
        self.addCleanup(environment.stop)
        version_probe = patch.object(self.resolver, "msbuild_major", return_value=18)
        version_probe.start()
        self.addCleanup(version_probe.stop)
        self.store_files = (
            "Default.props", "Platforms/x64/Platform.Default.props",
            "Platforms/x64/Platform.props", "Platforms/x64/Platform.targets",
            "Platforms/x64/PlatformToolsets/v145/Toolset.props",
            "Platforms/x64/PlatformToolsets/v145/Toolset.targets",
        )

    @staticmethod
    def touch(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def seed_store(self):
        for relative in self.store_files:
            self.touch(self.store / relative)

    def test_desktop_only_installation_is_rejected_only_for_winui(self):
        self.assertEqual([], self.resolver.validation_errors(self.msbuild))
        errors = self.resolver.validation_errors(self.msbuild, winui=True)
        self.assertEqual(1, len(errors))
        self.assertIn("Windows Store C++ x64 targets", errors[0])
        self.assertIn("Microsoft.VisualStudio.ComponentGroup.UWP.VC", errors[0])

    def test_complete_same_installation_is_accepted(self):
        self.seed_store()
        self.assertEqual([], self.resolver.validation_errors(self.msbuild, winui=True))

    def test_each_missing_store_import_fails_preflight(self):
        self.seed_store()
        for relative in self.store_files:
            with self.subTest(relative=relative):
                path = self.store / relative
                path.unlink()
                self.assertTrue(self.resolver.validation_errors(self.msbuild, winui=True))
                self.touch(path)

    def test_old_toolset_overlay_does_not_satisfy_v145(self):
        self.seed_store()
        (self.store / "Platforms/x64/PlatformToolsets/v145").rename(
            self.store / "Platforms/x64/PlatformToolsets/v143")
        self.assertTrue(self.resolver.validation_errors(self.msbuild, winui=True))

    def test_store_imports_cannot_be_combined_across_vc_roots(self):
        self.seed_store()
        path = self.store / "Platforms/x64/Platform.targets"
        other = self.vc.parent / "v170/Application Type/Windows Store/10.0" / path.relative_to(self.store)
        self.touch(other)
        path.unlink()
        self.assertTrue(self.resolver.validation_errors(self.msbuild, winui=True))

    def test_only_app_build_requests_winui_preflight(self):
        app = (ROOT / "app/winui/build.cmd").read_text(encoding="utf-8")
        helper = (ROOT / "app/winui/helper/build.cmd").read_text(encoding="utf-8")
        self.assertIn('resolve_msbuild.py" --winui', app)
        self.assertNotIn("--winui", helper)


if __name__ == "__main__":
    unittest.main()
