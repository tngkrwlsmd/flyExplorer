"""PX15 owned two-axis SearchPanel compact-window GUI acceptance only.

Uses test-owned files, an isolated profile and owned WinUI HWND screenshots.
Does not exercise unrelated Search Cancel, Move, Home or session persistence.
"""
from pathlib import Path
import argparse
import ctypes as c
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes as w

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "winui"))
from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
from uia_polling import wait_until
from pywinauto import Desktop
from PIL import ImageGrab
import psutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--theme", choices=("light", "dark"), required=True)
args = parser.parse_args()
base = ROOT / "logs" / "px15-horizontal-search-owned"
base.mkdir(parents=True, exist_ok=True)
owned = Path(tempfile.mkdtemp(prefix="run-", dir=base)).resolve()
fixture = owned / "fixture"
fixture.mkdir()
for name in ("search-owned-one.txt", "other-owned.txt"):
    (fixture / name).write_text("owned compact search fixture", encoding="utf-8")
original = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in fixture.iterdir()}
env = {k: v for k, v in os.environ.items() if not k.startswith("FLY")}
for key in ("APPDATA", "LOCALAPPDATA", "USERPROFILE", "TEMP", "TMP"):
    p = owned / key.lower()
    p.mkdir()
    env[key] = str(p)
legacy_root, legacy = snapshot_legacy_profile()
exe = ROOT / "out" / "winui" / "Release" / "flyExplorer.exe"
u = c.windll.user32
u.GetForegroundWindow.restype = w.HWND
u.GetWindowThreadProcessId.argtypes = (w.HWND, c.POINTER(w.DWORD))
u.MoveWindow.argtypes = (w.HWND, c.c_int, c.c_int, c.c_int, c.c_int, w.BOOL)
u.PostMessageW.argtypes = (w.HWND, w.UINT, w.WPARAM, w.LPARAM)
u.GetDpiForWindow.argtypes = (w.HWND,)
u.GetDpiForWindow.restype = w.UINT
app = subprocess.Popen([str(exe), str(fixture)], cwd=exe.parent, env=env)
hwnd = None
complete = False
result = {"theme": args.theme,
          "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
          "windows": platform.version(), "snapshots": []}

def wait(fn, why, timeout=20):
    return wait_until(fn, why, seconds=timeout, interval=.15)

def pid(handle):
    out = w.DWORD()
    u.GetWindowThreadProcessId(handle, c.byref(out))
    return out.value

def rect(node):
    r = node.rectangle()
    return [r.left, r.top, r.right, r.bottom]

def capture(label, win):
    assert pid(u.GetForegroundWindow()) == app.pid, "foreign foreground"
    box = rect(win)
    sw, sh = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    assert 0 <= box[0] < box[2] <= sw and 0 <= box[1] < box[3] <= sh
    path = base / (args.theme + "-" + label + ".png")
    assert not path.exists(), "existing screenshot: refusing overwrite"
    ImageGrab.grab(bbox=tuple(box), include_layered_windows=True).save(path)
    result["snapshots"].append({"label": label,
          "png_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
          "window": box, "dpi": u.GetDpiForWindow(hwnd)})
try:
    def view():
        global hwnd
        assert app.poll() is None
        assert Path(psutil.Process(app.pid).exe()).resolve() == exe.resolve()
        wins = [v for v in Desktop(backend="uia").windows(process=app.pid)
                if "flyExplorer" in v.window_text()]
        if len(wins) != 1:
            return None
        hwnd = wins[0].handle
        assert pid(hwnd) == app.pid
        return Desktop(backend="uia").window(handle=hwnd)

    win = wait(view, "owned window absent")
    el = lambda name: win.child_window(auto_id=name, visible_only=False)
    def has_owned_row(name):
        return any("search-owned-one.txt" in row.window_text()
                   for row in el(name).descendants(control_type="ListItem"))
    wait(lambda: has_owned_row("LeftFiles") or has_owned_row("RightFiles"),
         "no owned file rows in either pane")
    result["startup_owned_left"] = bool(has_owned_row("LeftFiles"))
    result["startup_owned_right"] = bool(has_owned_row("RightFiles"))
    win.set_focus()
    assert pid(u.GetForegroundWindow()) == app.pid
    sw, sh = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    assert sw >= 1000 and sh >= 620, "display too small for controlled test"
    el("ThemePicker").select(1 if args.theme == "light" else 2)
    wait(lambda: ("라이트" if args.theme == "light" else "다크")
         in el("ThemeStateText").window_text(), "theme switch failed")
    assert u.MoveWindow(hwnd, 20, 20, 960, 519, True)
    el("SearchPanelButton").invoke()
    wait(lambda: el("SearchTermBox").is_visible(), "search panel closed")
    # Search the exact owned folder, independent of the initial active pane.
    el("SearchScopeBox").set_edit_text(str(fixture))
    el("SearchTermBox").set_edit_text("search-owned-one")
    el("SearchRunButton").invoke()
    wait(lambda: len(el("SearchMatches").descendants(control_type="ListItem")) == 1,
         "owned search result absent")
    panel = el("SearchPanel").wrapper_object()
    scroll = panel.iface_scroll
    assert scroll.CurrentVerticallyScrollable, "vertical scrollbar unavailable"
    assert u.MoveWindow(hwnd, 20, 20, 800, 519, True)
    time.sleep(.5)
    win.set_focus()
    assert pid(u.GetForegroundWindow()) == app.pid
    panel = el("SearchPanel").wrapper_object()
    scroll = panel.iface_scroll
    assert scroll.CurrentHorizontallyScrollable, "800px search row has no horizontal overflow"
    scroll.SetScrollPercent(0, 0)
    time.sleep(.2)
    capture("compact-800-left", win)
    scroll.SetScrollPercent(100, -1)
    time.sleep(.3)
    pct = float(scroll.CurrentHorizontalScrollPercent)
    assert pct >= 95.0, ("horizontal scroll did not reach end", pct)
    viewport = el("SearchPanel").rectangle()
    right = el("SearchCancelButton").rectangle()
    assert viewport.left <= right.left < right.right <= viewport.right, (
        "rightmost control remains clipped after horizontal scroll", viewport, right)
    capture("compact-800-right", win)
    scroll.SetScrollPercent(0, 100)
    time.sleep(.3)
    matches = el("SearchMatches").descendants(control_type="ListItem")
    assert len(matches) == 1 and "search-owned-one.txt" in matches[0].window_text()
    matches[0].select()
    assert el("SearchLocateButton").is_enabled()
    assert u.MoveWindow(hwnd, 20, 20, 960, 519, True)
    time.sleep(.4)
    win.set_focus()
    for name in ("LeftFiles", "RightFiles"):
        box = el(name).rectangle()
        assert box.bottom - box.top >= 80, (name, box)
        r = win.rectangle()
        assert r.top <= box.top < box.bottom <= r.bottom, (name, box)
    capture("compact-960-results", win)
    result["horizontal_scroll_percent"] = pct
    result["file_panes_visible"] = True
    complete = True
finally:
    if app.poll() is None:
        if hwnd:
            u.PostMessageW(hwnd, 0x10, 0, 0)
        try:
            app.wait(timeout=15)
        except subprocess.TimeoutExpired:
            app.terminate()
            app.wait(timeout=6)
    result["normal_exit"] = app.returncode == 0
    assert_legacy_profile_unchanged(legacy_root, legacy)
    result["legacy_profile_unchanged"] = True
    assert original == {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in fixture.iterdir()}
    result["owned_original_preserved"] = True
    if complete and result["normal_exit"]:
        assert owned.parent == base and not owned.is_symlink()
        shutil.rmtree(owned)
        result["owned_profiles_removed"] = True
    print("PX15_HORIZONTAL_SEARCH_RESULT=" + json.dumps(result), flush=True)
assert complete and result["normal_exit"]
