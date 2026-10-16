"""Owned WinUI F05 extended acceptance; four modes + per-tab collapse restore.

Called only with FLY_F05_MODES_ONLY=YES by the disposable test_shell_gui
harness. Never uses real folders, machine preferences, or OS display settings.
Requires fresh Windows Release after product integration, not a legacy binary.
"""
import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path
import time
from uuid import uuid4

from pywinauto import Desktop, keyboard


MODE_IDS = {
    "Type": "ViewGroupByTypeItem",
    "Name": "ViewGroupByNameItem",
    "Size": "ViewGroupBySizeItem",
    "Month": "ViewGroupByMonthItem",
}


def run(*, win, element, safe_click, eventually, left, right):
    assert left.parent == right.parent and left.name == "Left"
    assert right.name == "Right" and (left / "Nested").is_dir()
    owned_files = ("Alpha-small.txt", "Mango-medium.md", "Zebra-large.log",
                   "가나다-note.txt")
    assert all((left / name).is_file() for name in owned_files)
    process_id = win.wrapper_object().element_info.process_id
    assert process_id > 0
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.WindowFromPoint.argtypes = [wintypes.POINT]
    user32.WindowFromPoint.restype = wintypes.HWND

    def owned_foreground():
        foreground = user32.GetForegroundWindow()
        pid = wintypes.DWORD()
        if foreground:
            user32.GetWindowThreadProcessId(foreground, ctypes.byref(pid))
        return pid.value == process_id

    # Optional actual-window pixels, only in the synthetic F05 GUI fixture.
    capture = os.environ.get("FLY_F05_VISUAL_CAPTURE") == "YES"
    visual_dir = None
    if capture:
        from paths import ROOT
        from PIL import ImageGrab
        theme = os.environ.get("FLY_F05_VISUAL_THEME")
        assert theme in ("light", "dark")
        root = ROOT / "logs" / "f05-visual-modes"
        assert not root.is_symlink() and not ROOT.is_symlink()
        root.mkdir(parents=True, exist_ok=True)
        visual_dir = root / (theme + "-" + uuid4().hex)
        visual_dir.mkdir()

    def screenshot(stage):
        if not capture:
            return
        assert owned_foreground(), "Refusing screenshot of any other desktop"
        rect = win.rectangle()
        desktop_w = user32.GetSystemMetrics(0)
        desktop_h = user32.GetSystemMetrics(1)
        assert (0 <= rect.left < rect.right <= desktop_w and
                0 <= rect.top < rect.bottom <= desktop_h and
                rect.width() >= 640 and rect.height() >= 350), (
                    "Actual WinUI window is not wholly within desktop",
                    (rect.left, rect.top, rect.right, rect.bottom),
                    (desktop_w, desktop_h))
        time.sleep(.18)  # Let the settled UIA state composite before grabbing.
        png = visual_dir / (stage + ".png")
        assert not png.exists() and png.parent == visual_dir
        image = ImageGrab.grab(
            bbox=(rect.left, rect.top, rect.right, rect.bottom),
            include_layered_windows=True)
        assert image.width == rect.width() and image.height == rect.height()
        image.save(png, format="PNG")
        assert 1000 < png.stat().st_size < 3_000_000
        digest = hashlib.sha256(png.read_bytes()).hexdigest()
        print("F05_VISUAL_CAPTURE=" + stage + " THEME=" + theme +
              " SIZE=" + str(image.width) + "x" + str(image.height) +
              " DPI=" + str(user32.GetDpiForWindow(win.wrapper_object().handle)) +
              " SHA256=" + digest + " FILE=" + str(png.relative_to(ROOT)),
              flush=True)

    def file_row(name):
        for candidate in element("LeftFiles").descendants():
            if (candidate.element_info.control_type == "ListItem"
                    and name in candidate.window_text()):
                return candidate
        return None

    def heading(title):
        for candidate in element("LeftFiles").descendants():
            if (candidate.element_info.control_type == "Button"
                    and title in candidate.window_text()):
                return candidate
        return None

    def live_menu(automation_id):
        # A dismissed WinUI flyout can leave a stale UIA peer. Inspect the
        # currently onscreen popup in the test-owned process only.
        for top in Desktop(backend="uia").windows():
            if top.element_info.process_id != process_id:
                continue
            for child in [top, *top.descendants()]:
                if child.element_info.automation_id != automation_id:
                    continue
                try:
                    rectangle = child.rectangle()
                    if (not child.is_visible() or rectangle.width() < 12
                            or rectangle.height() < 12):
                        continue
                    point = rectangle.mid_point()
                    hwnd = user32.WindowFromPoint(
                        wintypes.POINT(point.x, point.y))
                    pid = wintypes.DWORD()
                    if hwnd:
                        user32.GetWindowThreadProcessId(hwnd,
                                                         ctypes.byref(pid))
                    if pid.value == process_id:
                        return child
                except (AttributeError, RuntimeError, ValueError):
                    continue
        return None

    def set_mode(mode):
        assert mode in MODE_IDS and owned_foreground(), (
            "Refusing View flyout keys outside the owned process")
        element("ViewButton").invoke()
        menu = eventually(lambda: live_menu(MODE_IDS[mode]),
                          "Owned F05 menu missing: " + mode, 9)
        assert menu.element_info.process_id == process_id
        menu.set_focus()
        assert owned_foreground(), "Focus moved outside the test-owned app"
        keyboard.send_keys("{ENTER}")
        print("F05_MODE_OWNED_ENTER=" + mode, flush=True)

    eventually(lambda: all(file_row(name) is not None for name in owned_files),
               "Owned F05 grouping fixture files missing", 15)
    # The isolated metadata worker is asynchronous. Allow the small, owned
    # fixture to settle without modifying system settings or user files.
    time.sleep(.8)
    assert heading(".md") is None

    screenshot("before")
    set_mode("Name")
    eventually(lambda: all(heading(title) is not None for title in
                           ("A–F", "M–R", "S–Z", "가–힣")),
               "Name grouping headings missing", 12)
    assert heading(".md") is None
    print("F05_GUI_GROUP_NAME=PASS", flush=True)
    screenshot("name")

    set_mode("Size")
    eventually(lambda: all(heading(title) is not None for title in
                           ("10 KB 미만", "10 KB–1 MB", "1–100 MB")),
               "Size grouping headings missing", 12)
    assert heading("A–F") is None
    print("F05_GUI_GROUP_SIZE=PASS", flush=True)
    screenshot("size")

    set_mode("Month")
    eventually(lambda: all(heading(title) is not None for title in
                           ("2026년 7월", "2026년 8월", "2026년 9월")),
               "Modified-month grouping headings missing", 12)
    assert heading("10 KB 미만") is None
    print("F05_GUI_GROUP_MODIFIED_MONTH=PASS", flush=True)
    screenshot("month")

    set_mode("Type")
    eventually(lambda: all(heading(title) is not None for title in
                           (".txt", ".md", ".log")),
               "Type regression grouping headings missing", 12)
    assert heading("2026년 7월") is None
    print("F05_GUI_GROUP_TYPE_REGRESSION=PASS", flush=True)
    screenshot("type")

    safe_click(heading(".md"))
    eventually(lambda: file_row("Mango-medium.md") is None,
               "Markdown collapsed file remained selectable", 9)
    assert file_row("Alpha-small.txt") is not None
    print("F05_GUI_COLLAPSE_REAL_FILE_ONLY=PASS", flush=True)
    screenshot("collapsed")

    def left_tabs():
        peers = [p for p in element("LeftTabs").descendants()
                 if p.element_info.control_type == "TabItem"]
        assert all(p.element_info.process_id == process_id for p in peers)
        return peers

    count = len(left_tabs())
    assert 1 <= count < 32
    safe_click(element("NewTabButton"))
    eventually(lambda: len(left_tabs()) == count + 1,
               "New left tab not created", 10)
    eventually(lambda: file_row("Mango-medium.md") is not None,
               "New tab did not show its uncategorized owned file", 13)
    assert heading(".md") is None, "New tab inherited old group's state"
    print("F05_GUI_NEW_TAB_UNGROUPED=PASS", flush=True)

    safe_click(left_tabs()[0])
    eventually(lambda: heading(".md") is not None
               and file_row("Mango-medium.md") is None,
               "Original tab did not restore collapsed Markdown group", 15)
    print("F05_GUI_PER_TAB_COLLAPSE_RESTORED=PASS", flush=True)
    screenshot("tab-restored")

    safe_click(left_tabs()[-1])
    eventually(lambda: file_row("Mango-medium.md") is not None,
               "New tab not restored after switching", 12)
    assert heading(".md") is None
    safe_click(element("CloseTabButton"))
    eventually(lambda: len(left_tabs()) == count,
               "New tab close failed", 10)
    eventually(lambda: heading(".md") is not None
               and file_row("Mango-medium.md") is None,
               "Closing new tab changed original collapse state", 13)
    print("F05_GUI_TAB_CLOSE_COHERENCE=PASS", flush=True)

    set_mode("Type")  # selecting active mode again is explicit opt-out
    eventually(lambda: heading(".md") is None
               and file_row("Mango-medium.md") is not None,
               "Explicit type grouping off failed", 10)
    print("F05_GUI_GROUP_EXPLICIT_OFF=PASS", flush=True)
    screenshot("off")
