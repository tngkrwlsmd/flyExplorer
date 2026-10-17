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
import struct
import time
from uuid import uuid4

from pywinauto import Desktop, keyboard


MODE_IDS = {
    "Type": "ViewGroupByTypeItem",
    "Name": "ViewGroupByNameItem",
    "Size": "ViewGroupBySizeItem",
    "Month": "ViewGroupByMonthItem",
}


def run(*, win, element, safe_click, focus, eventually, left, right):
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

    # The existing WinUI RenderTargetBitmap pipeline writes only RootShell.
    # Desktop PrintWindow/ImageGrab returns blank pixels on this VM.
    capture = os.environ.get("FLY_F05_VISUAL_CAPTURE") == "YES"
    visual_dir = None
    if capture:
        from paths import ROOT
        from PIL import Image
        theme = os.environ.get("FLY_F05_VISUAL_THEME")
        assert theme in ("light", "dark")
        root = ROOT / "logs" / "f05-visual-modes"
        visual_dir = Path(os.environ["FLY_F05_OWNED_XAML_VISUAL_DIR"])
        assert (visual_dir.is_dir() and visual_dir.parent == root and
                visual_dir.name.startswith(theme + "-") and
                not visual_dir.is_symlink() and not root.is_symlink())

    def screenshot(stage):
        if not capture:
            return
        assert stage in ("before", "name", "size", "month", "type",
                         "collapsed", "tab-restored", "off")
        bmp = visual_dir / (stage + ".bmp")
        png = visual_dir / (stage + ".png")
        assert not png.exists() and not png.is_symlink()
        def ready():
            if not bmp.is_file() or bmp.stat().st_size < 4096:
                return None
            try:
                data = bmp.read_bytes()
                if data[:2] != b"BM":
                    return None
                offset = struct.unpack_from("<I", data, 10)[0]
                width, signed_height = struct.unpack_from("<ii", data, 18)
                bits = struct.unpack_from("<H", data, 28)[0]
                if (offset < 54 or width < 640 or signed_height > -350 or
                        bits != 32 or len(data) !=
                        offset + width * -signed_height * 4):
                    return None
                # WinUI RenderTargetBitmap emits a top-down BGRA image.
                # Pillow's generic BI_RGB BMP reader discards the original
                # alpha channel, turning transparent Light backgrounds black.
                img = Image.frombytes(
                    "RGBA", (width, -signed_height), data[offset:],
                    "raw", "BGRA")
                extrema = img.getextrema()
                if (not any(high - low > 32 for low, high in extrema[:3])
                        or extrema[3][1] == 0):
                    return None
                return img
            except (OSError, ValueError, struct.error):
                return None
        image = eventually(ready, "Owned XAML bitmap unavailable: " +
                           stage, 18)
        image.save(png, format="PNG")
        assert 1000 < png.stat().st_size < 3_000_000
        # Diagnostic preview only. This opaque color is not a verified
        # Windows backdrop, so it never establishes composited-pixel PASS.
        background = (248, 248, 248, 255) if theme == "light" else (
            26, 26, 26, 255)
        diagnostic = Image.alpha_composite(
            Image.new("RGBA", image.size, background), image)
        diagnostic.convert("RGB").save(
            visual_dir / ("diagnostic-" + stage + ".png"), format="PNG")
        digest = hashlib.sha256(png.read_bytes()).hexdigest()
        print("F05_VISUAL_RGBA_ALPHA_PRESERVED=True "
              "DIAGNOSTIC_COMPOSITE_NOT_REAL_BACKDROP=True", flush=True)
        print("F05_VISUAL_CAPTURE=" + stage + " THEME=" + theme +
              " SIZE=" + str(image.width) + "x" + str(image.height) +
              " DPI=" + str(user32.GetDpiForWindow(
                  win.wrapper_object().handle)) +
              " SHA256=" + digest + " FILE=" + str(png.relative_to(ROOT)),
              flush=True)

        # Separate opt-in real screen crop; XAML RGBA is not a DWM screenshot.
        # The helper fails closed if the test-owned window is not foreground.
        if (stage in ("name", "size", "month", "type") and
                os.environ.get("FLY_F05_SCREEN_WINDOW_CAPTURE") == "YES"):
            # GUI source contracts cover the grouped left pane; the actual
            # full-window screenshot must additionally wait for the right
            # pane's asynchronously enumerated synthetic fixture.
            def owned_right_pane_ready():
                right_list = element("RightFiles")
                if not right_list.exists(timeout=.1):
                    return False
                texts = [item.window_text()
                         for item in right_list.descendants()
                         if item.element_info.control_type == "ListItem"]
                return all(any(name in text for text in texts)
                           for name in ("Alpha-small.txt", "Mango-medium.md",
                                        "Zebra-large.log"))
            eventually(owned_right_pane_ready,
                       "Right pane synthetic files not ready for screen pixels",
                       14)
            time.sleep(.35)  # Let the enumerated rows' icons settle.
            from owned_f05_compositor import attempt_capture
            attempt_capture(win=win, process_id=process_id, visual_dir=visual_dir,
                            stage=stage, theme=theme, focus=focus,
                            owned_foreground=owned_foreground)

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
        assert mode in MODE_IDS
        # UIA discovery and asynchronous XAML rendering do not guarantee
        # that this specific test-owned window remains the foreground HWND.
        # Reacquire owned focus before using physical keyboard input.
        focus()
        assert owned_foreground(), (
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
    # The opt-in visual Type fixture may already be grouped by WinUI's
    # dispatcher before Python reaches this pre-grouping checkpoint.
    if not (capture and
            os.environ.get("FLY_F05_VISUAL_GROUP_MODE_ONLY") == "type"):
        assert heading(".md") is None

    screenshot("before")
    if os.environ.get("FLY_F05_KEYBOARD_DISCLOSURE_ONLY") == "YES":
        # Physical keyboard input is separate from the app-side visual fixture.
        assert not capture, "Keyboard disclosure is a separate GUI gate"
        set_mode("Type")
        eventually(lambda: heading(".md") is not None
                   and file_row("Mango-medium.md") is not None,
                   "Keyboard fixture type group not ready", 12)
        focus()
        disclosure = eventually(lambda: heading(".md"),
                                "Owned Markdown disclosure missing", 9)
        disclosure.set_focus()
        assert owned_foreground(), "Refusing Space outside owned F05 GUI"
        keyboard.send_keys("{SPACE}")
        eventually(lambda: file_row("Mango-medium.md") is None,
                   "Space did not collapse Markdown group", 9)
        assert heading(".md") is not None
        print("F05_KEYBOARD_SPACE_COLLAPSE=PASS", flush=True)

        focus()
        disclosure = eventually(lambda: heading(".md"),
                                "Collapsed Markdown disclosure missing", 9)
        disclosure.set_focus()
        assert owned_foreground(), "Refusing Enter outside owned F05 GUI"
        keyboard.send_keys("{ENTER}")
        eventually(lambda: file_row("Mango-medium.md") is not None,
                   "Enter did not expand Markdown group", 9)
        print("F05_KEYBOARD_ENTER_EXPAND=PASS", flush=True)
        return

    if capture and os.environ.get("FLY_F05_SCREEN_PHYSICAL_TYPE_ONLY") == "YES":
        # Read the initial model projection before sending a single input.
        # The first pane's directory must already be fully test-owned.
        right_control = element("RightFiles")
        initial = [x for x in right_control.descendants()
                   if x.element_info.control_type == "ListItem"]
        print("F05_PHYSICAL_TYPE_INITIAL_RIGHT_ITEMS=" + str(len(initial)),
              flush=True)
        # Use the already established independent-pane navigation from
        # test_shell_gui: activate only this owned right surface, visit the
        # synthetic /Right folder and await a real helper-delivered row.
        safe_click(right_control)
        eventually(lambda: "오른쪽" in element("ActivePaneText").window_text(),
                   "Right pane failed test-owned activation", 8)
        address = element("AddressBox")
        address.set_edit_text(str(right))
        focus()
        address.type_keys("{ENTER}", set_foreground=True)
        eventually(lambda: str(right).casefold() in
                   element("AddressBox").get_value().casefold(),
                   "Right pane did not accept owned folder address", 10)
        eventually(lambda: any(
                   p.element_info.control_type == "ListItem" and
                   "Secondary" in p.window_text()
                   for p in element("RightFiles").descendants()),
                   "Explicit right Shell navigation did not project row", 16)
        print("F05_PHYSICAL_TYPE_EXPLICIT_RIGHT_NAV=PASS", flush=True)
        safe_click(element("LeftFiles"))
        eventually(lambda: str(left).casefold() in
                   element("AddressBox").get_value().casefold(),
                   "Left pane not preserved after explicit right navigation", 8)
        set_mode("Type")
        eventually(lambda: all(heading(x) is not None
                   for x in (".txt", ".md", ".log")),
                   "Physical View Type headings never appeared", 12)
        screenshot("type")
        assert file_row("Mango-medium.md") is not None
        print("F05_PHYSICAL_TYPE_MENU_GROUPING_AND_SCREEN=PASS", flush=True)
        return

    if capture and os.environ.get("FLY_F05_VISUAL_BASELINE_ONLY") == "YES":
        # No physical input when the interactive user is not foreground.
        print("F05_VISUAL_BASELINE_ONLY=PASS", flush=True)
        return
    if capture and os.environ.get("FLY_F05_VISUAL_GROUP_MODE_ONLY"):
        mode = os.environ["FLY_F05_VISUAL_GROUP_MODE_ONLY"]
        titles = {
            "name": ("A–F", "M–R", "S–Z", "가–힣"),
            "size": ("10 KB 미만", "10 KB–1 MB", "1–100 MB"),
            "month": ("2026년 7월", "2026년 8월", "2026년 9월"),
            "type": (".txt", ".md", ".log"),
        }
        assert mode in titles
        # WinUI itself triggers this opt-in visual fixture after the
        # entire synthetic metadata model is ready. This is NOT an
        # interactive View-menu input acceptance test.
        eventually(lambda: all(heading(name) is not None
                               for name in titles[mode]),
                   "Owned visual fixture group headings missing: " +
                   mode, 21)
        screenshot(mode)
        assert file_row("Alpha-small.txt") is not None
        print("F05_VISUAL_GROUP_FIXTURE_MODE=" + mode +
              " PASS_NO_PHYSICAL_INPUT=True", flush=True)
        return
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
