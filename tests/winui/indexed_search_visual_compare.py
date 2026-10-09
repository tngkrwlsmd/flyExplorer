"""Bounded pixel comparison and review previews for test-owned indexed Search UI."""
from __future__ import annotations

import argparse
import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageChops

MAX_BMP = 10 * 1024 * 1024
MAX_SIDE = 2200
MAX_PIXELS = 2200 * 1600


def read_capture(path: Path) -> tuple[Image.Image, str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing or linked capture")
    raw = path.read_bytes()
    if not raw.startswith(b"BM") or len(raw) > MAX_BMP:
        raise ValueError("not a bounded app-owned BMP")
    with Image.open(BytesIO(raw)) as bmp:
        bmp.load()
        if (
            bmp.width <= 0 or bmp.height <= 0
            or max(bmp.size) > MAX_SIDE
            or bmp.width * bmp.height > MAX_PIXELS
        ):
            raise ValueError("out of range screenshot geometry")
        image = bmp.convert("RGB")
    return image, hashlib.sha256(raw).hexdigest()


def print_preview(label: str, image: Image.Image) -> None:
    max_width = 960
    if image.width > max_width:
        height = max(1, image.height * max_width // image.width)
        image = image.resize((max_width, height), Image.Resampling.LANCZOS)
    preview = image.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    output = BytesIO()
    preview.save(output, format="PNG", optimize=True)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    if len(encoded) > 240_000:
        raise ValueError("visual preview exceeds log budget")
    print(f"INDEXED_VISUAL_{label}_PREVIEW_BEGIN", flush=True)
    for offset in range(0, len(encoded), 2500):
        print(f"INDEXED_VISUAL_{label}_B64={encoded[offset:offset+2500]}", flush=True)
    print(f"INDEXED_VISUAL_{label}_PREVIEW_END", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    before, before_sha = read_capture(args.before)
    after, after_sha = read_capture(args.after)
    # Different window extents can be a real layout regression (for example
    # a wrapped subtitle). Report the difference rather than rejecting the
    # evidence or cropping a row that may contain a clipped control.
    common = (min(before.width, after.width), min(before.height, after.height))
    diff = ImageChops.difference(
        before.crop((0, 0, *common)),
        after.crop((0, 0, *common)),
    )
    region = diff.getbbox()
    changed_in_common = sum(1 for p in diff.getdata() if p != (0, 0, 0))
    outside_common = (
        before.width * before.height + after.width * after.height
        - 2 * common[0] * common[1]
    )
    changed_pixels = changed_in_common + outside_common
    if changed_pixels == 0:
        raise ValueError("no composited pixel change found; inspect captures")
    report = {
        "schema": 1,
        "source": "app-owned RenderTargetBitmap; matched dark UI and test-owned fixture",
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "before_size": [before.width, before.height],
        "after_size": [after.width, after.height],
        "geometry_matched": before.size == after.size,
        "height_delta": after.height - before.height,
        "width_delta": after.width - before.width,
        "common_overlap_size": list(common),
        "overlap_difference_bounds": list(region) if region else None,
        "changed_pixels_in_common": changed_in_common,
        "nonoverlapping_extent_pixels": outside_common,
        "changed_pixels_total": changed_pixels,
        "changed_ratio": round(
            changed_pixels / max(before.width * before.height,
                                 after.width * after.height), 6
        ),
        "note": (
            "Geometry differences remain a manual visual-review gate. "
            "Automated pixel deltas alone do not imply acceptance."
        ),
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print("INDEXED_VISUAL_PIXEL_REPORT=" + json.dumps(report, sort_keys=True), flush=True)
    print_preview("BEFORE", before)
    print_preview("AFTER", after)
    print("INDEXED_VISUAL_COMPARISON_CAPTURED=PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
