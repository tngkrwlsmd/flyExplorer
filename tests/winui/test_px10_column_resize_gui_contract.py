"""PX10 bounded real-pointer columns and per-workspace geometry."""
from pathlib import Path
import ast
import re
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
            'posted=bool(user32.PostMessageW',
            'user32=ctypes.windll.user32',
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
        # A failed/vanished close HWND must never mask an earlier GUI failure.
        self.assertNotIn('assert user32.PostMessageW(',source)
        self.assertNotIn('assert owned_shutdown_state()[0]',source)

    def test_g01_owned_native_close_phases_are_opt_in_and_bounded(self):
        cpp=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text("utf-8")
        gui=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text("utf-8")
        for fragment in (
            'FLY_G01_OWNED_CLOSE_TRACE',
            'columns-gui-owned-',
            'TraceG01OwnedClose("APPWINDOW_CLOSING_ENTER")',
            'TraceG01OwnedClose("APPWINDOW_CLOSING_EXIT")',
            'TraceG01OwnedClose("WINDOW_CLOSED_ENTER")',
            'TraceG01OwnedClose("WINDOW_CLOSED_EXIT")',
            'TraceG01OwnedClose("FOCUS_TRANSFER_BEGIN")',
            'TraceG01OwnedClose("FOCUS_TRANSFER_DONE")',
            'G01OwnedCloseTraceEnabled()',
            'GetFocusedElement(RootShell().XamlRoot())',
            'const bool changed=NewTabButton().Focus(',
            'FOCUS_TRANSFER_SUCCEEDED',
            'FOCUS_TRANSFER_REJECTED',
            'FOCUS_BEFORE_TEXT_INPUT',
            'FOCUS_AFTER_TEXT_INPUT',
            'TraceG01OwnedClose("SHELL_NAV_SHUTDOWN_DONE")',
            'TraceG01OwnedClose("PREPARE_CLOSE_EXIT")',
            'TraceG01OwnedClose("MAINWINDOW_DESTRUCTOR_EXIT")',
            'FILE_APPEND_DATA',
            'FILE_FLAG_WRITE_THROUGH',
        ):
            self.assertIn(fragment,cpp,fragment)
        for fragment in (
            'env["FLY_G01_OWNED_CLOSE_TRACE"]="YES"',
            'trace_files=(owned/"tmp"/trace_name,owned/"temp"/trace_name)',
            'trace.stat().st_size>4096',
            'len(lines)>64',
            'allowed_close_phases',
            'G01_OWNED_CLOSE_PHASE_TRACE',
            'FOCUS_BEFORE_TEXT_INPUT',
            'FOCUS_AFTER_TEXT_INPUT',
            'FOCUS_TRANSFER_SUCCEEDED',
            'FOCUS_TRANSFER_REJECTED',
            'G01_OWNED_CLOSE_PHASE_TRACE_MISSING',
            'G01_OWNED_CLOSE_PHASE_TRACE_INVALID',
            'reason=("phase-count-exceeded" if len(lines)>64',
            'else "unrecognized-phase")',
            '"REASON",reason,flush=True)',
            'SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL',
            'assert observed=="sizewe"',
        ):
            self.assertIn(fragment,gui,fragment)
        self.assertNotIn('SetUnhandledExceptionFilter',cpp)
        self.assertNotIn('MiniDumpWriteDump',cpp)

    def test_owned_close_phase_allowlist_covers_emitted_normal_phases(self):
        # Read the actual Python set rather than hard-code another copied list.
        # A newly emitted native phase must not silently invalidate every
        # test-owned close trace and conceal the shutdown chronology.
        cpp=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text("utf-8")
        app=(ROOT/"app/winui/App.xaml.cpp").read_text("utf-8")
        gui=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text(
            "utf-8")
        assignments=[
            node for node in ast.walk(ast.parse(gui))
            if isinstance(node,ast.Assign) and any(
                isinstance(target,ast.Name) and
                target.id=="allowed_close_phases"
                for target in node.targets)
        ]
        self.assertEqual(len(assignments),1)
        phases=ast.literal_eval(assignments[0].value)
        self.assertIsInstance(phases,set)
        emitted=set(re.findall(
            r'TraceG01OwnedClose\(\s*"([A-Z_]+)"\s*\)',cpp))
        # The App destructor stages pass through TraceG01AppLifecycle(stage)
        # into the same owned trace. Unhandled-exception markers are not
        # ordinary close stages and must remain outside this normal-close
        # acceptance contract.
        app_destructor=app.split("\n    App::~App()\n",1)[1].split(
            "void App::OnLaunched",1)[0]
        emitted.update(re.findall(
            r'TraceG01AppLifecycle\(\s*"([A-Z_]+)"\s*\)',
            app_destructor))
        self.assertIn("QUEUED_XAML_TIMERS_STOPPED",emitted)
        self.assertFalse(emitted-phases,
                         "Native close phases missing from GUI allowlist")
        self.assertIn('len(lines)>64',gui)
        self.assertIn('trace.stat().st_size>4096',gui)
        self.assertIn('"REASON",reason,flush=True)',gui)

    def test_g01_app_window_member_release_boundary_is_trace_only(self):
        app_h=(ROOT/"app/winui/App.xaml.h").read_text("utf-8")
        app_cpp=(ROOT/"app/winui/App.xaml.cpp").read_text("utf-8")
        window_cpp=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text("utf-8")
        gui=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text("utf-8")
        for fragment in (
            '~App();',
            'winrt::Microsoft::UI::Xaml::Window window{ nullptr };',
        ):
            self.assertIn(fragment,app_h)
        for fragment in (
            'App::~App()',
            'TraceG01AppLifecycle("APP_DESTRUCTOR_ENTER")',
            'TraceG01AppLifecycle("APP_DESTRUCTOR_BODY_EXIT")',
        ):
            self.assertIn(fragment,app_cpp)
        self.assertIn('void TraceG01AppLifecycle(char const* stage) noexcept',
                      window_cpp)
        self.assertIn('TraceG01OwnedClose(stage);',window_cpp)
        for token in ('APP_DESTRUCTOR_ENTER','APP_DESTRUCTOR_BODY_EXIT'):
            self.assertIn(token,gui)
        # Not a product lifecycle workaround; no manual release in destructor.
        self.assertNotIn('window = nullptr;',app_cpp)
        self.assertNotIn('window.Close()',app_cpp)

    def test_g01_exact_fault_observer_survives_window_member_release(self):
        app_h=(ROOT/"app/winui/App.xaml.h").read_text("utf-8")
        app=(ROOT/"app/winui/App.xaml.cpp").read_text("utf-8")
        gui=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text(
            "utf-8")
        self.assertLess(
            app_h.index("mG01NativeExceptionSubscription{};"),
            app_h.index("Window window{ nullptr };"),
        )
        self.assertIn("~G01OwnedNativeExceptionSubscription() noexcept;",app_h)
        self.assertIn("~G01OwnedNativeExceptionSubscription() noexcept",app)
        self.assertIn("::RemoveVectoredExceptionHandler(handle);",app)
        self.assertNotIn(
            "RemoveVectoredExceptionHandler",
            app.split("\n    App::~App()\n",1)[1].split(
                "void App::OnLaunched",1)[0],
        )
        # The handler is only installed under the existing owned fixture.
        self.assertIn("if(G01OwnedAppDiagnosticsEnabled())",app)
        self.assertIn("AddVectoredExceptionHandler",app)
        self.assertIn("code == 0xC0000005",app)
        self.assertIn('originRva != 0xAB04Bull',app)
        self.assertIn("NATIVE_CLOSE_AV_ENTER",app)
        self.assertIn("NATIVE_CLOSE_AV_EXIT",app)
        self.assertIn("EXCEPTION_CONTINUE_SEARCH",app)
        for unsafe in ("MiniDumpWriteDump","SetUnhandledExceptionFilter"):
            self.assertNotIn(unsafe,app)
        # Native stack telemetry must remain a bounded redacted envelope.
        self.assertIn("index < 8 && frame.Rip",app)
        self.assertIn('"FLY"',app)
        self.assertIn('"XAML"',app)
        self.assertIn('"OTHER"',app)
        self.assertIn("rva <= 0xFFFFFFFFull",app)
        assignments=[
            node for node in ast.walk(ast.parse(gui))
            if isinstance(node,ast.Assign) and any(
                isinstance(target,ast.Name) and
                target.id=="native_close_frame" for target in node.targets)
        ]
        self.assertEqual(len(assignments),1)
        pattern=re.compile(ast.literal_eval(assignments[0].value.args[0]))
        self.assertIsNotNone(
            pattern.fullmatch("NATIVE_CLOSE_AV_FRAME_00_XAML_000AB04B"))
        for invalid in (
            "NATIVE_CLOSE_AV_FRAME_08_XAML_000AB04B",
            "NATIVE_CLOSE_AV_FRAME_00_PERSONAL_000AB04B",
            "NATIVE_CLOSE_AV_FRAME_00_XAML_123456789",
            "NATIVE_CLOSE_AV_FRAME_00_XAML_000AB04B\\nsecret",
            "NATIVE_CLOSE_AV_FRAME_00_XAML_000AB04B C:\\\\User",
        ):
            self.assertIsNone(pattern.fullmatch(invalid))
        self.assertIn("native_close_frame.fullmatch(line) is None",gui)
        self.assertIn('"NATIVE_CLOSE_AV_ENTER","NATIVE_CLOSE_AV_EXIT"',gui)
        self.assertIn("len(lines)>64",gui)
        self.assertIn("trace.stat().st_size>4096",gui)

    def test_all_realized_tooltips_detach_before_xaml_close(self):
        # Native shutdown AV stack: ToolTip::~ToolTip -> island root access.
        # Teardown is bounded and runs only during ordinary window close.
        cpp=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text("utf-8")
        gui=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text(
            "utf-8")
        close=cpp.split(
            "void MainWindow::PrepareXamlForClose() noexcept",1)[1].split(
            "void MainWindow::PrepareForClose() noexcept",1)[0]
        self.assertIn("constexpr std::size_t kMaxCloseTooltipNodes=8192;",close)
        self.assertIn("nodes.push_back(RootShell());",close)
        self.assertIn("VisualTreeHelper::GetChildrenCount",close)
        self.assertIn("VisualTreeHelper::GetChild",close)
        self.assertIn("ToolTipService::GetToolTip(*node)",close)
        self.assertIn("ToolTipService::SetToolTip(",close)
        self.assertIn(
            "*node,winrt::Windows::Foundation::IInspectable{nullptr});",
            close)
        self.assertIn("nodes.rbegin()",close)
        self.assertLess(close.index("VISUAL_TOOLTIP_SWEEP_RELEASED"),
                        close.index("NewTabButton().Focus("))
        for marker in (
            "VISUAL_TOOLTIP_SWEEP_RELEASED",
            "VISUAL_TOOLTIP_SWEEP_EMPTY",
            "VISUAL_TOOLTIP_SWEEP_LIMIT",
            "VISUAL_TOOLTIP_SWEEP_EXCEPTION",
        ):
            self.assertIn('TraceG01OwnedClose(',close)
            self.assertIn('"'+marker+'"',close)
            self.assertIn('"'+marker+'"',gui)
        self.assertNotIn("MiniDumpWriteDump",close)
        self.assertIn('assert observed=="sizewe"',gui)

    def test_close_focus_target_tooltip_detaches_before_focus(self):
        cpp=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text("utf-8")
        xaml=(ROOT/"app/winui/MainWindow.xaml").read_text("utf-8")
        gui=(ROOT/"tests/winui/test_owned_column_resize_gui.py").read_text(
            "utf-8")
        close=cpp.split(
            "void MainWindow::PrepareXamlForClose() noexcept",1)[1].split(
            "void MainWindow::PrepareForClose() noexcept",1)[0]
        self.assertIn('x:Name="NewTabButton"',xaml)
        tag=xaml.split('x:Name="NewTabButton"',1)[1].split('</Button>',1)[0]
        self.assertIn('ToolTipService.ToolTip=',tag)
        self.assertIn("ToolTipService::SetToolTip(",close)
        self.assertIn(
            "NewTabButton(),winrt::Windows::Foundation::IInspectable{nullptr});",close)
        self.assertLess(close.index('ToolTipService::SetToolTip('),
                        close.index('NewTabButton().Focus('))
        self.assertIn('TraceG01OwnedClose("FOCUS_TARGET_TOOLTIP_DETACHED")',
                      close)
        self.assertIn(
            'TraceG01OwnedClose("FOCUS_TARGET_TOOLTIP_DETACH_EXCEPTION")',
            close)
        self.assertIn('"FOCUS_TARGET_TOOLTIP_DETACHED"',gui)
        self.assertIn('"FOCUS_TARGET_TOOLTIP_DETACH_EXCEPTION"',gui)
        self.assertIn('NewTabButton().Focus(FocusState::Programmatic)',close)
        # Do not clear all tooltips or dispose the window manually.
        self.assertNotIn('window = nullptr;',cpp)
        self.assertNotIn('ToolTipService::SetToolTip(RootShell()',close)

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
