"""Synthetic visual-comparison contract for unequal real window geometry."""
from pathlib import Path
import json
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from PIL import Image


class IndexedVisualComparatorContract(unittest.TestCase):
    def test_unequal_height_is_reported_without_suppressing_pixel_review(self):
        with TemporaryDirectory() as folder:
            folder = Path(folder)
            before = folder / "before.bmp"
            after = folder / "after.bmp"
            report = folder / "report.json"
            Image.new("RGB", (100, 70), (20, 35, 50)).save(before)
            Image.new("RGB", (100, 60), (21, 35, 50)).save(after)
            script = Path(__file__).with_name("indexed_search_visual_compare.py")
            done = subprocess.run(
                [sys.executable, "-X", "utf8", str(script),
                 "--before", str(before), "--after", str(after),
                 "--metadata", str(report)],
                text=True, capture_output=True, timeout=15,
            )
            self.assertEqual(0, done.returncode, (done.stdout, done.stderr))
            output = json.loads(report.read_text(encoding="utf-8"))
            self.assertFalse(output["geometry_matched"])
            self.assertEqual([100, 70], output["before_size"])
            self.assertEqual([100, 60], output["after_size"])
            self.assertEqual(-10, output["height_delta"])
            self.assertEqual(1000, output["nonoverlapping_extent_pixels"])
            self.assertEqual(6000, output["changed_pixels_in_common"])
            self.assertIn("INDEXED_VISUAL_BEFORE_PREVIEW_BEGIN", done.stdout)
            self.assertIn("INDEXED_VISUAL_AFTER_PREVIEW_BEGIN", done.stdout)
            self.assertIn("INDEXED_VISUAL_COMPARISON_CAPTURED=PASS", done.stdout)

    def test_equal_images_do_not_claim_diff(self):
        with TemporaryDirectory() as folder:
            folder = Path(folder)
            before = folder / "a.bmp"
            after = folder / "b.bmp"
            report = folder / "report.json"
            Image.new("RGB", (30, 30), (0, 0, 0)).save(before)
            after.write_bytes(before.read_bytes())
            script = Path(__file__).with_name("indexed_search_visual_compare.py")
            done = subprocess.run(
                [sys.executable, "-X", "utf8", str(script),
                 "--before", str(before), "--after", str(after),
                 "--metadata", str(report)],
                text=True, capture_output=True, timeout=15,
            )
            self.assertNotEqual(0, done.returncode)
            self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
