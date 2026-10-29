"""M24: owned .txt registered icon readiness and visible WinUI pixel receipt.

A row's registered type text is not sufficient: wait for the actual UIA Image
child named "Windows system registered file icon", within the exact owned
readme.txt row, and capture the owned window after the image appears.
"""
import argparse
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "winui"))
from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
from uia_polling import wait_until
from pywinauto import Desktop
from PIL import ImageGrab
import psutil

p = argparse.ArgumentParser()
p.add_argument("--theme", choices=("dark", "light"), required=True)
args = p.parse_args()
BASE = ROOT / "logs" / "m24-txt-icon-20261029-owned"
fixture = BASE / "fixture"
assert fixture.is_dir() and fixture.resolve().parent == BASE.resolve()
names = ("readme.txt", ".env.local", ".gitignore")
assert sorted(x.name for x in fixture.iterdir()) == sorted(names)
original = {x.name: hashlib.sha256(x.read_bytes()).hexdigest()
            for x in fixture.iterdir()}
profile = BASE / ("profile-" + args.theme)
profile.mkdir(exist_ok=False)
env = {k: v for k, v in os.environ.items() if not k.startswith("FLY")}
for key in ("APPDATA", "LOCALAPPDATA", "USERPROFILE", "TEMP", "TMP"):
    d = profile / key.lower()
    d.mkdir()
    env[key] = str(d)
legacy_root, legacy = snapshot_legacy_profile()
exe = ROOT / "out" / "winui" / "Release" / "flyExplorer.exe"
exe_hash = hashlib.sha256(exe.read_bytes()).hexdigest()
u = c.windll.user32
u.GetForegroundWindow.restype = w.HWND
u.GetWindowThreadProcessId.argtypes = (w.HWND, c.POINTER(w.DWORD))
u.MoveWindow.argtypes = (w.HWND, c.c_int, c.c_int, c.c_int, c.c_int, w.BOOL)
u.PostMessageW.argtypes = (w.HWND, w.UINT, w.WPARAM, w.LPARAM)
u.GetDpiForWindow.argtypes = (w.HWND,)
u.GetDpiForWindow.restype = w.UINT
process = subprocess.Popen([str(exe), str(fixture)], cwd=exe.parent, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
hwnd = None
ready = False
receipt = {"theme": args.theme, "exe_sha256": exe_hash,
           "windows": platform.version(), "icon_ready": False}

def wait(fn, label, seconds=25):
    return wait_until(fn, label, seconds=seconds, interval=.2)

def pid(handle):
    out = w.DWORD()
    u.GetWindowThreadProcessId(handle, c.byref(out))
    return out.value

def win_of_owned_pid():
    global hwnd
    assert process.poll() is None, "owned flyExplorer exited unexpectedly"
    assert Path(psutil.Process(process.pid).exe()).resolve() == exe.resolve()
    windows = [x for x in Desktop(backend="uia").windows(process=process.pid)
               if "flyExplorer" in x.window_text()]
    if len(windows) != 1:
        return None
    hwnd = windows[0].handle
    assert pid(hwnd) == process.pid, "foreign app HWND"
    return Desktop(backend="uia").window(handle=hwnd)

def target_row(win, side):
    listing = win.child_window(auto_id=side + "Files", visible_only=False)
    for row in listing.descendants(control_type="ListItem"):
        first = row.window_text().split("|", 1)[0].strip()
        if first.startswith("[파일]") and first[len("[파일]"):].strip() == "readme.txt":
            return row
    return None

def image_info(row):
    images = []
    for node in row.descendants(control_type="Image"):
        try:
            images.append((node.window_text(), node.rectangle()))
        except (RuntimeError, AttributeError):
            continue
    return images

def capture(win, label):
    assert pid(u.GetForegroundWindow()) == process.pid, "foreign foreground"
    rect = win.rectangle()
    sw, sh = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    assert 0 <= rect.left < rect.right <= sw
    assert 0 <= rect.top < rect.bottom <= sh
    target = BASE / ("capture-" + label + "-" + args.theme + ".png")
    assert not target.exists(), "do not overwrite prior pixel evidence"
    ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom),
                   include_layered_windows=True).save(target)
    receipt["png_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    receipt["window_rect"] = [rect.left, rect.top, rect.right, rect.bottom]

try:
    win = wait(win_of_owned_pid, "owned WinUI window absent")
    win.set_focus()
    assert pid(u.GetForegroundWindow()) == process.pid
    assert u.MoveWindow(hwnd, 20, 20, 1160, 640, True)
    picker = win.child_window(auto_id="ThemePicker", visible_only=False)
    picker.select(1 if args.theme == "light" else 2)
    wait(lambda: ("라이트" if args.theme == "light" else "다크")
         in win.child_window(auto_id="ThemeStateText").window_text(),
         "requested theme did not activate")
    assert u.GetDpiForWindow(hwnd) == 96, "only 96 DPI in this scenario"

    def owned_readme_exists():
        for side in ("Left", "Right"):
            row = target_row(win, side)
            if row is not None:
                return side, row
        return None
    wait(owned_readme_exists, "owned readme.txt row not yet visible")
    def visible_image():
        for side in ("Left", "Right"):
            row = target_row(win, side)
            if row is None:
                continue
            for name, rect in image_info(row):
                if name != "Windows system registered file icon":
                    continue
                rowrect = row.rectangle()
                if (rowrect.left <= rect.left < rect.right <= rowrect.right and
                    rowrect.top <= rect.top < rect.bottom <= rowrect.bottom):
                    return side, row, rect
        return None
    try:
        side, row, icon_rect = wait(
            visible_image, "registered readme.txt UIA Image never ready", 24)
        # Re-observe after a finite settling interval rather than recording
        # only one transient automation element.
        time.sleep(.35)
        verified = visible_image()
        assert verified is not None, "registered icon vanished"
        receipt["icon_ready"] = True
        receipt["source_pane"] = side
        receipt["readme_type"] = row.window_text().split("|")[1].strip()
        receipt["image_automation_name"] = "Windows system registered file icon"
        receipt["icon_rect"] = [icon_rect.left, icon_rect.top,
                                icon_rect.right, icon_rect.bottom]
    except AssertionError as failure:
        receipt["icon_diagnostic"] = {
            side: {
                "row": (row.window_text() if (row := target_row(win, side))
                        is not None else None),
                "images": ([name for name, _ in image_info(row)]
                           if row is not None else []),
            } for side in ("Left", "Right")
        }
        receipt["icon_failure"] = str(failure)

    win.set_focus()
    capture(win, "ready" if receipt["icon_ready"] else "missing")
    ready = receipt["icon_ready"]
finally:
    if process.poll() is None:
        if hwnd and pid(hwnd) == process.pid:
            u.PostMessageW(hwnd, 0x10, 0, 0)
        try:
            process.wait(timeout=16)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=6)
    receipt["normal_exit"] = process.returncode == 0
    assert_legacy_profile_unchanged(legacy_root, legacy)
    receipt["legacy_profile_unchanged"] = True
    receipt["fixture_bytes_unchanged"] = (
        original == {x.name: hashlib.sha256(x.read_bytes()).hexdigest()
                     for x in fixture.iterdir()})
    if receipt["normal_exit"] and receipt["fixture_bytes_unchanged"]:
        assert profile.parent == BASE and not profile.is_symlink()
        shutil.rmtree(profile)
        receipt["owned_profile_removed"] = True
    print("M24_ICON_GUI_RESULT=" + json.dumps(receipt, ensure_ascii=True), flush=True)
assert ready and receipt["normal_exit"] and receipt["fixture_bytes_unchanged"]
