"""Focused F04 tree GUI acceptance in the disposable Left/Nested fixture."""
from pathlib import Path
from uuid import uuid4
import ctypes
from ctypes import wintypes
import os

from paths import ROOT


def run(*, win, element, safe_click, eventually, left, right):
    assert (left / "Nested").is_dir() and right.is_dir()
    toggle = element("FolderTreeToggle")
    tree = element("FolderTreeView")
    assert toggle.exists(timeout=4) and not tree.is_visible()
    app = win.wrapper_object()
    owner_pid = app.element_info.process_id

    def capture(label):
        if os.environ.get("FLY_F04_TREE_VISUAL_CAPTURE") != "YES":
            return
        user = ctypes.windll.user32
        user.GetForegroundWindow.restype = wintypes.HWND
        user.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        hwnd = user.GetForegroundWindow()
        pid = wintypes.DWORD()
        if hwnd:
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        assert pid.value == owner_pid, "Refuse non-owned foreground screenshot"
        folder = ROOT / "logs" / "f04-tree-visual"
        assert not folder.is_symlink() and not ROOT.is_symlink()
        assert folder.resolve(strict=False).is_relative_to(
            (ROOT / "logs").resolve())
        folder.mkdir(parents=True, exist_ok=True)
        image = app.capture_as_image()
        assert image.width >= 650 and image.height >= 400
        png = folder / ("f04-" + label + "-" + uuid4().hex + ".png")
        image.save(png, format="PNG")
        assert 1000 < png.stat().st_size < 3000000
        print("F04_TREE_" + label.upper() + "_PNG=" + str(png), flush=True)

    # Verify collapsed/expanded actual windows, not just an XAML source token.
    safe_click(toggle)
    eventually(lambda: tree.is_visible(), "F04 tree did not open", 6)
    safe_click(toggle)
    eventually(lambda: not tree.is_visible(), "F04 tree did not collapse", 6)
    capture("collapsed")
    safe_click(toggle)
    eventually(lambda: tree.is_visible(), "F04 tree did not reopen", 6)

    def nested_row():
        for item in tree.descendants():
            if item.element_info.control_type == "TreeItem":
                if item.window_text() == "Nested":
                    return item
        return None

    row = eventually(nested_row, "F04 test-owned Nested child missing", 15)
    assert row.element_info.process_id == owner_pid
    capture("expanded")
    safe_click(row)
    eventually(lambda: str(left / "Nested").casefold() in
               element("AddressBox").get_value().casefold(),
               "F04 tree selection did not navigate active pane", 15)
    print("F04_TREE_OWNED_LOCAL_NAVIGATION=PASS", flush=True)
    eventually(lambda: any(
               str(left / "Nested").casefold() in x.window_text().casefold()
               for x in tree.descendants()),
               "F04 tree retained previous root after in-tab navigation", 9)
    capture("navigated")
    safe_click(toggle)
    eventually(lambda: not tree.is_visible(), "F04 tree did not hide", 6)
    print("F04_TREE_TOGGLE_EXPAND_NAVIGATE=PASS", flush=True)
