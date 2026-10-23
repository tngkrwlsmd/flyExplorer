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

    def test_owned_handle_event_instrumentation_is_diagnostic_only(self):
        header=(ROOT/"app/winui/DetailColumnHandle.h").read_text("utf-8")
        cpp=(ROOT/"app/winui/DetailColumnHandle.cpp").read_text("utf-8")
        gui=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text("utf-8")
        self.assertIn("mCursorDiagnosticEnabled=false;",header)
        self.assertIn("winrt::hstring(value.c_str())",cpp)
        self.assertIn("get_strong().as<Microsoft::UI::Xaml::DependencyObject>()",cpp)
        self.assertNotIn("this->as<Microsoft::UI::Xaml::DependencyObject>()",cpp)
        self.assertNotIn("winrt::hstring{value}",cpp)
        self.assertIn("FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC",cpp)
        self.assertIn("if(mCursorDiagnosticEnabled){",cpp)
        for marker in ("PointerEntered([this]", "PointerExited([this]",
                       "mCursorDiagnosticLoaded=true;",
                       "ProtectedCursor(Microsoft::UI::Input::InputSystemCursor::Create(",
                       "ProtectedCursor()?1:0", "AutomationProperties::SetHelpText("):
            self.assertIn(marker,cpp)
        for marker in ("def handle_diagnostic(auto_id):", "peer.CurrentHelpText",
                       "L08_HANDLE_INITIAL", "L08_HANDLE_AFTER_EXIT",
                       "HANDLE_STATE", "L08_LOAD=1 "):
            self.assertIn(marker,gui)
        self.assertLess(cpp.index("if(mCursorDiagnosticEnabled){"),
                        cpp.index("PointerEntered([this]"))

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
