"""PX10 independent source gate for the scoped functional GUI oracle."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
def read(rel):return (ROOT/rel).read_text(encoding="utf-8-sig")
class Px10GuiHarnessContract(unittest.TestCase):
 def test_explicit_area_and_scoped_exit(self):
  a=read("tools/winui/run_checks.py");b=read("tests/winui/test_shell_gui.py")
  for needle in ('"selection-projection"','FLY_PX10_SELECTION_ONLY',
                 'PX10_OWNED_GUI_MARKERS_MISSING_OR_ERROR'):
   self.assertIn(needle,a)
  for needle in ('from test_px10_selection_projection_gui import run',
                 'PX10_SELECTION_PROJECTION_GUI_PASS=True',
                 'raise SystemExit(0)','OWNED_SYNTHETIC_FIXTURE_REMOVED'):
   self.assertIn(needle,b)
 def test_exact_owned_selection_focus_and_rebuild_oracle(self):
  p=read("tests/winui/test_px10_selection_projection_gui.py")
  for needle in ('iface_selection_item.AddToSelection()', 'keyboard.send_keys("^+f")',
                 'keyboard.send_keys("Alpha")',
                 'has_keyboard_focus()', 'ViewGroupByTypeItem',
                 'keyboard.send_keys("{ENTER}")','PX10_GUI_GROUP_TWO_SELECTED=PASS',
                 'PX10_GUI_GROUPED_FILE_FOCUSABLE=PASS',
                 'PX10_GUI_GROUPED_EDITOR_FOCUS=PASS',
                 'PX10_GUI_EXCLUDED_NO_GHOST_SELECTION=PASS',
                 'def no_ghost_selection():',
                 'PX10_GUI_ORIGINAL_FILE_HASHES_UNCHANGED=PASS'):
   self.assertIn(needle,p)
  for unsafe in ("ImageGrab","ClearClipboard","SetFileAttributesW","os.system("):
   self.assertNotIn(unsafe,p)
if __name__=="__main__":unittest.main()
