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
        self.assertTrue((ROOT/"clean.bat").is_file())
        self.assertTrue((ROOT/"package.bat").is_file())
        self.assertTrue((ROOT/"packaging/package.py").is_file())
        self.assertTrue((ROOT/"packaging/installer/setup.cpp").is_file())
        self.assertTrue((APP/"product_version.h").is_file())
        self.assertTrue((APP/"product.rc").is_file())
        self.assertTrue((APP/"Assets/flyExplorer.ico").is_file())
        self.assertTrue((ROOT/"tests/winui/test_shell_gui.py").is_file())
        self.assertTrue((ROOT/"tests/winui/paths.py").is_file())
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
            self.assertIn("flyExplorer",body)

    def test_active_app_links_native_file_core(self):
        project=(APP/"flyExplorer.project-template.xml").read_text(encoding="utf-8")
        self.assertIn(r"..\..\src\base\file_operation_core.cpp",project)
        self.assertIn(r"..\..\src\base\shell_navigation_core.cpp",project)
        self.assertTrue((ROOT/"src/base/file_operation_core.cpp").is_file())

    def test_current_native_source_tree(self):
        self.assertEqual(["base"],
            sorted(p.name for p in (ROOT/"src").iterdir() if p.is_dir()))
        self.assertTrue((ROOT/"src/base/shell_navigation_core.cpp").is_file())
        self.assertTrue((ROOT/"src/base/shell_enum_bridge.cpp").is_file())

if __name__=="__main__":
    unittest.main()
