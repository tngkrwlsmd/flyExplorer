"""PX06 exact-source owned Windows GUI: cancel a busy search and reject late rows.

All filesystem I/O stays under a uniquely-created owned test folder. It never
touches an existing Explorer window, machine settings, or a user search history.
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
import time

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


def eventually(predicate, label, seconds=15):
    return wait_until(predicate, label, seconds=seconds, interval=.15)


def owner_pid(hwnd):
    pid = w.DWORD()
    user.GetWindowThreadProcessId(w.HWND(hwnd), c.byref(pid))
    return pid.value


def invoke(button):
    try:
        button.invoke()
    except Exception:
        button.click_input()


def main(config="Release"):
    exe = app_exe(config)
    assert exe.is_file()
    owned_root = ROOT / "logs" / "px06-owned-search-cancel"
    owned_root.mkdir(parents=True, exist_ok=True)
    owned = Path(tempfile.mkdtemp(prefix="px06-cancel-", dir=owned_root))
    slow = owned / "검색-취소-전용"
    quick = owned / "검색-재실행-전용"
    slow.mkdir()
    quick.mkdir()
    # 18k owned 1 KiB files force repeated bounded Win32 file reads while
    # remaining under the product's 20k-walk and 16 MiB content budgets.
    # No sleeps or hooks are added to product code.
    payload = b"owned-px06-content-never-matches-" + b"a" * 992
    for index in range(18000):
        (slow / f"px06-cancel-{index:05d}.txt").write_bytes(payload)
    survivor = slow / "px06-cancel-00000.txt"
    sample = quick / "px06-accepted-one.txt"
    sample_bytes = b"px06-test-owned-accepted"
    sample.write_bytes(sample_bytes)
    before_survivor = hashlib.sha256(survivor.read_bytes()).hexdigest()
    mfc = Path(os.environ["APPDATA"]) / "fxfile" / "conf"
    legacy = {name: hashlib.sha256((mfc / name).read_bytes()).digest()
              for name in LEGACY if (mfc / name).is_file()}
    env = os.environ.copy()
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        sub = owned / key.lower()
        sub.mkdir()
        env[key] = str(sub)
    for key in ("FLY_M23_OWNED_SESSION", "FLY_M23_OWNED_DRAG_TEST"):
        env.pop(key, None)
    app = subprocess.Popen([str(exe), str(slow)], cwd=exe.parent, env=env,
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    hwnd = None
    completed = False
    try:
        def view():
            nonlocal hwnd
            assert app.poll() is None, "PX06 owned app exited before search GUI"
            windows = [x for x in Desktop(backend="uia").windows(process=app.pid)
                       if "flyExplorer" in x.window_text()]
            if len(windows) != 1:
                return None
            hwnd = windows[0].handle
            assert owner_pid(hwnd) == app.pid
            return Desktop(backend="uia").window(handle=hwnd)

        win = eventually(view, "PX06 owned WinUI window not found", 25)
        element = lambda name: win.child_window(auto_id=name)
        eventually(lambda: str(slow).casefold() in
                   element("AddressBox").get_value().casefold(),
                   "Owned initial PX06 search folder not active", 22)
        invoke(element("SearchPanelButton"))
        eventually(lambda: element("SearchCancelButton").exists() and
                   element("SearchRunButton").is_enabled(),
                   "PX06 search controls not visible")
        assert not element("SearchCancelButton").is_enabled()
        assert not element("SearchRememberBox").get_toggle_state()
        scope = element("SearchScopeBox")
        scope.set_edit_text(str(slow))
        element("SearchTermBox").set_edit_text("px06-cancel-")
        element("SearchContentBox").set_edit_text(
            "an-owned-needle-not-present-in-any-file")
        invoke(element("SearchRunButton"))
        # Click before the bounded 18k-file content pass is complete.
        eventually(lambda: element("SearchCancelButton").is_enabled(),
                   "Search finished before an actual in-flight cancel", 4)
        assert not element("SearchRunButton").is_enabled()
        assert "직접 탐색" in element("SearchActiveScopeText").window_text()
        assert str(slow).casefold() in (
            element("SearchActiveScopeText").window_text().casefold())
        print("PX06_CANCEL_ACTUALLY_IN_FLIGHT=PASS", flush=True)
        invoke(element("SearchCancelButton"))
        eventually(lambda: "검색을 취소했습니다" in
                   element("SearchCountText").window_text(),
                   "Cancel did not surface canceled state", 5)
        assert not element("SearchCancelButton").is_enabled()
        assert element("SearchRunButton").is_enabled()
        assert not element("SearchLocateButton").is_enabled()
        assert not element("SearchMatches").descendants(control_type="ListItem")
        print("PX06_CANCEL_CLEAR_VISIBLE_RESULTS=PASS", flush=True)

        # Immediately issue an unrelated, tiny scope. The old ticket must
        # never repopulate its stale results or replace this accepted result.
        element("SearchContentBox").set_edit_text("")
        element("SearchTermBox").set_edit_text("px06-accepted-one")
        scope.set_edit_text(str(quick))
        invoke(element("SearchRunButton"))
        eventually(lambda: "검색 결과 1개" in
                   element("SearchCountText").window_text(),
                   "New search did not complete after canceled worker", 20)
        assert str(quick).casefold() in (
            element("SearchActiveScopeText").window_text().casefold())
        assert not element("SearchCancelButton").is_enabled()
        assert element("SearchLocateButton").is_enabled() is False
        # Wait beyond the owned scan's ordinary completion opportunity.
        # A late callback must not change the accepted new-scope summary.
        time.sleep(3)
        assert "검색 결과 1개" in element("SearchCountText").window_text()
        assert str(quick).casefold() in (
            element("SearchActiveScopeText").window_text().casefold())
        assert "px06-accepted-one" in " ".join(
            x.window_text() for x in element("SearchMatches").descendants())
        print("PX06_CANCEL_LATE_RESULT_DID_NOT_REPLACE_NEW_SEARCH=PASS",
              flush=True)
        assert survivor.is_file()
        assert hashlib.sha256(survivor.read_bytes()).hexdigest() == before_survivor
        assert sample.read_bytes() == sample_bytes
        completed = True
    finally:
        if app.poll() is None:
            if hwnd and owner_pid(hwnd) == app.pid:
                user.PostMessageW(hwnd, 0x10, 0, 0)
                try:
                    app.wait(timeout=14)
                except subprocess.TimeoutExpired:
                    app.terminate()
                    app.wait(timeout=6)
            else:
                app.terminate()
                app.wait(timeout=6)
        exited = app.poll() == 0
        unchanged = all((mfc / name).is_file() and
                        hashlib.sha256((mfc / name).read_bytes()).digest()
                        == digest for name, digest in legacy.items())
        files_ok = (survivor.is_file() and
                    hashlib.sha256(survivor.read_bytes()).hexdigest()
                    == before_survivor and sample.read_bytes() == sample_bytes)
        print("PX06_CANCEL_APP_NORMAL_EXIT", exited, flush=True)
        print("PX06_CANCEL_LEGACY_PROFILE_UNCHANGED", unchanged, flush=True)
        print("PX06_CANCEL_OWNED_FILES_PRESERVED", files_ok, flush=True)
        if completed and exited and unchanged and files_ok:
            shutil.rmtree(owned)
            print("PX06_CANCEL_OWNED_WORKSPACE_REMOVED=True", flush=True)
        else:
            print("PX06_CANCEL_OWNED_TEST_RETAINED_FOR_DIAGNOSTIC=True",
                  flush=True)
    return 0 if completed and exited and unchanged and files_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "Release"))
