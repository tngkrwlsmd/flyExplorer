"""G01 synthetic mapping-provenance boundary: no real processes or paths."""
import importlib.util
from pathlib import Path
import unittest

HELPER = Path(__file__).resolve().parent / "g01_runtime_module_paths.py"
spec = importlib.util.spec_from_file_location("g01_runtime_module_paths", HELPER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class G01CoreMsgProvenanceTests(unittest.TestCase):
    def classify(self, paths):
        return module.classify_coremsg_paths(
            r"C:\owned\out\winui\Release\flyExplorer.exe",
            paths, r"C:\Program Files", r"C:\Windows")

    def test_app_local_runtime_and_package_runtime_are_distinct(self):
        observed = self.classify([
            r"C:\owned\out\winui\Release\CoreMessagingXP.dll",
            r"C:\Program Files\WindowsApps\Microsoft.WindowsAppRuntime.2_2.5.1.0_x64\CoreMessagingXP.dll",
            r"C:\Windows\System32\CoreMessagingXP.dll",
            r"C:\Other\CoreMessagingXP.dll",
        ])
        self.assertEqual(observed, {
            "APPLOCAL": 1, "WINDOWSAPPS": 1, "SYSTEM": 1, "OTHER": 1})

    def test_case_insensitive_dedup_and_path_boundary(self):
        observed = self.classify([
            r"C:\OWNED\OUT\WINUI\RELEASE\CoreMessagingXP.DLL",
            r"c:\owned\out\winui\Release\coremessagingxp.dll",
            r"C:\owned\out\winui\ReleaseOther\CoreMessagingXP.dll",
            r"C:\Program Files\WindowsAppsOther\CoreMessagingXP.dll",
            r"C:\Windows\System32Other\CoreMessagingXP.dll",
            r"C:\Windows\System32\combase.dll",
        ])
        self.assertEqual(observed, {
            "APPLOCAL": 1, "WINDOWSAPPS": 0, "SYSTEM": 0, "OTHER": 3})

    def test_empty_nonspecific_or_invalid_mapping(self):
        self.assertEqual(sum(self.classify([]).values()), 0)
        self.assertEqual(sum(self.classify([None, "", "CoreMessagingXP.dll"]).values()), 1)
        with self.assertRaises(ValueError):
            module.classify_coremsg_paths("a.exe", [], "", r"C:\Windows")

    def test_harness_pid_scoped_and_exports_counters_only(self):
        text = (HELPER.parent / "test_owned_g01_shutdown_gui.py").read_text("utf-8")
        self.assertIn("inspected = psutil.Process(proc.pid)", text)
        self.assertIn("inspected.memory_maps()", text)
        self.assertIn("G01_OWNED_COREMSG_PROVENANCE", text)
        self.assertIn("G01_OWNED_GUI_FIXTURE_CLEANED=YES", text)
        source = HELPER.read_text("utf-8")
        self.assertNotIn("print(", source)
        self.assertNotIn("ReadProcessMemory", source)


if __name__ == "__main__":
    unittest.main()
