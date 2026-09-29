"""Static scoped safety for the manual WinUI and Explorer clipboard probe."""
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
class ManualInteropContracts(unittest.TestCase):
 def test_four_directions_and_no_automatic_clipboard_mutation(self):
  text=(HERE/"manual_owned_clipboard_probe.py").read_text(encoding="utf-8")
  for token in ("winui_copy_to_explorer","explorer_copy_to_winui",
                "winui_cut_to_explorer","explorer_cut_to_winui",
                "stdin.isatty()","if not clipboard_empty()",
                "EXISTING_CLIPBOARD_FORMAT_COUNT",
                "preview=subprocess.Popen",
                "LEGACY_PRESENT_SETTINGS_UNCHANGED"):
   self.assertIn(token,text)
  for forbidden in ("EmptyClipboard(", "SetClipboardData(", "clipboard.GetClipboardData("):
   self.assertNotIn(forbidden,text)
 def test_global_clipboard_stays_outside_automatic_m23_gui(self):
  gui=(HERE/"test_m23_gui.py").read_text(encoding="utf-8")
  self.assertNotIn("shellclipboard::write",gui)
  self.assertNotIn("EmptyClipboard(",gui)
if __name__=="__main__":unittest.main()
