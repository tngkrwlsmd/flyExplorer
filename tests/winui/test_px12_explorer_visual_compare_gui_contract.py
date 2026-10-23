"""PX12 narrow visual comparison must protect existing Explorer windows."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(p):return (ROOT/p).read_text(encoding="utf-8-sig")

class Px12VisualComparisonContract(unittest.TestCase):
 def test_dedicated_synthetic_scope(self):
  runner=read("tools/winui/run_checks.py")
  shell=read("tests/winui/test_shell_gui.py")
  probe=read("tests/winui/test_px12_explorer_visual_compare_gui.py")
  for token in ('"address-visual-compare"', 'PX12_VISUAL_PROOF_MISSING_OR_INVALID',
                'OWNED_SYNTHETIC_FIXTURE_REMOVED True'):
   self.assertIn(token,runner)
  for token in ('FLY_PX12_VISUAL_COMPARE_ONLY',
                'from test_px12_explorer_visual_compare_gui import run',
                'AppsUseLightTheme','PX12VisualOwned.txt',
                'PX12_VISUAL_CAPTURE_HARNESS_FINISHED=True'):
   self.assertIn(token,shell)
  for token in ('initial_cabinets=cabinets()', 'cabinets()-initial_cabinets',
                'class_of(explorer_hwnd)=="CabinetWClass"',
                'foreground(explorer_hwnd,explorer_pid)',
                'editor.rectangle().bottom-top+2',
                'assert user.GetDpiForWindow(hwnd)==96',
                'PX12_EXPLORER_MATCHED_COMPARISON_CAPTURE=PASS'):
   self.assertIn(token,probe)
  for token in ('ImageGrab.grab(bbox=area','GetForegroundWindow',
                'GetWindowThreadProcessId','explorer_hwnd not in initial_cabinets'):
   self.assertIn(token,probe)
  for forbidden in ('SetWindowTheme','reg.exe add','taskkill',
                    'explore_proc.kill(', 'os.system('):
   self.assertNotIn(forbidden,probe)

if __name__=="__main__":unittest.main()
