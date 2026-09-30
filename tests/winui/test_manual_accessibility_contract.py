"""Avoid fake DPI/Narrator claims, alter no global user settings."""
import unittest
from pathlib import Path
BODY=(Path(__file__).resolve().parent/"manual_accessibility_matrix.py").read_text(encoding="utf-8")
class ManualOSMatrix(unittest.TestCase):
 def test_real_dpi_and_contrast_verified_before_human_ack(self):
  for token in ("--expected-scale","--contrast","GetDpiForWindow",
                "current_hc()","sys.stdin.isatty()",
                "Type YES only after real Narrator + IME checks",
                "typed==korean+chr(0xC785)+chr(0xB825)"):
   self.assertIn(token,BODY)
  for forbidden in ("SPI_SETHIGHCONTRAST","ChangeDisplaySettingsEx",
                    "SetProcessDpiAwarenessContext","Narrator.exe"):
   self.assertNotIn(forbidden,BODY)
if __name__=="__main__":unittest.main()
