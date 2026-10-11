"""Invoke only the canonical Properties verb on two disposable files.

Never click an arbitrary Shell extension. All input and WM_CLOSE targets must
belong to the exact owned WinUI app or its freshly spawned context helper.
No clipboard changes, no user filenames, and no inherited app settings.
"""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from time import sleep

import psutil
from PIL import ImageGrab
from pywinauto import Desktop, keyboard
from paths import APP, ROOT, app_exe
from uia_polling import wait_until

LEGACY = (
    "fxfile.conf", "fxfile-main.conf", "fxfile-toolbar.dat",
    "fxfile-coolbar.dat", "fxfile-dlg_state.conf", "fxfile-folder_layout.conf",
)
user = c.windll.user32
user.GetWindowThreadProcessId.argtypes = (w.HWND, c.POINTER(w.DWORD))
user.GetWindowThreadProcessId.restype = w.DWORD


def eventually(fn, name, seconds=12):
    return wait_until(fn, name, seconds=seconds, interval=.2)


def pid_of(hwnd):
    pid = w.DWORD()
    user.GetWindowThreadProcessId(w.HWND(hwnd), c.byref(pid))
    return pid.value


def owned_name(label):
    # Do not match provider-specific "Advanced Properties" verbs.
    text = label.replace("&", "").replace("_", "").strip().casefold()
    return bool(re.match(r"^(properties|속성)(?:$|[\s(（])", text))


def main(config="Release"):
    exe = app_exe(config)
    helper = exe.parent / "FlyShellIsolationHelper.exe"
    assert exe.is_file() and helper.is_file()
    log = ROOT / "logs" / "m24"
    log.mkdir(parents=True, exist_ok=True)
    owned = Path(tempfile.mkdtemp(prefix="properties-owned-", dir=log))
    source = owned / "source"
    source.mkdir()
    a, b = [source / n for n in (
        "properties-test-first-owned.txt", "properties-test-second-owned.txt")]
    a.write_text("owned first\n", encoding="utf-8")
    b.write_text("owned second\n", encoding="utf-8")
    original = {a: a.read_bytes(), b: b.read_bytes()}
    mfc = Path(os.environ["APPDATA"]) / "fxfile" / "conf"
    baseline = {
        name: hashlib.sha256((mfc / name).read_bytes()).digest()
        for name in LEGACY if (mfc / name).is_file()
    }
    env = os.environ.copy()
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        sub = owned / key.lower()
        sub.mkdir()
        env[key] = str(sub)
    for key in ("FLY_M23_OWNED_SESSION", "FLY_M23_OWNED_DRAG_TEST"):
        env.pop(key, None)
    app = subprocess.Popen([str(exe), str(source)],
                           cwd=exe.parent, env=env,
                           stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    helper_process = None
    app_hwnd = None
    dialog_hwnd = None
    completed = False
    try:
        def winui():
            nonlocal app_hwnd
            assert app.poll() is None, "Owned WinUI app exited"
            assert Path(psutil.Process(app.pid).exe()).resolve() == exe.resolve()
            windows = [x for x in Desktop(backend="uia").windows(process=app.pid)
                       if "flyExplorer" in x.window_text()]
            if len(windows) != 1:
                return None
            app_hwnd = windows[0].handle
            return Desktop(backend="uia").window(handle=app_hwnd)

        eventually(lambda: winui() is not None, "Owned app not ready", 23)
        view = winui()
        eventually(
            lambda: str(source).casefold() in
            view.child_window(auto_id="AddressBox").get_value().casefold(),
            "Test-owned folder did not commit", 14)

        def row(label):
            return next((x for x in view.child_window(
                auto_id="LeftFiles").descendants()
                if x.element_info.control_type == "ListItem"
                and label in x.window_text()), None)

        eventually(lambda: row(a.name) is not None and row(b.name) is not None,
                   "Two owned rows missing", 12)
        def select_owned_pair():
            view.set_focus()
            if pid_of(app_hwnd) != app.pid or user.GetForegroundWindow() != app_hwnd:
                return False
            first = row(a.name)
            other = row(b.name)
            if first is None or other is None:
                return False
            try:
                first.select()
                other = row(b.name)
                if other is None:
                    return False
                other.iface_selection_item.AddToSelection()
                first = row(a.name)
                other = row(b.name)
                return (first is not None and other is not None and
                        first.is_selected() and other.is_selected())
            except (AttributeError, RuntimeError):
                return False
        eventually(select_owned_pair, "Two owned siblings not stably selected", 12)
        view.child_window(auto_id="LeftFiles").set_focus()
        assert user.GetForegroundWindow() == app_hwnd
        keyboard.send_keys("+{F10}")

        def spawned():
            nonlocal helper_process
            candidates = []
            for child in psutil.Process(app.pid).children(recursive=False):
                try:
                    if Path(child.exe()).resolve() == helper.resolve() and \
                       "--context-menu" in child.cmdline():
                        candidates.append(child)
                except psutil.Error:
                    pass
            if len(candidates) != 1:
                return False
            helper_process = candidates[0]
            return True

        eventually(spawned, "Two-file Properties Shell helper did not launch", 9)
        def owned_popup():
            hwnd = user.GetForegroundWindow()
            return hwnd if hwnd and pid_of(hwnd) == helper_process.pid else None

        eventually(owned_popup, "Context popup not owned by exact helper", 8)
        popup = owned_popup()
        desktop = Desktop(backend="uia")
        menu = desktop.window(handle=popup)
        roots = [menu]
        # Native #32768 popup menus can be top-level owned windows rather
        # than UIA descendants of the hidden 1x1 foreground owner.
        roots.extend(x for x in desktop.windows(process=helper_process.pid)
                     if x.handle != popup)
        candidates = []
        seen = set()
        summaries = []
        for root in roots:
            try:
                entries = root.descendants()
                matching = 0
                for entry in entries:
                    if entry.element_info.control_type != "MenuItem":
                        continue
                    try:
                        if owned_name(entry.window_text()):
                            matching += 1
                            identity = (root.handle, entry.rectangle().left,
                                        entry.rectangle().top)
                            if identity not in seen:
                                seen.add(identity)
                                candidates.append(entry)
                    except Exception:
                        pass
                summaries.append((root.class_name(), len(entries), matching))
            except Exception as exc:
                summaries.append(("UNAVAILABLE", type(exc).__name__))
        print("OWNED_PROPERTIES_POPUP_UIA_SHAPES", summaries, flush=True)
        if not candidates:
            # Read-only diagnostic: the win32 accessibility/menu wrapper
            # may expose a native popup even when UIA exposes no children.
            try:
                native = Desktop(backend="win32").window(handle=popup)
                win32menu = native.menu()
                print("OWNED_PROPERTIES_WIN32_MENU_INFO",
                      native.class_name(), type(win32menu).__name__,
                      len(win32menu.items()) if win32menu else 0, flush=True)
            except Exception as exc:
                print("OWNED_PROPERTIES_WIN32_MENU_CLASS",
                      type(exc).__name__, flush=True)
        assert len(candidates) == 1, (
            "No unambiguous canonical Properties menu item; do not click",
            len(candidates),
        )
        selected = candidates[0]
        bounds = selected.rectangle()
        assert bounds.width() > 10 and bounds.height() > 8
        assert user.GetForegroundWindow() == popup
        assert pid_of(popup) == helper_process.pid
        selected.click_input()
        print("OWNED_MULTI_PROPERTIES_VERB_CLICKED", True, flush=True)

        def owned_dialog():
            nonlocal dialog_hwnd
            if not helper_process or not helper_process.is_running():
                return False
            for candidate in Desktop(backend="uia").windows(
                    process=helper_process.pid):
                try:
                    hwnd = candidate.handle
                    label = candidate.window_text()
                    if hwnd == popup or not candidate.is_visible():
                        continue
                    if pid_of(hwnd) != helper_process.pid:
                        continue
                    if re.search(r"(properties|속성)", label, re.IGNORECASE):
                        dialog_hwnd = hwnd
                        return True
                except Exception:
                    pass
            return False

        eventually(owned_dialog, "Owned Properties dialog not visible", 18)
        dialog = Desktop(backend="uia").window(handle=dialog_hwnd)
        box = dialog.rectangle()
        assert box.width() >= 220 and box.height() >= 160
        # Capture exactly the newly created Properties window, never desktop.
        image = log / "owned-multi-properties-dialog.png"
        ImageGrab.grab(bbox=(box.left, box.top, box.right, box.bottom),
                       include_layered_windows=True).save(image)
        print("OWNED_MULTI_PROPERTIES_DIALOG_VISIBLE", True, flush=True)
        print("OWNED_MULTI_PROPERTIES_DIALOG_PIXELS",
              box.width(), box.height(), flush=True)
        assert pid_of(dialog_hwnd) == helper_process.pid
        assert user.PostMessageW(dialog_hwnd, 0x10, 0, 0)
        eventually(
            lambda: not any(x.handle == dialog_hwnd for x in
                            Desktop(backend="uia").windows(process=helper_process.pid)),
            "Owned Properties dialog did not close", 12)
        print("OWNED_MULTI_PROPERTIES_DIALOG_CLOSED", True, flush=True)
        eventually(lambda: not helper_process.is_running() or
                   helper_process.status() == "zombie",
                   "Isolated helper did not settle after Properties close", 9)
        assert all(p.read_bytes() == data for p, data in original.items())
        print("OWNED_MULTI_PROPERTIES_SOURCE_UNCHANGED", True, flush=True)
        completed = True
    finally:
        if dialog_hwnd and helper_process and helper_process.is_running():
            if pid_of(dialog_hwnd) == helper_process.pid:
                user.PostMessageW(dialog_hwnd, 0x10, 0, 0)
        if helper_process and helper_process.is_running():
            try:
                if Path(helper_process.exe()).resolve() == helper.resolve() and \
                   "--context-menu" in helper_process.cmdline():
                    helper_process.terminate()
                    helper_process.wait(timeout=6)
            except psutil.Error:
                pass
        if app.poll() is None:
            if app_hwnd and pid_of(app_hwnd) == app.pid:
                user.PostMessageW(app_hwnd, 0x10, 0, 0)
                try:
                    app.wait(timeout=11)
                except subprocess.TimeoutExpired:
                    app.terminate()
                    app.wait(timeout=7)
            else:
                app.terminate()
                app.wait(timeout=7)
        unchanged = all((mfc / name).is_file() and
                        hashlib.sha256((mfc / name).read_bytes()).digest() == digest
                        for name, digest in baseline.items())
        files_unchanged = all(p.is_file() and p.read_bytes() == data
                              for p, data in original.items())
        print("SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL", unchanged, flush=True)
        print("OWNED_MULTI_PROPERTIES_FINAL_FILES_IDENTICAL",
              files_unchanged, flush=True)
        if completed and unchanged and files_unchanged:
            import shutil
            shutil.rmtree(owned)
        else:
            print("OWNED_MULTI_PROPERTIES_FIXTURE_RETAINED", owned, flush=True)
    return 0 if completed and unchanged and files_unchanged else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "Release"))
