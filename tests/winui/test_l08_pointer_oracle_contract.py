"""Pure-source L08 hover correlation: not a WinUI build or GUI PASS."""
from pathlib import Path
import unittest
from column_resize_source_contract import assert_opt_in_pointer_observer

from l08_pointer_oracle import (
    PointerState, parse_l08_pointer_help, classify_l08_hover,
    classify_l08_cursor_reference,
)
from l08_sendinput_mouse import _normalized_point

ROOT = Path(__file__).resolve().parents[2]
HARNESS = (ROOT / "tests/winui/test_owned_column_resize_gui.py").read_text(
    encoding="utf-8")
PRODUCT = (ROOT / "app/winui/DetailColumnHandle.cpp").read_text(
    encoding="utf-8")
WINDOW = (ROOT / "app/winui/MainWindow.xaml.cpp").read_text(
    encoding="utf-8")
WINDOW_HEADER = (ROOT / "app/winui/MainWindow.xaml.h").read_text(
    encoding="utf-8")
SENDINPUT = (ROOT / "tests/winui/l08_sendinput_mouse.py").read_text(
    encoding="utf-8")


class L08PointerOracleContract(unittest.TestCase):
    def test_exact_owned_format_only(self):
        self.assertEqual(
            parse_l08_pointer_help("L08_enter ENTER=3 EXIT=2 CURSOR_SET=1"),
            PointerState("enter", 3, 2, True),
        )
        for raw in (
            "", "L08_move ENTER=1 EXIT=0 CURSOR_SET=1",
            "L08_enter ENTER=-1 EXIT=0 CURSOR_SET=1",
            "L08_enter ENTER=2 EXIT=0 CURSOR_SET=2",
            "L08_enter ENTER=2 EXIT=0 CURSOR_SET=1 C:\\Users\\secret",
            "<uia-help-error:RuntimeError>",
            "L08_enter ENTER=123456 EXIT=0 CURSOR_SET=1",
            "L08_enter ENTER=1 EXIT=0 CURSOR_SET=1\nprivate",
            "L08_enter ENTER=1 EXIT=0 CURSOR_SET=1" + " " * 200,
            None, 123,
        ):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_l08_pointer_help(raw))

    def test_entered_but_arrow_is_distinct_from_no_event(self):
        baseline = PointerState("exit", 2, 2, True)
        entered = PointerState("enter", 3, 2, True)
        unchanged = PointerState("loaded", 2, 2, True)
        self.assertEqual(
            classify_l08_hover(baseline, entered, "arrow", True),
            "pointer-entered-native-arrow",
        )
        self.assertEqual(
            classify_l08_hover(baseline, entered, "sizewe", True),
            "pointer-entered-native-sizewe",
        )
        self.assertEqual(
            classify_l08_hover(baseline, unchanged, "arrow", True),
            "no-new-pointer-enter-observed",
        )

    def test_exited_thumb_is_not_misreported_as_native_arrow_override(self):
        baseline = PointerState("exit", 2, 2, True)
        left_thumb = PointerState("exit", 3, 3, True)
        reentered = PointerState("enter", 4, 3, True)
        self.assertEqual(
            classify_l08_hover(baseline, left_thumb, "arrow", True),
            "pointer-entered-then-exited",
        )
        self.assertEqual(
            classify_l08_hover(baseline, left_thumb, "sizewe", True),
            "pointer-entered-then-exited",
        )
        self.assertEqual(
            classify_l08_hover(baseline, reentered, "arrow", True),
            "pointer-entered-native-arrow",
        )

    def test_missing_or_stale_data_is_not_called_pointer_failure(self):
        baseline = PointerState("exit", 5, 4, True)
        reset = PointerState("loaded", 0, 0, True)
        no_cursor = PointerState("enter", 6, 4, False)
        self.assertEqual(
            classify_l08_hover(baseline, no_cursor, "arrow", True),
            "protected-cursor-not-set",
        )
        self.assertEqual(
            classify_l08_hover(baseline, reset, "arrow", True),
            "diagnostic-counters-reset",
        )
        self.assertEqual(
            classify_l08_hover(None, no_cursor._replace(cursor_set=True),
                               "arrow", True),
            "prehover-baseline-unavailable",
        )
        self.assertEqual(
            classify_l08_hover(baseline, None, "arrow", True),
            "uia-diagnostic-unavailable",
        )
        self.assertEqual(
            classify_l08_hover(baseline, reset, "sizewe", False),
            "non-owned-or-missed-thumb",
        )

    def test_independent_cursor_reference_is_evidence_only(self):
        self.assertEqual(
            classify_l08_cursor_reference(
                True, "ibeam", ("sizewe", "sizewe", "sizewe")),
            "native-cursor-observations-match",
        )
        self.assertEqual(
            classify_l08_cursor_reference(
                True, "ibeam", ("arrow", "sizewe", "sizewe")),
            "resize-cursor-not-observed-with-valid-reference",
        )
        self.assertEqual(
            classify_l08_cursor_reference(
                True, "arrow", ("arrow", "arrow", "arrow")),
            "cursor-reference-ibeam-not-observed",
        )
        self.assertEqual(
            classify_l08_cursor_reference(
                False, "ibeam", ("arrow", "arrow", "arrow")),
            "cursor-reference-target-unverified",
        )
        for bad in (
            ("ibeam", ("arrow",)),
            ("invalid", ("arrow", "arrow", "arrow")),
            ("ibeam", ("arrow", "arrow", "secret")),
        ):
            self.assertEqual(
                classify_l08_cursor_reference(True, bad[0], bad[1]),
                "cursor-reference-evidence-invalid",
            )
        self.assertEqual(
            classify_l08_cursor_reference(
                1, "ibeam", ("sizewe", "sizewe", "sizewe")),
            "cursor-reference-evidence-invalid",
        )

    def test_os_cursor_reference_is_scoped_to_owned_edit_without_relaxing_gate(self):
        self.assertIn('owned_edit_hit=(getattr(hit,"process_id",None)==proc.pid', HARNESS)
        self.assertIn('getattr(hit,"control_type",None)=="Edit"', HARNESS)
        self.assertIn('search.is_enabled() and owned_foreground()', HARNESS)
        self.assertIn('reference=classify_l08_cursor_reference(', HARNESS)
        self.assertIn('print("L08_CURSOR_REFERENCE_CLASSIFICATION"', HARNESS)
        self.assertIn('assert observed=="sizewe"', HARNESS)

    def test_sendinput_virtual_desktop_mapping(self):
        self.assertEqual(_normalized_point(0, 0, 0, 0, 1280, 768),
                         (0, 0))
        self.assertEqual(_normalized_point(1279, 767, 0, 0, 1280, 768),
                         (65535, 65535))
        self.assertEqual(_normalized_point(-20, -10, -20, -10, 2, 2),
                         (0, 0))
        self.assertEqual(_normalized_point(-19, -9, -20, -10, 2, 2),
                         (65535, 65535))
        for point in (
            (-1, 0, 0, 0, 1280, 768),
            (1280, 0, 0, 0, 1280, 768),
            (0, 768, 0, 0, 1280, 768),
            (0, 0, 0, 0, 1, 768),
            (0, 0, 0, 0, 1280, 1),
            (True, 0, 0, 0, 1280, 768),
            (0.5, 0, 0, 0, 1280, 768),
        ):
            with self.subTest(point=point):
                with self.assertRaises(ValueError):
                    _normalized_point(*point)

    def test_sendinput_is_bounded_and_never_falls_back_to_setcursorpos(self):
        # The failed VM oracle used SetCursorPos; the same-session
        # SendInput intervention delivered PointerEntered and sizewe on all
        # three grips and an I-beam on the independently verified Edit.
        self.assertIn("from l08_sendinput_mouse import sendinput_mouse_move",
                      HARNESS)
        self.assertIn("for step in range(1, 5):", SENDINPUT)
        self.assertIn("user32.SendInput(1, ctypes.byref(move), ctypes.sizeof(move))",
                      SENDINPUT)
        self.assertIn("_MOUSEEVENTF_MOVE | _MOUSEEVENTF_VIRTUALDESK |",
                      SENDINPUT)
        self.assertIn("_MOUSEEVENTF_ABSOLUTE", SENDINPUT)
        self.assertIn('raise ctypes.WinError()', SENDINPUT)
        self.assertNotIn("SetCursorPos(", SENDINPUT)
        self.assertNotIn("mouse.move(coords=", HARNESS)
        self.assertEqual(HARNESS.count("sendinput_mouse_move(coords="), 7)
        self.assertIn("sendinput_mouse_move(coords=(search_x,search_y))",
                      HARNESS)
        self.assertIn('assert observed=="sizewe"', HARNESS)

    def test_staged_hover_crosses_thumb_before_observation(self):
        # UIA element-from-point alone is not a routed WinUI entry event.
        # The owned GUI must advance the system mouse across the actual grip.
        self.assertIn("sendinput_mouse_move(coords=(x-24,y))", HARNESS)
        self.assertIn("for approach_x in (x-12,x-6,x):", HARNESS)
        self.assertIn("sendinput_mouse_move(coords=(approach_x,y))", HARNESS)
        self.assertIn('assert owned_foreground(), "approach left owned window"', HARNESS)
        self.assertLess(
            HARNESS.index("sendinput_mouse_move(coords=(x-24,y))"),
            HARNESS.index("pointer_before=pointer_snapshot()"),
        )
        self.assertLess(
            HARNESS.index("pointer_before=pointer_snapshot()"),
            HARNESS.index("for approach_x in (x-12,x-6,x):"),
        )
        self.assertIn('assert observed=="sizewe"', HARNESS)

    def test_root_pointer_move_diagnostic_is_opt_in_and_correlated(self):
        # A missing thumb PointerEntered alone cannot classify WinUI input.
        # The unchanged native cursor oracle must remain a separate gate.
        self.assertIn("mL08RootPointerMoves=0;", WINDOW_HEADER)
        assert_opt_in_pointer_observer(self, WINDOW)
        self.assertIn('L" rootMove="+std::to_wstring(ui->mL08RootPointerMoves)', WINDOW)
        self.assertIn('root_move_before=routed_root_moves()', HARNESS)
        self.assertIn('root_move_after=routed_root_moves()', HARNESS)
        self.assertIn('print("L08_ROOT_POINTER_MOVE"', HARNESS)
        self.assertIn('assert observed=="sizewe"', HARNESS)
        self.assertNotIn('assert root_move_delta', HARNESS)

    def test_each_dwell_has_its_own_event_cursor_classification(self):
        self.assertIn("dwell_boundary=classify_l08_hover(", HARNESS)
        self.assertIn('"BOUNDARY",dwell_boundary', HARNESS)
        self.assertIn('assert observed=="sizewe"', HARNESS)

    def test_integration_does_not_relax_existing_acceptance(self):
        for expected in (
            'from l08_pointer_oracle import parse_l08_pointer_help, '
            'classify_l08_hover',
            "pointer_before=pointer_snapshot()",
            "pointer_after=pointer_snapshot()",
            'print("L08_POINTER_BOUNDARY"',
            'assert observed=="sizewe"',
            'assert owned_hit[0]==thumb_id',
            'env["FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC"]="1"',
        ):
            self.assertIn(expected, HARNESS)
        self.assertNotIn(
            'print("L08_POINTER_EVENT_HELP",thumb_id,raw', HARNESS)
        self.assertIn('PointerEntered([this]', PRODUCT)
        self.assertIn('PointerExited([this]', PRODUCT)
        self.assertIn('ProtectedCursor(Microsoft::UI::Input::InputSystemCursor',
                      PRODUCT)


if __name__ == "__main__":
    unittest.main()
