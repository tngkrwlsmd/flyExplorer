"""Collect native flyExplorer scrollbar/other UI screenshots for review.

Capture requires an existing isolated test profile with synthetic file names.
Never infer visual PASS from pixel equality or capture success.
"""
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent

class Rect(ctypes.Structure):
    _fields_ = [(k, wintypes.LONG) for k in ("left", "top", "right", "bottom")]

class ScrollInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD), ("rcScrollBar", Rect),
        ("dxyLineButton", ctypes.c_int), ("xyThumbTop", ctypes.c_int),
        ("xyThumbBottom", ctypes.c_int), ("reserved", ctypes.c_int),
        ("rgstate", wintypes.DWORD * 6),
    ]

def rect_of(hwnd):
    u = ctypes.windll.user32
    u.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(Rect))
    r = Rect()
    if not u.GetWindowRect(hwnd, ctypes.byref(r)):
        raise RuntimeError("GetWindowRect failed")
    return (r.left, r.top, r.right, r.bottom)

def find_hwnd(exe, child_class=None, window_title=None):
    import psutil
    u = ctypes.windll.user32
    cb_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    matches = []
    u.IsWindowVisible.argtypes = (wintypes.HWND,)
    u.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    u.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    u.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    @cb_type
    def visit(hwnd, unused):
        if not u.IsWindowVisible(hwnd):
            return True
        if child_class:
            name = ctypes.create_unicode_buffer(128)
            u.GetClassNameW(hwnd, name, len(name))
            if name.value == child_class:
                matches.append(int(hwnd))
        else:
            # Each final-pixel scrollbar is its own nonactivating owned popup,
            # not an independent flyExplorer main window.
            cls = ctypes.create_unicode_buffer(128)
            u.GetClassNameW(hwnd, cls, len(cls))
            if cls.value == "flyExplorer.DarkScrollbarOverlay.v1":
                return True
            pid = wintypes.DWORD()
            u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                if os.path.normcase(psutil.Process(pid.value).exe()) == os.path.normcase(str(exe)):
                    title = ctypes.create_unicode_buffer(512)
                    u.GetWindowTextW(hwnd, title, len(title))
                    if not window_title or window_title.casefold() in title.value.casefold():
                        matches.append(int(hwnd))
            except (psutil.Error, OSError):
                pass
        return True
    if child_class:
        u.EnumChildWindows.argtypes = (wintypes.HWND, cb_type, wintypes.LPARAM)
        u.EnumChildWindows(exe, visit, 0)  # exe parameter is parent HWND in this mode
    else:
        u.EnumWindows.argtypes = (cb_type, wintypes.LPARAM)
        u.EnumWindows(visit, 0)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one visible window/control; found {len(matches)}")
    return matches[0]

def scrollbar(hwnd, vertical):
    u = ctypes.windll.user32
    u.GetScrollBarInfo.argtypes = (wintypes.HWND, wintypes.LONG, ctypes.POINTER(ScrollInfo))
    info = ScrollInfo()
    info.cbSize = ctypes.sizeof(info)
    if not u.GetScrollBarInfo(hwnd, -5 if vertical else -6, ctypes.byref(info)):
        raise RuntimeError("GetScrollBarInfo failed")
    if info.rgstate[0] & (0x8000 | 0x10000) or info.xyThumbBottom <= info.xyThumbTop:
        raise RuntimeError("Scrollbar has no visible draggable thumb")
    return info

def drag_points(info, vertical):
    r = info.rcScrollBar
    first = r.top if vertical else r.left
    last = r.bottom if vertical else r.right
    low = first + info.dxyLineButton
    high = last - info.dxyLineButton
    center = first + (info.xyThumbTop + info.xyThumbBottom) // 2
    if low >= high or not low <= center <= high:
        raise ValueError("Unsafe scrollbar geometry")
    step = max(1, (high - low) // 3)
    target = center + step if center + step <= high else max(low, center - step)
    fixed = (r.left + r.right) // 2 if vertical else (r.top + r.bottom) // 2
    return ((fixed, center), (fixed, target)) if vertical else ((center, fixed), (target, fixed))

def capture(bbox, filename):
    from PIL import ImageGrab
    # An app-owned layered popup must be part of screenshot evidence:
    # Win32 native NC screenshots alone can contradict the visible pixels.
    ImageGrab.grab(bbox=bbox, include_layered_windows=True).save(filename)

def compare(before, after, output, tolerance):
    from PIL import Image, ImageChops
    with Image.open(before) as a, Image.open(after) as b:
        a, b = a.convert("RGB"), b.convert("RGB")
        if a.size != b.size:
            raise ValueError("Window size/DPI mismatch")
        diff = ImageChops.difference(a, b)
        diff.save(output)
        data = diff.tobytes()
        changed = sum(max(data[i:i+3]) > tolerance for i in range(0, len(data), 3))
        return {"changed_pixels": changed, "total_pixels": a.width * a.height,
                "status": "REVIEW_REQUIRED" if changed else "NO_DIFFERENCE_NOT_VISUAL_PASS"}

def bright_neutral_ratio(image_path, bounds):
    """Flag likely native light surfaces, never declare a visual failure alone."""
    from PIL import Image
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        left, top, right, bottom = bounds
        left, top = max(0, left), max(0, top)
        right, bottom = min(image.width, right), min(image.height, bottom)
        if left >= right or top >= bottom:
            raise ValueError("Native scrollbar ROI is outside the captured control")
        pixels = image.crop((left, top, right, bottom)).tobytes()
        bright = sum(
            min(pixels[i:i + 3]) >= 210 and
            max(pixels[i:i + 3]) - min(pixels[i:i + 3]) <= 24
            for i in range(0, len(pixels), 3)
        )
        return bright / ((right - left) * (bottom - top))


def run(args):
    if platform.system() != "Windows":
        raise RuntimeError("Windows interactive desktop is required")
    if not args.synthetic_fixture:
        raise RuntimeError("Open synthetic data and isolated settings before --synthetic-fixture")
    exe = args.exe.resolve(strict=True)
    marker = exe.with_name("build-revision.txt")
    if not marker.exists():
        raise RuntimeError("Build revision marker missing")
    revision = marker.read_text(encoding="utf-8-sig").strip().splitlines()[0].strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if revision != head:
        raise RuntimeError(f"Stale build {revision}; checkout {head}")
    parent = find_hwnd(exe, window_title=args.window_title)
    output = ROOT / "logs" / "visual-ui" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    output.mkdir(parents=True, exist_ok=False)
    u = ctypes.windll.user32
    if hasattr(u, "GetDpiForWindow"):
        u.GetDpiForWindow.argtypes = (wintypes.HWND,)
        u.GetDpiForWindow.restype = wintypes.UINT
        dpi = u.GetDpiForWindow(parent)
    else:
        dpi = None
    manifest = {"revision": revision, "dpi": dpi,
                "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "label": args.label, "status": "CAPTURED_REVIEW_REQUIRED"}
    if args.action == "snapshot":
        capture(rect_of(parent), output / "snapshot.png")
    else:
        from pywinauto import mouse
        cls = "SysListView32" if args.control == "list" else "SysTreeView32"
        target = find_hwnd(parent, cls)
        vertical = args.orientation == "vertical"
        info = scrollbar(target, vertical)
        start, end = drag_points(info, vertical)
        bbox = rect_of(target)
        bar = info.rcScrollBar
        roi = (bar.left - bbox[0], bar.top - bbox[1],
               bar.right - bbox[0], bar.bottom - bbox[1])
        capture(bbox, output / "before.png")
        initial_bright_ratio = bright_neutral_ratio(output / "before.png", roi)
        bright_ratios = []
        thumbs = []
        mouse.press(button="left", coords=start)
        try:
            for i in range(12):
                point = tuple(round(start[j] + (end[j] - start[j]) * (i + 1) / 12) for j in (0, 1))
                mouse.move(coords=point)
                time.sleep(0.06)
                frame_file = output / f"drag-{i:02d}.png"
                capture(bbox, frame_file)
                bright_ratios.append(bright_neutral_ratio(frame_file, roi))
                thumbs.append(scrollbar(target, vertical).xyThumbTop)
        finally:
            mouse.release(button="left", coords=end)
        capture(bbox, output / "after.png")
        suspicious = sum(ratio > 0.35 and ratio - initial_bright_ratio > 0.15
                         for ratio in bright_ratios)
        manifest.update({"initial_bright_ratio": initial_bright_ratio,
                         "drag_bright_ratios": bright_ratios,
                         "possible_native_brightening_frames": suspicious,
                         "control": args.control, "orientation": args.orientation,
                         "start": start, "end": end, "thumb_positions": thumbs,
                         "scrollbar_screen_rect": [info.rcScrollBar.left, info.rcScrollBar.top,
                                                   info.rcScrollBar.right, info.rcScrollBar.bottom]})
        if not any(p != info.xyThumbTop for p in thumbs):
            manifest["status"] = "INCONCLUSIVE_NO_THUMB_MOVEMENT"
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(output)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("snapshot", "ui02"):
        p = sub.add_parser(name)
        p.add_argument("--exe", type=Path, default=ROOT / "bin" / "x64" / "fxfile.exe")
        p.add_argument("--synthetic-fixture", action="store_true")
        p.add_argument("--window-title", help="Select a visible dialog/main window by localized title")
        p.add_argument("--label", required=True, help="Case ID, not a personal file name")
        if name == "ui02":
            p.add_argument("--control", choices=("list", "tree"), required=True)
            p.add_argument("--orientation", choices=("vertical", "horizontal"), required=True)
    p = sub.add_parser("compare")
    p.add_argument("baseline", type=Path)
    p.add_argument("current", type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--tolerance", type=int, default=12, choices=range(256))
    args = parser.parse_args()
    if args.action == "compare":
        print(json.dumps(compare(args.baseline, args.current, args.output, args.tolerance), indent=2))
    else:
        run(args)

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print("NOT TESTED:", exc, file=sys.stderr)
        sys.exit(2)
