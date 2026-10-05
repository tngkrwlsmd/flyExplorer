"""Owned WinUI bookmark persistence/import/navigation acceptance."""
from pathlib import Path
from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile
from uia_polling import wait_until
import ctypes as c
import os
import shutil
import subprocess
import tempfile
import time
from ctypes import wintypes as W
from pywinauto import Desktop
from PIL import ImageGrab

CONFIG = os.environ.get("FLY_MIGRATION_CONFIGURATION", "Release")
assert CONFIG in ("Debug", "Release")
EXE = app_exe(CONFIG)
assert EXE.exists(), EXE
BASE = ROOT / "logs" / "bookmark-owned"
BASE.mkdir(parents=True, exist_ok=True)
owned = Path(tempfile.mkdtemp(prefix="bookmark-owned-", dir=BASE))
source = owned / "북마크원본"
other = owned / "다른폴더"
imported = owned / "가져온폴더"
for folder in (source, other, imported):
    folder.mkdir(parents=True, exist_ok=True)
(source / "owned.txt").write_text("bookmark owned", encoding="utf-8")
appdata = owned / "appdata"
localdata = owned / "localdata"
tmp = owned / "tmp"
for folder in (appdata, localdata, tmp):
    folder.mkdir()
profile = localdata / "flyExplorer"
profile.mkdir()
(profile / "ui-preferences-v1.txt").write_bytes(
    b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=details\r\n"
)
legacy = owned / "legacy-bookmark.conf"
legacy.write_text(
    "[bookmark]\r\n"
    "bookmark.item1.name=가져온 북마크\r\n"
    f"bookmark.item1.path={imported}\r\n",
    encoding="utf-16",
    newline="",
)

real_conf, before = snapshot_legacy_profile()
u = c.windll.user32
CALL = c.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
u.EnumWindows.argtypes = [CALL, W.LPARAM]
u.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
u.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
u.SetWindowPos.argtypes = [W.HWND, W.HWND, c.c_int, c.c_int,
                           c.c_int, c.c_int, W.UINT]

def windows(pid):
    found = []
    @CALL
    def callback(hwnd, _):
        owner = W.DWORD()
        u.GetWindowThreadProcessId(hwnd, c.byref(owner))
        if owner.value == pid and u.IsWindowVisible(hwnd):
            found.append(int(hwnd))
        return 1
    u.EnumWindows(callback, 0)
    return found

def eventually(fn, label, timeout=10):
    return wait_until(fn, label, seconds=timeout, interval=.15)

def launch(start):
    env = {
        **os.environ,
        "APPDATA": str(appdata),
        "LOCALAPPDATA": str(localdata),
        "TEMP": str(tmp),
        "TMP": str(tmp),
    }
    process = subprocess.Popen(
        [str(EXE), str(start)], cwd=EXE.parent, env=env,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    eventually(lambda: bool(windows(process.pid)) or process.poll() is not None,
               "bookmark WinUI window did not appear")
    assert process.poll() is None, process.returncode
    hwnd = windows(process.pid)[0]
    u.SetWindowPos(hwnd, 0, 120, 70, 972, 720, 0x0040)
    win = Desktop(backend="uia").window(handle=hwnd)
    element = lambda name: win.child_window(auto_id=name)
    eventually(lambda: str(start).lower() in
               element("AddressBox").get_value().lower(),
               "bookmark fixture did not finish initial navigation", 18)
    return process, hwnd, win, element

def close(process, hwnd):
    u.PostMessageW(hwnd, 0x0010, 0, 0)
    process.wait(timeout=12)
    assert process.returncode == 0, process.returncode

def invoke(target):
    try:
        target.invoke()
    except Exception:
        target.click()

def titled_button(win, title):
    expected = {title, f"북마크 {title}"}
    matches = [x for x in win.descendants(control_type="Button")
               if x.window_text() in expected]
    return matches[0] if matches else None

p = None
hwnd = None
p2 = None
hwnd2 = None
try:
    p, hwnd, win, element = launch(source)
    for key in ("BookmarkButtonsPanel", "AddBookmarkButton",
                "BookmarkManagerButton"):
        assert element(key).exists(timeout=5), key

    invoke(element("AddBookmarkButton"))
    eventually(lambda: titled_button(win, "북마크원본") is not None,
               "current folder bookmark was not added")

    invoke(element("BookmarkManagerButton"))
    eventually(lambda: element("BookmarkManagerBox").exists() and
               element("BookmarkNameEdit").exists(),
               "bookmark manager controls did not open")
    element("BookmarkNameEdit").set_edit_text("자주 쓰는 폴더")
    invoke(element("BookmarkRenameButton"))
    eventually(lambda: titled_button(win, "자주 쓰는 폴더") is not None,
               "bookmark rename did not reach toolbar")

    address = element("AddressBox")
    address.set_edit_text(str(other))
    address.type_keys("{ENTER}", set_foreground=True)
    eventually(lambda: str(other).lower() in address.get_value().lower(),
               "navigation away from bookmarked folder failed", 15)
    invoke(titled_button(win, "자주 쓰는 폴더"))
    eventually(lambda: str(source).lower() in address.get_value().lower(),
               "bookmark toolbar navigation failed", 15)

    element("BookmarkImportPathBox").set_edit_text(str(legacy))
    invoke(element("BookmarkImportButton"))
    eventually(lambda: titled_button(win, "가져온 북마크") is not None,
               "legacy bookmark import did not reach toolbar")

    element("BookmarkManagerBox").select(0)
    invoke(element("BookmarkDeleteButton"))
    eventually(lambda: titled_button(win, "자주 쓰는 폴더") is None,
               "bookmark delete did not remove toolbar item")
    assert titled_button(win, "가져온 북마크") is not None

    invoke(element("BookmarkManagerButton"))
    capture = os.environ.get("FLY_BOOKMARK_SCREENSHOT")
    if capture:
        rect = win.rectangle()
        ImageGrab.grab(
            bbox=(rect.left, rect.top, rect.right, rect.bottom),
            include_layered_windows=True,
        ).save(capture)

    store_file = localdata / "flyExplorer" / "bookmarks-v1.txt"
    eventually(store_file.exists, "private bookmark file was not created")
    close(p, hwnd)
    p = hwnd = None
    print("OWNED_BOOKMARK_ADD_RENAME_DELETE_IMPORT", True, flush=True)

    p2, hwnd2, win2, element2 = launch(other)
    eventually(lambda: titled_button(win2, "가져온 북마크") is not None,
               "persisted bookmark did not reload after restart")
    invoke(titled_button(win2, "가져온 북마크"))
    eventually(lambda: str(imported).lower() in
               element2("AddressBox").get_value().lower(),
               "reloaded bookmark did not navigate to imported folder", 15)
    close(p2, hwnd2)
    p2 = hwnd2 = None
    print("OWNED_BOOKMARK_RESTART_PERSISTENCE", True, flush=True)

    assert_legacy_profile_unchanged(real_conf, before)
    print("ORIGINAL_BOOKMARK_TEST_USER_CONFIG_SHA256_IDENTICAL", True, flush=True)
finally:
    for process, handle in ((p, hwnd), (p2, hwnd2)):
        if process is not None and process.poll() is None:
            if handle:
                u.PostMessageW(handle, 0x0010, 0, 0)
            try:
                process.wait(timeout=5)
            except Exception:
                process.kill()
    shutil.rmtree(owned, ignore_errors=True)
