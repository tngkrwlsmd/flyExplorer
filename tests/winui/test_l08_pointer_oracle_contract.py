"""Pure-source L08 hover correlation: not a WinUI build or GUI PASS."""
from pathlib import Path
import unittest

from l08_pointer_oracle import (
    PointerState, parse_l08_pointer_help, classify_l08_hover,
)

ROOT = Path(__file__).resolve().parents[2]
HARNESS = (ROOT / "tests/winui/test_owned_column_resize_gui.py").read_text(
    encoding="utf-8")
PRODUCT = (ROOT / "app/winui/DetailColumnHandle.cpp").read_text(
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
