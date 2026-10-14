"""Owned F01-C actual Shell hidden-file/hidden-folder and View-menu test.

Runs through test_shell_gui.py ONLY with FLY_F01_HIDDEN_ONLY=YES.
All filesystem attributes are assigned to disposable test-owned fixtures
before process launch; no Explorer settings, registry or user files touched.
"""
from pathlib import Path
import ctypes as ct
from ctypes import wintypes as W

from PIL import ImageGrab
from pywinauto import Desktop


def run(*, win, element, safe_click, focus, eventually, base, owned, left, right):
    assert Path(left).is_relative_to(owned) and Path(right).is_relative_to(owned)
    pid = win.wrapper_object().element_info.process_id
    assert pid > 0
    user = ct.windll.user32
    user.GetForegroundWindow.restype = W.HWND
    user.GetWindowThreadProcessId.argtypes = [W.HWND, ct.POINTER(W.DWORD)]
    user.GetDpiForWindow.argtypes = [W.HWND]
    user.GetDpiForWindow.restype = W.UINT
    ui = Desktop(backend="uia")

    def guarded_foreground():
        focus()
        fg = user.GetForegroundWindow()
        owner = W.DWORD()
        if fg:
            user.GetWindowThreadProcessId(fg, ct.byref(owner))
        assert fg and owner.value == pid, "foreign foreground: refuse PNG or keyboard"

    def rows(side):
        return [r for r in element("LeftFiles" if side == 0 else "RightFiles").descendants()
                if r.element_info.control_type == "ListItem"]

    def find_row(side, name):
        return next((r for r in rows(side) if name in r.window_text()), None)

    def absent(side):
        return all("hidden-note.txt" not in r.window_text() and
                   "HiddenOwnedFolder" not in r.window_text()
                   for r in rows(side))

    def visible(side):
        file = find_row(side, "hidden-note.txt")
        folder = find_row(side, "HiddenOwnedFolder")
        return bool(file and folder and
                    "숨김 항목" in file.window_text() and
                    "숨김 항목" in folder.window_text())

    def menu():
        guarded_foreground()
        safe_click(element("ViewButton"))
        def lookup():
            local = element("ViewHiddenItemsItem")
            if local.exists(timeout=.10):
                return local.wrapper_object()
            candidates = [x for w in ui.windows(process=pid) for x in w.descendants()
                          if x.element_info.process_id == pid and
                          x.element_info.automation_id == "ViewHiddenItemsItem"]
            return candidates[0] if len(candidates) == 1 else None
        target = eventually(lookup, "View hidden toggle not published", 8)
        assert target.element_info.process_id == pid
        assert target.element_info.automation_id == "ViewHiddenItemsItem"
        return target

    def checked(expected):
        target = menu()
        actual = int(target.iface_toggle.CurrentToggleState)
        assert actual == int(expected), (expected, actual)
        # Escape belongs only to owned foreground app UI.
        from pywinauto.keyboard import send_keys
        guarded_foreground()
        send_keys("{ESC}", pause=.06)

    def toggle():
        target = menu()
        target.iface_toggle.Toggle()
        eventually(lambda: "숨김 항목" in element("StatusText").window_text(),
                   "owned hidden toggle did not dispatch", 8)

    # Match the previously accepted real 96-DPI WinUI captures; change
    # only our own HWND, never the OS desktop or another process's window.
    user.SetWindowPos.argtypes = [W.HWND, W.HWND, ct.c_int, ct.c_int,
                                  ct.c_int, ct.c_int, W.UINT]
    width = min(940, user.GetSystemMetrics(0)-75)
    height = min(610, user.GetSystemMetrics(1)-85)
    assert width >= 800 and height >= 550
    guarded_foreground()
    assert user.SetWindowPos(win.handle, None, 35, 35, width, height, 0x0014)
    eventually(lambda: abs(win.rectangle().width()-width) <= 3 and
               abs(win.rectangle().height()-height) <= 3,
               "test-owned screenshot HWND size not stable", 8)

    def shot(state, flyout_open=False):
        if not flyout_open:
            guarded_foreground()
        else:
            fg = user.GetForegroundWindow()
            owner = W.DWORD()
            if fg:
                user.GetWindowThreadProcessId(fg, ct.byref(owner))
            assert fg and owner.value == pid, "foreign popup foreground"
        bounds = win.rectangle()
        crop = (bounds.left + 12, bounds.top + 8,
                bounds.right - 8, bounds.bottom - 8)
        assert bounds.width() >= 800 and bounds.height() >= 550
        assert crop[0] >= 0 and crop[1] >= 0
        assert crop[2] <= user.GetSystemMetrics(0)
        assert crop[3] <= user.GetSystemMetrics(1)
        theme = __import__("os").environ.get("FLY_F01_HIDDEN_THEME", "light")
        file = base / f"f01-hidden-{theme}-{state}-owned.png"
        ImageGrab.grab(bbox=crop, include_layered_windows=True).save(
            file, "PNG", optimize=True)
        assert file.stat().st_size > 1500
        print("F01_HIDDEN_SCREENSHOT", file.name,
              "DPI", user.GetDpiForWindow(win.handle), flush=True)

    # Both panes initially display the owned left Shell folder, not Right.
    eventually(lambda: find_row(0, "readme.txt") is not None and
               find_row(1, "readme.txt") is not None,
               "owned original visible Shell rows missing", 15)
    eventually(lambda: absent(0) and absent(1),
               "hidden Shell items leaked into default pane", 8)
    safe_click(find_row(0, "readme.txt"))
    checked(False)
    shot("default")
    toggle()
    eventually(lambda: visible(0), "native hidden file/folder not shown", 12)
    assert find_row(0, "readme.txt").is_selected(), (
        "normal selected Shell item lost on hidden toggle")
    checked(True)
    shot("enabled")
    menu()
    shot("menu", flyout_open=True)
    from pywinauto.keyboard import send_keys
    send_keys("{ESC}", pause=.06)
    print("F01_HIDDEN_FILE_AND_FOLDER=PASS", flush=True)

    # Independent View states: right stays hidden until its own action.
    safe_click(find_row(1, "readme.txt"))
    checked(False)
    assert absent(1), "right pane exposed hidden items without its own toggle"
    toggle()
    eventually(lambda: visible(1), "right pane hidden toggle not applied", 9)
    checked(True)
    safe_click(find_row(0, "readme.txt"))
    checked(True)
    assert visible(0), "left pane lost hidden mode on right activation"
    print("F01_HIDDEN_PANE_ISOLATION=PASS", flush=True)

    # Selected hidden item must not survive hiding its row. No filesystem
    # operation, deletion, modification or selection-by-stale-index.
    safe_click(find_row(0, "hidden-note.txt"))
    eventually(lambda: find_row(0, "hidden-note.txt") is not None and
               find_row(0, "hidden-note.txt").is_selected(),
               "hidden item not selectable", 8)
    toggle()
    eventually(lambda: absent(0), "left hidden row leaked after hide", 9)
    checked(False)
    assert all("hidden-note.txt" not in r.window_text() for r in rows(0))
    assert not any(r.is_selected() and "hidden-note" in r.window_text()
                   for r in rows(0))
    shot("restored")
    safe_click(find_row(1, "readme.txt"))
    checked(True)
    toggle()
    eventually(lambda: absent(1), "right hidden row leaked after hide", 9)
    checked(False)
    print("F01_HIDDEN_TOGGLE_SELECTION_AND_RESTORE=PASS", flush=True)
