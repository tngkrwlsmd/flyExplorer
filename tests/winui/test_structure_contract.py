"""Canonical main-tree structure guard for the WinUI product."""
from pathlib import Path
import unittest
from historical_mfc import revision_exists, exists as historical_exists

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app"/"winui"

class StructureContract(unittest.TestCase):
    def test_canonical_product_paths(self):
        self.assertTrue((APP/"MainWindow.xaml").is_file())
        self.assertTrue((APP/"build.cmd").is_file())
        self.assertTrue((ROOT/"tools/winui/run_checks.py").is_file())
        self.assertTrue((ROOT/"clean.bat").is_file())
        self.assertTrue((ROOT/"package.bat").is_file())
        self.assertTrue((ROOT/"packaging/package.py").is_file())
        self.assertTrue((ROOT/"packaging/installer/setup.cpp").is_file())
        self.assertTrue((APP/"product_version.h").is_file())
        self.assertTrue((APP/"product.rc").is_file())
        self.assertTrue((APP/"Assets/flyExplorer.ico").is_file())
        self.assertTrue((ROOT/"tests/winui/test_shell_gui.py").is_file())
        self.assertTrue((ROOT/"tests/winui/paths.py").is_file())
        self.assertTrue((ROOT/"tests/winui/historical_mfc.py").is_file())
        self.assertFalse((ROOT/"experiments").exists())
        for rel in ("x64","obj","Generated Files","FlyExplo.A79A2C56",
                    "helper/bin","helper/obj"):
            self.assertFalse((APP/rel).exists(),rel)

    def test_root_commands_are_winui_first(self):
        build=(ROOT/"build.bat").read_text(encoding="utf-8-sig")
        run=(ROOT/"run.bat").read_text(encoding="utf-8-sig")
        test=(ROOT/"test.bat").read_text(encoding="utf-8-sig")
        clean=(ROOT/"clean.bat").read_text(encoding="utf-8-sig")
        package=(ROOT/"package.bat").read_text(encoding="utf-8-sig")
        self.assertIn(r"app\winui\build.cmd",build)
        self.assertIn(r"out\winui",run)
        self.assertIn(r"tools\winui\run_checks.py",test)
        self.assertIn(r"%~dp0out",clean)
        self.assertIn(r"%~dp0.cache",clean)
        self.assertIn(r"packaging\package.py",package)
        self.assertIn("flyExplorer.exe",run)
        ignore=(ROOT/".gitignore").read_text(encoding="utf-8-sig")
        self.assertIn("/out/",ignore)
        self.assertIn("/.cache/",ignore)
        for body in (build,run,test,package):
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

    def test_retired_mfc_exists_only_in_git_history(self):
        self.assertFalse((ROOT/"legacy").exists())
        self.assertFalse((ROOT/"local_ci.bat").exists())
        self.assertFalse((ROOT/"fxfile.gyp").exists())
        for name in ("build","dist","lib"):
            self.assertFalse((ROOT/name).exists(),name)
        self.assertEqual(["base"],
            sorted(p.name for p in (ROOT/"src").iterdir() if p.is_dir()))
        self.assertTrue(revision_exists())
        for path in ("src/fxfile/main_frame.cpp",
                     "src/fxfile/search_dlg.cpp",
                     "src/fxfile/bookmark.cpp"):
            self.assertTrue(historical_exists(path),path)

if __name__=="__main__":
    unittest.main()
