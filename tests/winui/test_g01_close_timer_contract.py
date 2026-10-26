"""Source contract for cancelling queued XAML timers before window teardown.

This is a focused guard against reintroducing active drag/visual callbacks
after close. Native compilation and real Release close are separate gates.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "app" / "winui" / "MainWindow.xaml.cpp"
HARNESS = ROOT / "tests" / "winui" / "test_owned_g01_shutdown_gui.py"
TIMERS = (
    "mDetailColumnDragTimer",
    "mFileRowDragTimer",
    "mOwnedSearchVisualTimer",
    "mOwnedShellProviderVisualTimer",
    "mOwnedF05VisualTimer",
    "mOwnedF05VisualGroupTimer",
)


def teardown():
    text = PRODUCT.read_text(encoding="utf-8")
    opening = text.index("void MainWindow::PrepareForClose() noexcept")
    closing = text.index("MainWindow::~MainWindow()", opening)
    return text[opening:closing]


class G01CloseTimerContract(unittest.TestCase):
    def test_each_window_owned_timer_stopped_before_input_site_release(self):
        source = teardown()
        close = source.index("mClosing=true;")
        release = source.index("UpdateDetailColumnInputSite(false)")
        for timer in TIMERS:
            with self.subTest(timer=timer):
                self.assertEqual(
                    source.count(timer + ".Stop();"), 1,
                    f"{timer} must have one close-path Stop",
                )
                stop = source.index(timer + ".Stop();")
                self.assertLess(close, stop)
                self.assertLess(stop, release)

    def test_drag_state_invalidated_before_timer_stop(self):
        source = teardown()
        initial = source.index("mClosing=true;")
        drag = source.index("mDetailColumnPointerDrag=false;", initial)
        timer = source.index("mDetailColumnDragTimer.Stop();", drag)
        self.assertLess(initial, drag)
        self.assertLess(drag, timer)
        for field, expected in (
            ("mDetailColumnPointerSide", "-1"),
            ("mDetailColumnPointerColumn", "-1"),
            ("mDetailColumnPointerWindowIdentity", "0"),
            ("mDetailColumnPointerPaneTab", "0"),
        ):
            with self.subTest(field=field):
                location = source.index(field + "=" + expected + ";", drag)
                self.assertLess(location, timer)

    def test_idempotent_early_return_survives(self):
        source = teardown()
        self.assertLess(source.index("if(mClosing){"),
                        source.index("mClosing=true;"))
        self.assertIn('TraceG01OwnedClose("PREPARE_CLOSE_ALREADY_CLOSING")',
                      source)
        self.assertLess(
            source.index('TraceG01OwnedClose("QUEUED_XAML_TIMERS_STOPPED")'),
            source.index('TraceG01OwnedClose("CURSOR_HOOKS_STOPPED")'),
        )

    def test_owned_phase_parser_accepts_timer_checkpoint(self):
        self.assertIn(
            '"QUEUED_XAML_TIMERS_STOPPED"',
            HARNESS.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
