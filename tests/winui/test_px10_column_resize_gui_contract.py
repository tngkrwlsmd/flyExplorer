"""PX10 bounded real-pointer columns and per-workspace geometry."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/winui"))
import run_checks


class PX10ColumnResizeGuiContract(unittest.TestCase):
    def test_dedicated_area_without_unrelated_gui_flags(self):
        cmd,env,limit=run_checks.gui_command("column-resize","Release",{})
        self.assertEqual(Path(cmd[-2]).name,"test_owned_column_resize_gui.py")
        self.assertEqual(cmd[-1],"Release")
        self.assertLessEqual(limit,150)
        self.assertNotIn("FLY_G01_INTEGRATED_STARTUP_ONLY",env)

    def test_real_pointer_workspace_and_normal_close_guards(self):
        source=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text("utf-8")
        for fragment in ('mouse.press(button="left"',
                         'mouse.move(coords=(nx,y))',
                         'L08_HOVER_TIMELINE',
                         'for wait_ms in (70,180,350)',
                         'mouse.move(coords=(body.left+30,body.top+36))',
                         'observed=="sizewe"',
                         'assert owned_hit[0]==thumb_id',
                         'assert observed=="sizewe"',
                         'element(next_header_id).rectangle().left>=start+12',
                         'keyboard.send_keys("^t")',
                         'len(tabs())==2',
                         'OWNED_DETAIL_COLUMN_WINDOW_TAB_RESTORED',
                         'PostMessageW(hwnd,0x10,0,0)',
                         'OWNED_DETAIL_COLUMN_EXIT',
                         'proc.returncode==0',
                         'SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL',
                         'OWNED_COLUMN_RESIZE_FIXTURE_REMOVED'):
            self.assertTrue(fragment in source,fragment)
        self.assertNotIn('eventually(horizontal_resize_cursor,',source)

    def test_g01_close_probe_is_bounded_owned_and_preserves_first_error(self):
        source=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text("utf-8")
        for fragment in (
            'G01_OWNED_WM_CLOSE_POSTED',
            'G01_OWNED_WM_CLOSE_TIMELINE',
            'G01_OWNED_WM_CLOSE_EXIT_MS',
            'GetWindowThreadProcessId',
            'process_id.value!=proc.pid',
            'SendMessageTimeoutW',
            'hwnd,0,0,0,0x0003,200',
            'for deadline in (.25,1.0,3.0,7.0,13.0):',
            'OWNED_DETAIL_COLUMN_CLOSE_TIMEOUT',
            'if close_timed_out and sys.exc_info()[0] is None:',
            'SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL',
            'assert observed=="sizewe"',
            'proc.terminate();proc.wait(timeout=5)',
        ):
            self.assertIn(fragment,source,fragment)
        # Do not quietly enlarge the existing 13-second normal-close budget.
        self.assertNotIn('proc.wait(timeout=30)',source)

    def test_existing_runner_requires_the_original_independent_resize_oracles(self):
        source=(ROOT/"tools/winui/run_checks.py").read_text("utf-8")
        section=source.split('if not rc and area == "column-resize":',1)[1].split(
            'return fail("GUI_ACCEPTANCE_FAILURE", rc) if rc else 0',1)[0]
        for fragment in ('OWNED_DETAIL_COLUMN_RESULT PASS',
                         'OWNED_DETAIL_COLUMN_NAME_RESIZE True',
                         'OWNED_DETAIL_COLUMN_TYPE_RESIZE True',
                         'OWNED_DETAIL_COLUMN_SIZE_RESIZE True',
                         'PX10_COLUMN_RAPID_TAIL_COMMITTED=True',
                         'OWNED_DETAIL_COLUMN_WINDOW_TAB_RESTORED True',
                         'OWNED_DETAIL_COLUMN_EXIT 0',
                         'SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL True',
                         'OWNED_COLUMN_RESIZE_FIXTURE_REMOVED True',
                         'Traceback (most recent call last)'):
            self.assertIn(fragment,section)


if __name__=="__main__":unittest.main()
