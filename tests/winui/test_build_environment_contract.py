"""Build-environment, fixture, packaging, and profile-safety contracts."""
from pathlib import Path
import sys
import tempfile
import unittest
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
            ["pywinauto==0.6.9", "Pillow==12.3.0", "psutil==7.2.2"],
        )
    def test_self_hosted_failure_artifacts_are_bounded_and_uploaded(self):
        workflow = (
            ROOT / ".github/workflows/windows-build.yml"
        ).read_text(encoding="utf-8")
        collector = (
            ROOT / "tools/winui/collect_ci_failure_artifacts.py"
        ).read_text(encoding="utf-8")
        self.assertIn("Prepare CI evidence marker", workflow)
        self.assertIn("collect_ci_failure_artifacts.py", workflow)
        self.assertIn(
            "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
            workflow,
        )
        self.assertIn("if: ${{ failure() }}", workflow)
        self.assertIn("retention-days: 14", workflow)
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


if __name__ == "__main__":
    unittest.main()
