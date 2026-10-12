"""Take matched actual WinUI filter-color/icon screenshots in a disposable profile.

The tool verifies *capture safety*, not visual acceptance. Inspect both rendered
PNG previews yourself before reporting a visual PASS. Run against exact pre-
feature and post-feature Release binaries at the same desktop DPI and geometry.
"""
from __future__ import annotations

import argparse
import ctypes as c
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

if os.name != "nt":
    raise SystemExit("Actual WinUI screenshots require Windows")


def run():
    a = argparse.ArgumentParser()
    a.add_argument("--source", required=True, type=Path)
    a.add_argument("--label", required=True, choices=("before", "after"))
    a.add_argument("--source-sha", required=True)
    a.add_argument("--output", required=True, type=Path)
    v = a.parse_args()
    root = v.source.resolve(strict=True)
    output = v.output.resolve(strict=True)
    assert len(v.source_sha) == 40 and all(ch in "0123456789abcdef" for ch in v.source_sha)
    sys.path.insert(0, str(root / "tests" / "winui"))
    from paths import app_exe
    from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
    from uia_polling import wait_until
    from pywinauto import Desktop
    from PIL import ImageGrab

    exe = app_exe("Release")
    assert exe.exists(), "Exact revision Release EXE is missing"
    orig, before = snapshot_legacy_profile()
    owned = Path(tempfile.mkdtemp(prefix="filter-visual-", dir=output))
    for folder in ("files", "appdata", "localdata", "temp"):
        (owned / folder).mkdir()
    for name in ("alpha.cpp", "beta.h", "notes.txt", "사진.JPG"):
        (owned / "files" / name).write_text("owned only", encoding="utf-8")
    env = dict(os.environ)
    env.update(APPDATA=str(owned / "appdata"),
               LOCALAPPDATA=str(owned / "localdata"),
               TEMP=str(owned / "temp"), TMP=str(owned / "temp"))

    u = c.windll.user32
    u.GetForegroundWindow.restype = W.HWND
    u.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
    u.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
    u.GetDpiForWindow.argtypes = [W.HWND]
    u.GetDpiForWindow.restype = W.UINT
    u.SetWindowPos.argtypes = [W.HWND, W.HWND, c.c_int, c.c_int, c.c_int, c.c_int, W.UINT]
    cbtype = c.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    u.EnumWindows.argtypes = [cbtype, W.LPARAM]

    def windows(pid):
        found = []
        @cbtype
        def visitor(hwnd, unused):
            opid = W.DWORD()
            u.GetWindowThreadProcessId(hwnd, c.byref(opid))
            if opid.value == pid and u.IsWindowVisible(hwnd):
                found.append(hwnd)
            return True
        u.EnumWindows(visitor, 0)
        return found

    def foreground_ours(pid):
        hwnd = u.GetForegroundWindow()
        opid = W.DWORD()
        if hwnd:
            u.GetWindowThreadProcessId(hwnd, c.byref(opid))
        return bool(hwnd) and opid.value == pid

    proc, hwnd = None, None
    try:
        proc = subprocess.Popen([str(exe), str(owned / "files")],
                                cwd=exe.parent, env=env,
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        wait_until(lambda: len(windows(proc.pid)) == 1 or proc.poll() is not None,
                   "owned WinUI filter visual window unavailable", seconds=22,
                   interval=.15)
        assert proc.poll() is None and len(windows(proc.pid)) == 1
        hwnd = windows(proc.pid)[0]
        win = Desktop(backend="uia").window(handle=hwnd)
        assert u.SetWindowPos(hwnd, None, 35, 25, 1060, 760, 0x0014)
        wait_until(lambda: win.rectangle().width() == 1060 and
                   win.rectangle().height() == 760,
                   "matched filter window geometry failed", seconds=8, interval=.15)
        for _ in range(5):
            win.set_focus()
            time.sleep(.12)
            if foreground_ours(proc.pid):
                break
        assert foreground_ours(proc.pid), "Refuse input/capture without test-owned foreground"
        win.child_window(auto_id="FilterRulePanelButton").click_input()
        name = win.child_window(auto_id="FilterRuleNameEdit")
        masks = win.child_window(auto_id="FilterRuleMasksEdit")
        assert name.exists(timeout=5) and masks.exists(timeout=5)
        name.set_edit_text("코드 파일")
        masks.set_edit_text("*.cpp;*.h")
        if v.label == "after":
            win.child_window(auto_id="FilterRuleColorBox").select(1)
            win.child_window(auto_id="FilterRuleIconBox").select(1)
        else:
            assert not win.child_window(auto_id="FilterRuleColorBox").exists(timeout=.2)
        win.child_window(auto_id="FilterRuleSaveButton").click_input()
        rulefile = owned / "localdata" / "flyExplorer" / "filter-rules-v1.txt"
        wait_until(lambda: rulefile.is_file() and
                   "필터 프리셋을 저장했습니다." in
                   win.child_window(auto_id="StatusText").window_text(),
                   "filter preset did not save", seconds=10, interval=.2)
        data = rulefile.read_text(encoding="utf-8")
        if v.label == "after":
            assert "schema=2" in data and "코드 파일\t*.cpp;*.h\t1\t1" in data
            wait_until(lambda: any("필터 분류 아이콘" in item.window_text()
                                     for item in win.child_window(
                                         auto_id="LeftFiles").descendants()),
                       "styled file badge not visible", seconds=8, interval=.2)
        else:
            assert "schema=1" in data and "코드 파일\t*.cpp;*.h" in data
        wait_until(lambda: any("alpha.cpp" in item.window_text()
                               for item in win.child_window(
                                   auto_id="LeftFiles").descendants(
                                   control_type="ListItem")),
                   "test-owned file row not visible", seconds=9, interval=.2)
        time.sleep(.8)
        assert foreground_ours(proc.pid), "Refuse capture: different foreground window"
        rect = win.rectangle()
        dpi = int(u.GetDpiForWindow(hwnd))
        window = [rect.left, rect.top, rect.right, rect.bottom]
        assert window == [35, 25, 1095, 785], window
        assert u.GetSystemMetrics(0) >= window[2] and u.GetSystemMetrics(1) >= window[3]
        full = ImageGrab.grab(bbox=tuple(window), include_layered_windows=True)
        assert full.size == (1060, 760)
        fullpath = output / (v.label + "-full.png")
        full.save(fullpath, "PNG", optimize=True)
        preview = full.crop((0, 0, 1060, 680))
        path = output / (v.label + "-preview.png")
        preview.save(path, "PNG", optimize=True)
        metadata = {
            "revision": v.source_sha,
            "binary_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
            "label": v.label, "configuration": "Release",
            "dpi": dpi, "window": window,
            "desktop": [u.GetSystemMetrics(0), u.GetSystemMetrics(1)],
            "preview_rect_relative_to_window": [0, 0, 1060, 680],
            "theme": "isolated user dark UI",
            "profile_schema": "schema=2" if v.label == "after" else "schema=1",
            "fixture": "test-owned alpha.cpp/beta.h/notes.txt/사진.JPG",
            "preview_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        (output / (v.label + "-metadata.json")).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print("FILTER_VISUAL_" + v.label.upper() + "_CAPTURE=PASS", flush=True)
        print("FILTER_VISUAL_" + v.label.upper() + "_DPI=" + str(dpi), flush=True)
    finally:
        if proc is not None and proc.poll() is None:
            if hwnd is not None:
                owner = W.DWORD()
                u.GetWindowThreadProcessId(hwnd, c.byref(owner))
                assert owner.value == proc.pid, "Refuse closing non-test HWND"
                assert u.PostMessageW(hwnd, 0x10, 0, 0)
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                raise AssertionError("Test-owned WinUI process failed graceful WM_CLOSE")
        if proc is not None and proc.poll() is not None:
            assert proc.returncode == 0, "Test-owned WinUI crashed on shutdown"
        assert_legacy_profile_unchanged(orig, before)
        shutil.rmtree(owned)


if __name__ == "__main__":
    run()
