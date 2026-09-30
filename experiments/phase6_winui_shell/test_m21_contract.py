"""M2.1 architecture/source assertions; actual native and GUI run separately."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2]
def src(n):return (R/n).read_text(encoding="utf-8-sig")
class KoreanM21(unittest.TestCase):
 def test_default_korean_real_winui_control_resources(self):
  def values(rel):
   root=ET.parse(R/rel).getroot()
   # XML character entities are intentional in M2.6 to keep remote writes
   # ASCII-stable; ElementTree returns the same real localized UI strings.
   return "\n".join(value for e in root.iter()
                     for value in e.attrib.values() if value)
  h=values("experiments/phase6_winui_shell/ShellHeader.xaml")
  n=values("experiments/phase6_winui_shell/NavigationSidebar.xaml")
  main=values("experiments/phase6_winui_shell/MainWindow.xaml")+"\n"+values(
       "experiments/phase6_winui_shell/FileToolbar.xaml")
  for word in ("\ud14c\ub9c8: \uc2dc\uc2a4\ud15c","\uc2dc\uc2a4\ud15c",
               "\ub77c\uc774\ud2b8","\ub2e4\ud06c"):
   self.assertIn(word,h)
  for word in ("\ud0d0\uc0c9","\ub0b4 PC","\ubb38\uc11c"):
   self.assertIn(word,n)
  for word in ("\ud30c\uc77c \uc791\uc5c5",
               "\uc0c8 \ud3f4\ub354","\uc774\ub984 \ubcc0\uacbd"):
   self.assertIn(word,main)
 def test_no_mojibake_runtime_korean_theme_labels(self):
  cpp=src("experiments/phase6_winui_shell/ShellHeader.xaml.cpp")
  for word in ("\ud14c\ub9c8: \uc2dc\uc2a4\ud15c","\ud14c\ub9c8: \ub77c\uc774\ud2b8",
               "\ud14c\ub9c8: \ub2e4\ud06c"):
   self.assertIn(word,cpp)
  self.assertNotIn("??:",cpp)
 def test_real_compiled_reusable_usercontrols_and_utf8(self):
  project=src("experiments/phase6_winui_shell/FlyExplorerWinUIShell.project-template.xml")
  for stem in ("ShellHeader","NavigationSidebar"):
   for ext in (".idl",".xaml",".xaml.cpp",".xaml.h"):
    self.assertIn(stem+ext,project)
  self.assertIn("/bigobj /utf-8",project)
  for name in ("preview_preferences.cpp","file_command_core.cpp","m21_commands.cpp"):
   self.assertIn(name,project)
 def test_preview_settings_are_korean_and_separate_from_mfc_conf(self):
  cpp=src("src/base/preview_preferences.cpp")
  h=src("src/base/preview_preferences.h")
  for token in ("WinUI3Preview","ui-preferences-v1.txt","ko-KR","GetTempFileNameW",
                "MOVEFILE_WRITE_THROUGH","MOVEFILE_REPLACE_EXISTING"):
   self.assertIn(token,cpp+h)
  self.assertNotIn("fxfile\\\\conf",cpp+h)
 def test_native_file_mutation_rejects_traversal_devices_and_overwrites(self):
  cpp=src("src/base/file_command_core.cpp")
  for token in ("validLeaf","ERROR_INVALID_NAME","ERROR_ALREADY_EXISTS",
                "CreateDirectoryW","MoveFileW","parent_path()!=folder"):
   self.assertIn(token,cpp)
  self.assertNotIn("MoveFileExW",cpp)
  self.assertNotIn("DeleteFileW",cpp)
 def test_real_winui_uses_native_file_command_and_weak_async_dispatch(self):
  impl=src("experiments/phase6_winui_shell/m21_commands.cpp")
  header=src("experiments/phase6_winui_shell/MainWindow.xaml.h")
  for token in ("filecommand::execute","mFileOperationEpoch","get_weak()",
                "DispatcherQueue()","CreateFolderButton","RenameButton"):
   self.assertIn(token,impl+header)
 def test_actual_owned_gui_verifies_korean_and_restart_safety(self):
  test=src("experiments/phase6_winui_shell/test_m21_gui.py")
  harness=src("experiments/phase6_winui_shell/test_shell_gui.py")
  for token in ("REAL_M21_SECOND_OWNED_PROCESS_RELOADED_KOREAN_DARK_THEME",
                "REAL_M21_NATIVE_RENAME_SELECTED_OWNED_KOREAN_FOLDER",
                "REAL_M21_DUPLICATE_KOREAN_NAME_BLOCKED"):
   self.assertIn(token,test)
  self.assertIn('FLY_M21_OWNED_FEATURES',harness)
if __name__=="__main__":unittest.main()
