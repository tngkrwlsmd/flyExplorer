"""PX02: one owned Windows GUI smoke for the unified Home overview.

No private history reads, external provider actions, unrelated HWNDs, or
persistent activity opt-in; the only bookmark is in an isolated APPDATA.
"""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from pywinauto import Desktop
from paths import ROOT, app_exe
from uia_polling import wait_until

LEGACY = ("fxfile.conf", "fxfile-main.conf", "fxfile-toolbar.dat",
          "fxfile-coolbar.dat", "fxfile-dlg_state.conf", "fxfile-folder_layout.conf")
user = c.windll.user32
user.GetWindowThreadProcessId.argtypes = (w.HWND, c.POINTER(w.DWORD))
user.GetWindowThreadProcessId.restype = w.DWORD
user.PostMessageW.argtypes = (w.HWND, w.UINT, w.WPARAM, w.LPARAM)
user.PostMessageW.restype = w.BOOL


def eventually(fn, label, seconds=14):
    return wait_until(fn, label, seconds=seconds, interval=.2)


def owner_pid(hwnd):
    pid = w.DWORD()
    user.GetWindowThreadProcessId(w.HWND(hwnd), c.byref(pid))
    return pid.value


def invoke(target):
    try:
        target.invoke()
    except Exception:
        target.click_input()


def main(config="Release"):
    exe = app_exe(config)
    assert exe.is_file()
    root = ROOT / "logs" / "px02-owned-home"
    root.mkdir(parents=True, exist_ok=True)
    owned = Path(tempfile.mkdtemp(prefix="home-overview-", dir=root))
    start = owned / "홈전용폴더"
    start.mkdir()
    file = start / "홈원본-보존.txt"
    file.write_bytes(b"home-owned-preserved-file")
    original = file.read_bytes()
    mfc = Path(os.environ["APPDATA"]) / "fxfile" / "conf"
    before = {name: hashlib.sha256((mfc / name).read_bytes()).digest()
              for name in LEGACY if (mfc / name).is_file()}
    env = os.environ.copy()
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        sub = owned / key.lower()
        sub.mkdir()
        env[key] = str(sub)
    for key in ("FLY_M23_OWNED_SESSION", "FLY_M23_OWNED_DRAG_TEST"):
        env.pop(key, None)
    app = subprocess.Popen([str(exe), str(start)], cwd=exe.parent, env=env,
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    hwnd = None
    completed = False
    try:
        def view():
            nonlocal hwnd
            assert app.poll() is None, "Test-owned app exited prematurely"
            windows = [x for x in Desktop(backend="uia").windows(process=app.pid)
                       if "flyExplorer" in x.window_text()]
            if len(windows) != 1:
                return None
            hwnd = windows[0].handle
            assert owner_pid(hwnd) == app.pid
            return Desktop(backend="uia").window(handle=hwnd)

        win = eventually(view, "Owned WinUI window did not appear", 25)
        element = lambda name: win.child_window(auto_id=name)
        def panel_visible(name):
            target = element(name)
            return target.exists() and target.is_visible()
        eventually(lambda: str(start).casefold()
                   in element("AddressBox").get_value().casefold(),
                   "Test-owned initial folder not committed", 20)
        # WinUI may remove Collapsed content entirely from its UIA tree.
        assert not panel_visible("HomeOverviewPanel")

        invoke(element("AddBookmarkButton"))
        eventually(lambda: element("BookmarkButtonsPanel").exists() and
                   any("홈전용폴더" in b.window_text()
                       for b in element("BookmarkButtonsPanel").descendants(
                           control_type="Button")),
                   "Test-owned bookmark was not created", 12)
        assert file.read_bytes() == original

        invoke(element("HomeButton"))
        eventually(lambda: panel_visible("HomeOverviewPanel"),
                   "Sidebar Home did not show unified overview")
        eventually(lambda: "1개" in element("HomePinnedStatus").window_text(),
                   "Unified Home did not aggregate owned bookmark")
        assert "기록 꺼짐" in element("HomeActivityPrivacyText").window_text()
        assert len(element("HomeRecentItems").descendants(
            control_type="Button")) == 0
        assert len(element("HomeFrequentItems").descendants(
            control_type="Button")) == 0
        print("PX02_HOME_DEFAULT_PRIVACY_OFF=PASS", flush=True)
        print("PX02_HOME_BOOKMARK_AGGREGATED=PASS", flush=True)

        invoke(element("HomeManageActivityButton"))
        eventually(lambda: panel_visible("RecentActivityPanel") and
                   not panel_visible("HomeOverviewPanel"),
                   "Recent activity management did not replace Home")
        assert "기록 꺼짐" in element("RecentActivityStateText").window_text()
        assert not element("RecentActivityFiles").is_enabled()
        invoke(element("RecentActivityOptIn"))
        eventually(lambda: "기록 켜짐" in
                   element("RecentActivityStateText").window_text(),
                   "Explicit consent did not enable session history")
        assert "아직 없습니다" in element("RecentActivityStateText").window_text()
        print("PX02_HOME_SESSION_OPT_IN_EMPTY=PASS", flush=True)

        invoke(element("HomeButton"))
        eventually(lambda: panel_visible("HomeOverviewPanel"),
                   "Home was not restored after activity management")
        assert "기록 켜짐" in element("HomeActivityPrivacyText").window_text()
        assert "최근 파일 0개" in element("HomeActivityPrivacyText").window_text()
        print("PX02_HOME_OPTED_IN_EMPTY_NO_BACKFILL=PASS", flush=True)

        invoke(element("HomeManageBookmarksButton"))
        eventually(lambda: panel_visible("BookmarkPanel") and
                   not panel_visible("HomeOverviewPanel"),
                   "Bookmark management did not replace Home")
        invoke(element("HomeButton"))
        eventually(lambda: panel_visible("HomeOverviewPanel"),
                   "Home not restored after bookmark management")

        def owned_tile():
            matches = [b for b in element("HomePinnedItems").descendants(
                control_type="Button")
                       if "홈전용폴더" in b.window_text()]
            return matches[0] if len(matches) == 1 else None

        tile = eventually(owned_tile, "Owned bookmark not present in Home")
        assert owner_pid(hwnd) == app.pid
        invoke(tile)
        eventually(lambda: not panel_visible("HomeOverviewPanel"),
                   "Home tile navigation did not dismiss overview")
        eventually(lambda: str(start).casefold() in
                   element("AddressBox").get_value().casefold(),
                   "Home tile did not retain owned navigation destination")
        assert file.read_bytes() == original
        print("PX02_HOME_BOOKMARK_NAVIGATION=PASS", flush=True)
        completed = True
    finally:
        if app.poll() is None:
            if hwnd and owner_pid(hwnd) == app.pid:
                user.PostMessageW(hwnd, 0x10, 0, 0)
                try:
                    app.wait(timeout=13)
                except subprocess.TimeoutExpired:
                    app.terminate()
                    app.wait(timeout=7)
            else:
                app.terminate()
                app.wait(timeout=7)
        exited = app.poll() == 0
        unchanged = all((mfc / name).is_file() and
                        hashlib.sha256((mfc / name).read_bytes()).digest()
                        == digest for name, digest in before.items())
        preserved = file.is_file() and file.read_bytes() == original
        print("PX02_HOME_APP_NORMAL_EXIT", exited, flush=True)
        print("PX02_HOME_LEGACY_PROFILE_UNCHANGED", unchanged, flush=True)
        print("PX02_HOME_OWNED_FILE_PRESERVED", preserved, flush=True)
        if completed and exited and unchanged and preserved:
            shutil.rmtree(owned)
            print("PX02_HOME_OWNED_WORKSPACE_REMOVED=True", flush=True)
        else:
            print("PX02_HOME_OWNED_TEST_RETAINED_FOR_DIAGNOSTIC=True", flush=True)
    return 0 if completed and exited and unchanged and preserved else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "Release"))
