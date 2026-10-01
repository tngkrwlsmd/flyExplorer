"""M2.7 installer ownership, uninstall and elevation contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SETUP=ROOT/"packaging"/"installer"/"setup.cpp"

class InstallerContract(unittest.TestCase):
    def test_machine_install_and_shortcut_surfaces_are_explicit(self):
        body=SETUP.read_text(encoding="utf-8")
        for token in ("FOLDERID_ProgramFiles","FOLDERID_CommonPrograms",
                      "FOLDERID_Desktop", 'L"runas"',
                      "flyExplorerUninstall.exe",
                      "CurrentVersion\\\\Uninstall\\\\flyExplorer",
                      "QuietUninstallString","EstimatedSize"):
            self.assertIn(token,body)

    def test_uninstall_is_manifest_bounded_and_preserves_user_settings(self):
        body=SETUP.read_text(encoding="utf-8")
        self.assertIn("install-manifest.txt",body)
        self.assertIn("removeInstalledPayload",body)
        self.assertIn("RegDeleteKeyExW",body)
        self.assertNotIn("LOCALAPPDATA",body)
        self.assertNotIn("remove_all(root)",body)
        self.assertIn("fs::remove(root,ec)",body)

    def test_private_installer_lifecycle_mode_is_bounded(self):
        body=SETUP.read_text(encoding="utf-8")
        self.assertIn("/TESTROOT=",body)
        self.assertIn("flyexplorer-installer-test-",body)
        self.assertIn("HKEY_CURRENT_USER",body)
        self.assertIn("flyExplorer-InstallerTest",body)
        self.assertIn("/TESTDISPLAYVERSION=",body)

    def test_package_command_builds_one_setup_artifact(self):
        root=(ROOT/"package.bat").read_text(encoding="utf-8-sig")
        script=(ROOT/"packaging/package.py").read_text(encoding="utf-8")
        self.assertIn(r"packaging\package.py",root)
        self.assertIn("flyExplorer-Setup-x64.exe",script)
        self.assertIn("shutil.rmtree(package_out)",script)
        self.assertIn("PAYLOAD_FILES=",script)

    def test_msbuild_discovery_is_shared_and_not_edition_locked(self):
        resolver=(ROOT/"tools/winui/resolve_msbuild.py").read_text(encoding="utf-8")
        app=(ROOT/"app/winui/build.cmd").read_text(encoding="utf-8-sig")
        helper=(ROOT/"app/winui/helper/build.cmd").read_text(encoding="utf-8-sig")
        package=(ROOT/"packaging/package.py").read_text(encoding="utf-8")
        self.assertIn("vswhere.exe",resolver)
        self.assertIn("Microsoft.Component.MSBuild",resolver)
        for body in (app,helper,package):
            self.assertIn("resolve_msbuild.py",body)
        self.assertNotIn(r"C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild",app)
        self.assertNotIn(r"C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild",helper)
        self.assertNotIn(r"C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild",package)

if __name__=="__main__":
    unittest.main()
