"""Pure regression checks for visual evidence geometry and image comparison."""
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from PIL import Image

from visual_ui_probe import Rect, ScrollInfo, drag_points, compare, bright_neutral_ratio, capture


class VisualProbeTests(unittest.TestCase):
    def test_capture_includes_owned_layered_scrollbar_windows(self):
        with patch("PIL.ImageGrab.grab") as grab:
            capture((0, 0, 8, 8), "layered-test.png")
            grab.assert_called_once_with(
                bbox=(0, 0, 8, 8), include_layered_windows=True)
            grab.return_value.save.assert_called_once_with(
                "layered-test.png")

    def test_vertical_scrollbar_drag_stays_on_track(self):
        s = ScrollInfo()
        s.rcScrollBar = Rect(100, 200, 118, 600)
        s.dxyLineButton = 18
        s.xyThumbTop, s.xyThumbBottom = 20, 60
        start, end = drag_points(s, True)
        self.assertEqual(start, (109, 240))
        self.assertGreater(end[1], start[1])
        self.assertLessEqual(end[1], 582)

    def test_horizontal_scrollbar_reverses_near_end(self):
        s = ScrollInfo()
        s.rcScrollBar = Rect(100, 200, 400, 218)
        s.dxyLineButton = 18
        s.xyThumbTop, s.xyThumbBottom = 245, 265
        start, end = drag_points(s, False)
        self.assertEqual(start, (355, 209))
        self.assertLess(end[0], start[0])

    def test_invalid_scrollbar_geometry_rejected(self):
        s = ScrollInfo()
        s.rcScrollBar = Rect(0, 0, 12, 12)
        s.dxyLineButton = 8
        s.xyThumbTop, s.xyThumbBottom = 1, 4
        with self.assertRaises(ValueError):
            drag_points(s, True)

    def test_equal_images_are_not_visual_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            Image.new("RGB", (4, 4), (0, 0, 0)).save(p / "a.png")
            result = compare(p / "a.png", p / "a.png", p / "diff.png", 12)
            self.assertEqual(result["status"], "NO_DIFFERENCE_NOT_VISUAL_PASS")

    def test_changed_images_are_review_only(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            Image.new("RGB", (4, 4), (0, 0, 0)).save(p / "a.png")
            Image.new("RGB", (4, 4), (255, 255, 255)).save(p / "b.png")
            result = compare(p / "a.png", p / "b.png", p / "diff.png", 12)
            self.assertEqual(result["changed_pixels"], 16)
            self.assertEqual(result["status"], "REVIEW_REQUIRED")

    def test_bright_neutral_detection(self):
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "frame.png"
            Image.new("RGB", (4, 4), (230, 229, 228)).save(image)
            self.assertEqual(bright_neutral_ratio(image, (0, 0, 4, 4)), 1.0)
            self.assertEqual(bright_neutral_ratio(image, (-3, -2, 4, 4)), 1.0)

    def test_brightness_invalid_roi_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "frame.png"
            Image.new("RGB", (4, 4), (0, 0, 0)).save(image)
            with self.assertRaises(ValueError):
                bright_neutral_ratio(image, (8, 8, 9, 9))

    def test_misaligned_dimensions_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            Image.new("RGB", (4, 4)).save(p / "a.png")
            Image.new("RGB", (5, 4)).save(p / "b.png")
            with self.assertRaises(ValueError):
                compare(p / "a.png", p / "b.png", p / "diff.png", 12)


if __name__ == "__main__":
    unittest.main()
