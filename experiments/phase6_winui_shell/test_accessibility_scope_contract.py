"""Actual-scope labeling: current OS settings, not fake 125% DPI/Narrator."""
from pathlib import Path
import unittest
S=(Path(__file__).resolve().parent/"test_owned_accessibility_layout_gui.py").read_text(encoding="utf-8")
class AccessScope(unittest.TestCase):
 def test_does_not_modify_global_accessibility_settings(self):
  for x in ("GetDpiForWindow","SystemParametersInfoW(0x0042",
            "NOT_VERIFIED_ALTERNATE_DPI_HC_ON_NARRATOR_KOREAN_IME",
            "ORIGINAL_SIX_USER_SETTINGS_IDENTICAL",
            "keyboard.send_keys","SetWindowPos(hwnd"):
   self.assertIn(x,S)
  for x in ("SPI_SETHIGHCONTRAST","SystemParametersInfoW(0x0043",
            "ChangeDisplaySettingsEx","winreg.SetValue","Narrator.exe"):
   self.assertNotIn(x,S)
if __name__=="__main__":unittest.main()
