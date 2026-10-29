"""Finite L03 extensionless-dotfile Type-column comparison on an owned WinUI window.

Run with --phase before on retained old Release, then --phase after after an
incremental build. Only controlled local fixture, isolated profile, and owned
process/window; never inspect arbitrary desktop content or user files.
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
p.add_argument("--phase", choices=("before", "after"), required=True)
p.add_argument("--theme", choices=("dark", "light"), required=True)
p.add_argument("--slot", choices=("v2", "v3", "v4"), default="v4")
args = p.parse_args()
BASE = ROOT / "logs" / ("l03-dotfile-20261029-owned-" + args.slot)
fixture = BASE / "fixture"
assert fixture.is_dir() and fixture.resolve().parent == BASE.resolve()
# An archive can be a virtual Shell folder; it is not a file-type row.
names = (".gitignore", ".env", ".env.local", "readme.txt")
fixture_names = names + ("archive.tar.gz",)
assert sorted(x.name for x in fixture.iterdir()) == sorted(fixture_names)
before_hashes = {x.name: hashlib.sha256(x.read_bytes()).hexdigest()
                 for x in fixture.iterdir()}
run_id = args.phase + "-" + args.theme
owned = BASE / ("profile-" + run_id)
owned.mkdir(exist_ok=False)
env = {k: v for k, v in os.environ.items() if not k.startswith("FLY")}
for key in ("APPDATA", "LOCALAPPDATA", "USERPROFILE", "TEMP", "TMP"):
    d = owned / key.lower()
    d.mkdir()
    env[key] = str(d)

legacy_root, legacy = snapshot_legacy_profile()
exe = ROOT / "out" / "winui" / "Release" / "flyExplorer.exe"
exe_digest = hashlib.sha256(exe.read_bytes()).hexdigest()
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
complete = False
out = {"phase": args.phase, "theme": args.theme, "exe_sha256": exe_digest,
       "windows": platform.version()}

def wait(fn, label, seconds=24):
    return wait_until(fn, label, seconds=seconds, interval=.17)

def hwnd_pid(handle):
    ident = w.DWORD()
    u.GetWindowThreadProcessId(handle, c.byref(ident))
    return ident.value

def get_win():
    global hwnd
    assert process.poll() is None, "owned app exited"
    assert Path(psutil.Process(process.pid).exe()).resolve() == exe.resolve()
    matches = [v for v in Desktop(backend="uia").windows(process=process.pid)
               if "flyExplorer" in v.window_text()]
    if len(matches) != 1:
        return None
    hwnd = matches[0].handle
    assert hwnd_pid(hwnd) == process.pid
    return Desktop(backend="uia").window(handle=hwnd)

def extract_type(row_text):
    # WinUI row accessible-name contract: [파일] name | type | size | date.
    parts = [part.strip() for part in row_text.split("|")]
    if len(parts) < 2 or "[파일]" not in parts[0]:
        return None
    return parts[1]

try:
    win = wait(get_win, "owned WinUI window absent")
    el = lambda name: win.child_window(auto_id=name, visible_only=False)

    def inspect_side(side):
        rows = el(side + "Files").descendants(control_type="ListItem")
        values = {}
        for row in rows:
            caption = row.window_text()
            name = caption.split("|", 1)[0].strip()
            if not name.startswith("[파일]"):
                continue
            name = name[len("[파일]"):].strip()
            if name in names:
                values[name] = extract_type(caption)
        return values

    def selected_side():
        for side in ("Left", "Right"):
            values = inspect_side(side)
            if all(values.get(name) for name in names):
                return (side, values)
        return None

    # The registered .txt label is an async decoration; it is not a
    # prerequisite for the dotfile fallback being independently observable.
    try:
        side, values = wait(selected_side, "owned file rows missing", 22)
    except AssertionError:
        print("L03_OWNED_UIA_DIAGNOSTIC=" + json.dumps({
            side: [r.window_text() for r in
                   el(side + "Files").descendants(control_type="ListItem")][:12]
            for side in ("Left", "Right")}, ensure_ascii=True), flush=True)
        raise
    time.sleep(1.0)
    win.set_focus()
    assert hwnd_pid(u.GetForegroundWindow()) == process.pid
    assert u.MoveWindow(hwnd, 20, 20, 1160, 640, True)
    el("ThemePicker").select(1 if args.theme == "light" else 2)
    wait(lambda: ("라이트" if args.theme == "light" else "다크")
         in el("ThemeStateText").window_text(), "theme state mismatch")
    side, values = wait(selected_side, "owned type labels missing after theme change", 15)
    if args.phase == "after":
        for name in (".gitignore", ".env"):
            assert values[name] == "파일", (name, values[name])
        assert values[".env.local"] != "파일", "genuine .local extension lost"
    out["source_pane"] = side
    out["types"] = values
    out["dpi"] = u.GetDpiForWindow(hwnd)
    window_rect = win.rectangle()
    out["window"] = [window_rect.left, window_rect.top,
                     window_rect.right, window_rect.bottom]
    assert out["dpi"] == 96, "out-of-scope DPI changed"
    assert len(el("LeftFiles").descendants(control_type="ListItem")) > 0
    assert len(el("RightFiles").descendants(control_type="ListItem")) > 0
    win.set_focus()
    assert hwnd_pid(u.GetForegroundWindow()) == process.pid
    r = win.rectangle()
    bounds = (r.left, r.top, r.right, r.bottom)
    sw, sh = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    assert 0 <= r.left < r.right <= sw and 0 <= r.top < r.bottom <= sh
    image = BASE / ("capture-" + run_id + ".png")
    assert not image.exists(), "existing capture must not be overwritten"
    ImageGrab.grab(bbox=bounds, include_layered_windows=True).save(image)
    out["png_sha256"] = hashlib.sha256(image.read_bytes()).hexdigest()
    complete = True
finally:
    if process.poll() is None:
        if hwnd and hwnd_pid(hwnd) == process.pid:
            u.PostMessageW(hwnd, 0x10, 0, 0)
        try:
            process.wait(timeout=16)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=6)
    out["normal_exit"] = process.returncode == 0
    assert_legacy_profile_unchanged(legacy_root, legacy)
    out["legacy_profile_unchanged"] = True
    out["owned_bytes_unchanged"] = (
        before_hashes == {x.name: hashlib.sha256(x.read_bytes()).hexdigest()
                          for x in fixture.iterdir()})
    if complete and out["normal_exit"] and out["owned_bytes_unchanged"]:
        assert owned.parent == BASE and not owned.is_symlink()
        shutil.rmtree(owned)
        out["owned_profile_removed"] = True
    print("L03_DOTFILE_GUI_RESULT=" + json.dumps(out, ensure_ascii=True), flush=True)
assert complete and out["normal_exit"] and out["owned_bytes_unchanged"]
