"""Canonical main-tree structure guard for the WinUI product."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app"/"winui"

class StructureContract(unittest.TestCase):
    def test_canonical_product_paths(self):
        self.assertTrue((APP/"MainWindow.xaml").is_file())
        self.assertTrue((APP/"build.cmd").is_file())
        self.assertTrue((ROOT/"tools/winui/run_checks.py").is_file())
        self.assertTrue((ROOT/"tests/winui/test_shell_gui.py").is_file())
        self.assertFalse((ROOT/"experiments").exists())

    def test_root_commands_are_winui_first(self):
        build=(ROOT/"build.bat").read_text(encoding="utf-8-sig")
        run=(ROOT/"run.bat").read_text(encoding="utf-8-sig")
        test=(ROOT/"test.bat").read_text(encoding="utf-8-sig")
        self.assertIn(r"app\winui\build.cmd",build)
        self.assertIn(r"app\winui\x64",run)
        self.assertIn(r"tools\winui\run_checks.py",test)
        for body in (build,run,test):
            self.assertNotIn("phase6_winui_shell",body)
            self.assertNotIn("FLYEXP_PHASE5",body)

    def test_active_app_has_no_legacy_product_dependency(self):
        text="\n".join(p.read_text(encoding="utf-8-sig",errors="replace")
            for p in APP.rglob("*") if p.is_file() and p.suffix.lower() in
            {".cpp",".h",".xaml",".idl",".xml",".cmd",".md"})
        for token in ("experiments/phase6_winui_shell",
                      "phase5_island_bridge","phase5_winui3",
                      "FlyExplorerIslandBridge",
                      r"..\..\src\fxfile\file_operation_core.cpp"):
            self.assertNotIn(token,text)
        self.assertIn(r"..\..\src\base\file_operation_core.cpp",text)

    def test_legacy_mfc_entry_points_are_quarantined(self):
        legacy=ROOT/"legacy"/"mfc"
        for name in ("build.bat","local_ci.bat","fxfile.gyp",
                     "LOCAL_CI_MANUAL.txt","README.md"):
            self.assertTrue((legacy/name).is_file(),name)
        self.assertFalse((ROOT/"local_ci.bat").exists())
        self.assertFalse((ROOT/"fxfile.gyp").exists())
        for name in ("build","dist","lib"):
            self.assertFalse((ROOT/name).exists(),name)
            self.assertTrue((legacy/name).is_dir(),name)
        self.assertEqual(["base"],
            sorted(p.name for p in (ROOT/"src").iterdir() if p.is_dir()))
        for name in ("fxfile","fxfile-crash","fxfile-keyhook",
                     "fxfile-launcher","fxfile-tests","xpr"):
            self.assertTrue((legacy/"src"/name).is_dir(),name)

if __name__=="__main__":
    unittest.main()
