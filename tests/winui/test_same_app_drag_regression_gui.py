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
    "--item-kind", choices=("file", "folder", "multi-file", "mixed"), default="file",
    help="Exact test-owned physical source item type",
)
direction_parser.add_argument(
    "--collision", choices=("none", "cancel", "keep-both", "skip"), default="none",
    help="Focused right-to-left copy collision decision; never overwrite",
)
arguments = direction_parser.parse_args()
DIRECTION = arguments.direction
REVERSE = DIRECTION == "right-to-left"
ITEM_KIND = arguments.item_kind
COLLISION = arguments.collision
if COLLISION != "none" and (
    not REVERSE or
    (COLLISION == "skip" and ITEM_KIND != "multi-file") or
    (COLLISION != "skip" and ITEM_KIND != "file")
):
    direction_parser.error(
        "collision requires right-to-left file (cancel/keep-both) "
        "or multi-file (skip)"
    )
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
second_source = None
if ITEM_KIND == "multi-file":
    second_source = source_dir / "두번째-한글.txt"
    second_source.write_bytes("owned second file\n".encode("utf-8"))
elif ITEM_KIND == "mixed":
    second_source = source_dir / "혼합-한글-폴더"
    second_source.mkdir()
    (second_source / "하위-폴더").mkdir()
    (second_source / "하위-폴더" / "혼합-한글.txt").write_bytes(
        "owned mixed folder content\n".encode("utf-8"))

# Only the opt-in collision case creates an already existing destination.
# Distinct bytes make silent replacement observable before any approval.
collision_target = target_dir / source.name
collision_bytes = b"existing test-owned destination: must remain unchanged"
if COLLISION != "none":
    collision_target.write_bytes(collision_bytes)
source_bytes = source.read_bytes() if ITEM_KIND == "file" else None

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
    if ITEM_KIND in ("multi-file", "mixed"):
        eventually(
            lambda: row(SOURCE_PANE_ID, second_source.name) is not None,
            "second test-owned ListItem did not render", 10)
        second_row = row(SOURCE_PANE_ID, second_source.name)
        focus_owned(win, win.handle, preview.pid)
        second_row.click_input(pressed="control")
        eventually(
            lambda: source_row.is_selected() and second_row.is_selected(),
            "two owned source rows not simultaneously selected", 5)
        print("M23_OWNED_MULTI_FILE_SELECTED", True, flush=True)

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

    if COLLISION != "none":
        def modal_button(label):
            matches = [
                item for item in win.descendants()
                if item.element_info.control_type == "Button"
                and item.window_text().strip() == label
                and item.element_info.process_id == preview.pid
                and item.is_visible()
            ]
            return matches[0] if len(matches) == 1 else None

        def collision_modal():
            owned_visible_text = [
                item.window_text() for item in win.descendants()
                if item.element_info.process_id == preview.pid
                and item.is_visible()
            ]
            if not any("동일한 이름이 이미 존재합니다" in text
                       for text in owned_visible_text):
                return None
            return modal_button("취소")

        cancel = eventually(
            collision_modal, "drag collision confirmation not displayed", 23)
        approve = modal_button("이름 바꿔 둘 다 유지")
        assert approve is not None, "collision policy must be explicit"
        assert source.read_bytes() == source_bytes
        assert collision_target.read_bytes() == collision_bytes
        assert sorted(p.name for p in target_dir.iterdir()) == [source.name]
        if COLLISION == "skip":
            assert second_source is not None and second_source.is_file()
            assert not (target_dir / second_source.name).exists()

        if COLLISION == "cancel":
            cancel.iface_invoke.Invoke()
            eventually(
                lambda: "파일 작업 확인을 취소했습니다."
                in element("StatusText").window_text(),
                "collision cancellation not acknowledged", 9)
            assert sorted(p.name for p in target_dir.iterdir()) == [source.name]
            print("M23_REVERSE_DRAG_COLLISION_CANCEL_NO_MUTATION=PASS", flush=True)
        elif COLLISION == "skip":
            skip = modal_button("충돌 항목 건너뛰기")
            assert skip is not None, "skip action missing from owned WinUI modal"
            skip.iface_invoke.Invoke()
            # Only the nonconflicting member of the test-owned pair may copy.
            clean_copy = target_dir / second_source.name
            eventually(clean_copy.is_file,
                       "nonconflicting owned drag item not copied after skip", 23)
            eventually(
                lambda: clean_copy.read_bytes() == second_source.read_bytes(),
                "nonconflicting owned drag item bytes incomplete", 15)
            assert sorted(p.name for p in target_dir.iterdir()) == sorted(
                (source.name, second_source.name))
            assert second_source.read_bytes() == (
                b"owned second file\n")
            print("M23_REVERSE_DRAG_COLLISION_SKIP_COPIES_ONLY_CLEAN=PASS",
                  flush=True)
        else:
            approve.iface_invoke.Invoke()

            def keep_both_copy():
                other = [
                    p for p in target_dir.iterdir()
                    if p.is_file() and p.name != source.name
                ]
                return other[0] if len(other) == 1 else None

            unique_copy = eventually(
                keep_both_copy, "drag Keep Both copy missing", 23)
            eventually(
                lambda: unique_copy.read_bytes() == source_bytes,
                "drag Keep Both copy bytes incomplete", 15)
            assert len(list(target_dir.iterdir())) == 2
            print("M23_REVERSE_DRAG_COLLISION_KEEP_BOTH_PRESERVES_TARGET=PASS",
                  flush=True)
        assert source.read_bytes() == source_bytes
        assert collision_target.read_bytes() == collision_bytes
        assert source.is_file() and collision_target.is_file()
    else:
        copied = target_dir / source.name
        eventually(
            lambda: copied.is_dir() if ITEM_KIND == "folder" else copied.is_file(),
            "same-app private-token drag did not copy owned "+ITEM_KIND, 18)
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
        if ITEM_KIND == "folder":
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
        if ITEM_KIND == "multi-file":
            second_copy = target_dir / second_source.name
            eventually(lambda: second_copy.is_file(),
                       "same-app multi-file second item missing", 18)
            assert second_copy.read_bytes() == second_source.read_bytes()
            assert second_source.is_file(), "multi-file drag removed original"
            print("REAL_SAME_APP_PRIVATE_DRAG_MULTI_FILE_COPY", True,
                  flush=True)
        if ITEM_KIND == "mixed":
            second_copy = target_dir / second_source.name
            eventually(
                lambda: (second_copy / "하위-폴더" / "혼합-한글.txt").is_file(),
                "same-app mixed drag folder payload missing", 18)
            assert owned_tree(second_copy) == owned_tree(second_source)
            assert second_source.is_dir(), "mixed drag removed original folder"
            print("REAL_SAME_APP_PRIVATE_DRAG_MIXED_FILE_FOLDER_COPY", True,
                  flush=True)
    print("SAME_APP_DRAG_DIRECTION", DIRECTION, flush=True)
    print("SAME_APP_DRAG_ITEM_KIND", ITEM_KIND, flush=True)
    if COLLISION == "none":
        if REVERSE:
            print("REAL_SAME_APP_PRIVATE_DRAG_RIGHT_TO_LEFT_COPY", True, flush=True)
        print("REAL_SAME_APP_PRIVATE_DRAG_COPY_AFTER_OUTBOUND_SUPPORT", True, flush=True)
    print("SAME_APP_DRAG_COLLISION_POLICY", COLLISION, flush=True)
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
