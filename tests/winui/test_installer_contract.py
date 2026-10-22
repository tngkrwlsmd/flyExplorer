"""M2.7 installer ownership, uninstall and elevation contracts."""
from pathlib import Path
import importlib.util
import os
import unittest

ROOT=Path(__file__).resolve().parents[2]
SETUP=ROOT/"packaging"/"installer"/"setup.cpp"
SETUP_PROJECT_TEMPLATE=ROOT/"packaging"/"installer"/"flyExplorerSetup.project-template.xml"

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
        self.assertIn("payload_provenance.verify_snapshot()",script)
        self.assertIn("RUNTIME_MANIFEST_SHA256=",script)
        self.assertTrue(SETUP_PROJECT_TEMPLATE.is_file())
        template=SETUP_PROJECT_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("<PlatformToolset>v145</PlatformToolset>",template)
        self.assertNotIn("v143",template)
        self.assertIn("SETUP_PROJECT_TEMPLATE",script)
        self.assertIn("materialize_setup_project",script)

    def test_owned_installer_lifecycle_verifies_runtime_update_and_rollback(self):
        body=(ROOT/"tests/winui/test_installed_lifecycle.py").read_text(
            encoding="utf-8")
        helper=(ROOT/"tools/winui/diagnose_installed_shutdown.py").read_text(
            encoding="utf-8")
        for token in (
            "PAYLOAD_PROVENANCE.json",
            "runtime_provenance(root)",
            "OWNED_INSTALLER_RUNTIME_PROVENANCE_PASS",
            "OWNED_INSTALLER_STALE_MANIFEST_CLEANUP_PASS",
            "OWNED_INSTALLER_UPDATE_LAUNCH_PASS",
            "OWNED_INSTALLER_ROLLBACK_LAUNCH_PASS",
            "OWNED_INSTALLER_RUNTIME_PROCESSES_SETTLED",
            "wait_owned_runtime_processes(root,label)",
            "shutdown_helper.post_close_and_observe",
            "OWNED_RUNTIME_SHUTDOWN_PROBE_PASS",
            "--runtime-root",
            "USER_SETTINGS_SENTINEL_PRESERVED",
        ):
            self.assertIn(token,body)
        for token in (
            "SHUTDOWN_TIMELINE",
            "WM_CLOSE_POSTED=",
            "HWND_EXISTS=",
            "PID_ALIVE=",
            "TOP_LEVEL_WINDOWS=",
            "CHILD_PIDS=",
            "INSTALLED_APP_WINDOW_CLOSE_TIMEOUT",
            "INSTALLED_APP_PROCESS_EXIT_TIMEOUT",
            "INSTALLED_APP_HARNESS_OBSERVATION_FAILURE",
        ):
            self.assertIn(token,helper)

    def test_lifecycle_refuses_preexisting_hkcu_test_registration(self):
        script=(ROOT/"tests/winui/test_installed_lifecycle.py").read_text(
            encoding="utf-8")
        main=script.split("def main():",1)[1]
        before_fixture=main.split("    LOGS.mkdir(",1)[0]
        self.assertIn("if reg_exists():",before_fixture)
        self.assertIn(
            "refusing to overwrite an existing installer test registry key",
            before_fixture)
        self.assertIn("raise RuntimeError(",before_fixture)

    def test_complete_removal_requires_explicit_opt_in_and_scoped_profile(self):
        body=SETUP.read_text(encoding="utf-8")
        self.assertIn('eq(a,L"/PURGEUSERDATA")',body)
        self.assertIn("o.purgeUserData&&(!o.uninstall||!o.silent)",body)
        self.assertIn("config.pszVerificationText=",body)
        self.assertIn("purge=checked!=FALSE",body)
        self.assertIn("FOLDERID_LocalAppData",body)
        self.assertIn("installer-profile-",body)
        self.assertIn('target.filename()!=L"flyExplorer"',body)
        self.assertIn("reparsePoint(target)",body)
        self.assertIn("safeManifestTarget(root,relative)",body)
        self.assertIn("if(!removeInstalledPayload(root))return ERROR_ACCESS_DENIED",body)
        self.assertIn("if(!removeShortcuts(o,root))return ERROR_ACCESS_DENIED",body)
        self.assertIn("ERROR_DIR_NOT_EMPTY",body)
        self.assertIn("onlySelfAndManifestRemain(root)",body)
        self.assertIn("if(reparsePoint(item.path()))return false",body)
        tail=body.split("int uninstall(Options o,",1)[1]
        self.assertLess(tail.index("if(!fs::remove(root,ec)"),
                        tail.index("if(o.purgeUserData&&!removePrivateData(o,root))"))

    def test_owned_lifecycle_proves_normal_and_purge_modes(self):
        body=(ROOT/"tests/winui/test_installed_lifecycle.py").read_text(
            encoding="utf-8")
        for marker in (
            "OWNED_INSTALLER_NORMAL_REMOVE_PRESERVES_SETTINGS",
            "OWNED_INSTALLER_IMPLICIT_PURGE_REJECTED",
            "OWNED_INSTALLER_UNTRACKED_FILE_BLOCKED_PURGE",
            "OWNED_INSTALLER_SELF_RESIDUAL_REFUSED",
            "OWNED_INSTALLER_EXPLICIT_PURGE_REMOVES_ONLY_OWNED_DATA",
        ):
            self.assertIn(marker,body)
        self.assertIn("assert unrelated.is_file() and sentinel.is_file()",body)

    def test_installer_resources_are_losslessly_compressed(self):
        script=(ROOT/"packaging/package.py").read_text(encoding="utf-8")
        installer=SETUP.read_text(encoding="utf-8")
        self.assertIn("COMPRESS_ALGORITHM_XPRESS_HUFF",script)
        self.assertIn("WindowsPayloadCompression",script)
        self.assertIn("codec.decode(packed,raw_size)!=raw",script)
        self.assertIn("PAYLOAD_RESOURCE_STORED_BYTES=",script)
        self.assertIn("file.storedBytes",installer)
        self.assertIn("CreateDecompressor(",installer)
        self.assertIn("Decompress(decoder,",installer)
        self.assertIn("decoded!=file.bytes",installer)
        self.assertIn('cabinet.lib',installer)

    @unittest.skipUnless(os.name=="nt","Windows built-in Cabinet compression only")
    def test_native_compression_codec_roundtrip(self):
        path=ROOT/"packaging/package.py"
        spec=importlib.util.spec_from_file_location("fly_package_codec",path)
        self.assertIsNotNone(spec)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with module.WindowsPayloadCompression() as codec:
            for source in (
                b"A"*8192,
                bytes(range(256))*200,
                b"flyExplorer"*2048,
                b"",
            ):
                packed=codec.encode(source)
                if source:
                    self.assertEqual(source,codec.decode(packed,len(source)))
                else:
                    self.assertEqual(b"",packed)

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
