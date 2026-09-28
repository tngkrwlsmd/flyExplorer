from pathlib import Path
import unittest
r=Path(__file__).resolve().parents[1]
class NativeWorkspaceContract(unittest.TestCase):
 def test_native_command_and_scope(self):
  s=(r/"src/fxfile/main_frame.cpp").read_text(encoding="utf-8-sig")
  h=(r/"src/fxfile/main_frame.h").read_text(encoding="utf-8-sig")
  x=(r/"src/fxfile/fxfile.rc").read_text(encoding="utf-8-sig")
  for name in ("SAVE","OPEN"):
   self.assertIn("ON_COMMAND(ID_VIEW_WORKSPACE_"+name,s)
   self.assertIn("ID_VIEW_WORKSPACE_"+name,x)
   self.assertIn("On"+name.title()+"Workspace",h)
  for text in ("OFN_OVERWRITEPROMPT","1048576","schema","--conf_dir",
               "INIT_TYPE_LAST_TAB","config.global_hotkey.enable",
               "gOpt->saveMainOption(sSnapshot)","::CreateProcess"):
   self.assertIn(text,s)
 def test_owned_native_dialogs(self):
  t=(r/"build/test_ui_uxh07_named_workspace_runtime.py").read_text(encoding="utf-8")
  for x in ("SECOND_NAMED_WORKSPACE_GUI_RESTORED_DIFFERENT_2_1_TABS",
             "ORIGINAL_SETTINGS_SIX_HASHES_IDENTICAL"):
   self.assertIn(x,t)
if __name__=="__main__":unittest.main()
