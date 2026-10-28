"""Focused same-app physical drag regression after outbound StorageItems support."""

from pathlib import Path
import argparse
import ctypes as c
from ctypes import wintypes as W
import os
import subprocess
import tempfile
import time

from pywinauto import Desktop, mouse

from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile
from uia_polling import wait_until


direction_parser = argparse.ArgumentParser(description=__doc__)
direction_parser.add_argument(
    "--direction", choices=("left-to-right", "right-to-left"),
    default="left-to-right",
    help="Exact test-owned source and destination pane direction",
)
direction_parser.add_argument(
    "--item-kind", choices=("file", "folder"), default="file",
    help="Exact test-owned physical source item type",
)
arguments = direction_parser.parse_args()
DIRECTION = arguments.direction
REVERSE = DIRECTION == "right-to-left"
ITEM_KIND = arguments.item_kind
SOURCE_PANE_ID = "RightFiles" if REVERSE else "LeftFiles"
TARGET_PANE_ID = "LeftFiles" if REVERSE else "RightFiles"

CONFIG = os.environ.get("FLY_MIGRATION_CONFIGURATION", "Release")
assert CONFIG in ("Debug", "Release")
EXE = app_exe(CONFIG)
assert EXE.is_file(), EXE

REAL_CONF, ORIGINAL_PROFILE = snapshot_legacy_profile()
base = ROOT / "logs" / "same-app-drag-gui"
base.mkdir(parents=True, exist_ok=True)
owned = Path(tempfile.mkdtemp(prefix="same-app-drag-owned-", dir=base))
left = owned / "left"
right = owned / "right"
left.mkdir()
right.mkdir()
source_dir = right if REVERSE else left
target_dir = left if REVERSE else right
source = source_dir / (
    "내부끌기-한글-폴더" if ITEM_KIND == "folder"
    else "내부끌기-한글.txt"
)
if ITEM_KIND == "folder":
    source.mkdir()
    nested = source / "하위-폴더"
    nested.mkdir()
    (nested / "한글-payload.txt").write_bytes(
        "owned nested same-app folder drag\n".encode("utf-8"))
    (source / "root-payload.bin").write_bytes(b"owned folder root\x00\xfe")
else:
    source.write_text("owned same-app drag\n", encoding="utf-8")

env = os.environ.copy()
for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
    folder = owned / key.lower()
    folder.mkdir()
    env[key] = str(folder)
env["FLY_M23_OWNED_DRAG_TRACE"] = "YES"

u = c.WinDLL("user32", use_last_error=True)
u.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
u.GetWindowThreadProcessId.restype = W.DWORD
u.GetForegroundWindow.restype = W.HWND
u.GetAncestor.argtypes = [W.HWND, W.UINT]
u.GetAncestor.restype = W.HWND
u.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
u.PostMessageW.restype = W.BOOL


def eventually(fn, label, seconds=15):
    return wait_until(fn, label, seconds=seconds, interval=.15)


def foreground_root():
    hwnd = u.GetForegroundWindow()
    return int(u.GetAncestor(hwnd, 2)) if hwnd else 0


def focus_owned(window, hwnd, pid):
    window.set_focus()
    eventually(lambda: foreground_root() == int(hwnd),
               "owned flyExplorer did not reach foreground", 5)
    owner = W.DWORD()
    u.GetWindowThreadProcessId(W.HWND(hwnd), c.byref(owner))
    assert owner.value == pid, "owned flyExplorer HWND PID mismatch"


preview = None
win = None
try:
    import psutil

    preview = subprocess.Popen(
        [str(EXE), str(left)],
        cwd=EXE.parent,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    def ready_window():
        global win
        if preview.poll() is not None:
            return False
        if Path(psutil.Process(preview.pid).exe()).resolve() != EXE.resolve():
            raise AssertionError("flyExplorer process ownership mismatch")
        candidates = [
            item for item in Desktop(backend="uia").windows(process=preview.pid)
            if "flyExplorer" in item.window_text()
        ]
        if len(candidates) != 1:
            return False
        win = Desktop(backend="uia").window(handle=candidates[0].handle)
        return bool(win.exists(timeout=.2))

    eventually(ready_window, "owned flyExplorer window not ready", 20)

    def element(auto_id):
        matches = [
            item for item in win.descendants()
            if item.element_info.automation_id == auto_id
            and item.is_visible()
        ]
        if not matches:
            raise AssertionError("missing visible control: " + auto_id)
        # WinUI can retain virtualized/transitioning peers. The visible peer
        # with the largest non-empty rectangle is the live interaction surface.
        def area(item):
            rect = item.rectangle()
            return max(0, rect.width()) * max(0, rect.height())
        return max(matches, key=area)

    def row(side_id, name):
        return next(
            (
                item for item in element(side_id).descendants()
                if item.element_info.control_type == "ListItem"
                and name in item.window_text()
                and item.is_visible()
            ),
            None,
        )

    def visit(side_id, path, expected_name=None):
        focus_owned(win, win.handle, preview.pid)
        element(side_id).click_input()
        address = element("AddressBox")
        address.set_edit_text(str(path))
        focus_owned(win, win.handle, preview.pid)
        address.type_keys("{ENTER}", set_foreground=True)
        eventually(
            lambda: str(path).rstrip("\\/").casefold()
            in element("AddressBox").get_value().rstrip("\\/").casefold(),
            "owned pane route did not load: " + side_id,
            18,
        )
        if expected_name is not None:
            eventually(
                lambda: row(side_id, expected_name) is not None,
                "owned row did not render after explicit route: " + expected_name,
                18,
            )

    # Reassert both owned routes explicitly. This avoids relying on UIA peer
    # identity across an AddressBox navigation and keeps the regression focused
    # on the physical drag rather than pane-routing state.
    visit("LeftFiles", left, source.name if not REVERSE else None)
    visit("RightFiles", right, source.name if REVERSE else None)
    visit(SOURCE_PANE_ID, source_dir, source.name)
    source_row = row(SOURCE_PANE_ID, source.name)
    source_row.select()

    origin = source_row.rectangle().mid_point()
    rr = element(TARGET_PANE_ID).rectangle()
    target = (
        rr.left + min(150, max(40, int(rr.width() * .35))),
        rr.top + min(180, max(55, int(rr.height() * .45))),
    )

    focus_owned(win, win.handle, preview.pid)
    mouse.move(coords=(origin.x, origin.y))
    mouse.press(button="left", coords=(origin.x, origin.y))
    try:
        time.sleep(.14)
        mouse.move(coords=(origin.x + 30, origin.y + 20))
        time.sleep(.25)
        mouse.move(coords=target)
        time.sleep(.35)
    finally:
        mouse.release(button="left", coords=target)

    copied = target_dir / source.name
    eventually(lambda: copied.is_file(),
               "same-app private-token drag did not copy owned file", 18)
    if ITEM_KIND == "folder":
        def owned_tree(root):
            assert root.is_dir() and not root.is_symlink()
            children = {}
            for child in sorted(root.rglob("*")):
                assert not child.is_symlink(), "owned tree may not contain links"
                relative = child.relative_to(root).as_posix()
                children[relative] = (
                    ("dir", None) if child.is_dir()
                    else ("file", child.read_bytes())
                )
            return children
        eventually(
            lambda: (copied / "하위-폴더" / "한글-payload.txt").is_file()
            and (copied / "root-payload.bin").is_file(),
            "same-app owned nested folder drag did not finish", 18)
        assert owned_tree(copied) == owned_tree(source), (
            "copied folder contents differ from owned source")
        print("REAL_SAME_APP_PRIVATE_DRAG_NESTED_FOLDER_COPY", True,
              flush=True)
    else:
        assert copied.read_bytes() == source.read_bytes()
        assert source.is_file(), "same-app copy drag must preserve source"
    assert source.exists(), "same-app copy drag must preserve source"
    assert source.parent == source_dir and copied.parent == target_dir
    print("SAME_APP_DRAG_DIRECTION", DIRECTION, flush=True)
    print("SAME_APP_DRAG_ITEM_KIND", ITEM_KIND, flush=True)
    if REVERSE:
        print("REAL_SAME_APP_PRIVATE_DRAG_RIGHT_TO_LEFT_COPY", True, flush=True)

    print("REAL_SAME_APP_PRIVATE_DRAG_COPY_AFTER_OUTBOUND_SUPPORT", True, flush=True)
    print("SAME_APP_DRAG_REGRESSION=PASS", flush=True)
finally:
    if preview and preview.poll() is None:
        hwnd = win.handle if win is not None else 0
        if hwnd:
            owner = W.DWORD()
            u.GetWindowThreadProcessId(W.HWND(hwnd), c.byref(owner))
            assert owner.value == preview.pid, "refuse closing foreign window"
            assert u.PostMessageW(W.HWND(hwnd), 0x10, 0, 0)
        try:
            preview.wait(timeout=14)
        except subprocess.TimeoutExpired:
            preview.terminate()
            preview.wait(timeout=5)
            raise AssertionError("owned flyExplorer did not close normally")
    if preview:
        assert preview.returncode == 0, preview.returncode
    assert_legacy_profile_unchanged(REAL_CONF, ORIGINAL_PROFILE)
