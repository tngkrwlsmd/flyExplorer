"""R06 file-context menu eligibility in a test-owned Windows WinUI process.

Only observes app-owned menu items. NEVER invokes either Share entry, opens
Windows Share UI, chooses a target, sends data or touches existing Explorer.
"""
import ctypes
from ctypes import wintypes
from pathlib import Path

from pywinauto import Desktop, keyboard, mouse


DIRECT = "Windows 공유 창 열기 (파일 1개)"
FALLBACK = "공유 옵션: Windows 탐색기에서 선택"


def run(*, win, element, focus, eventually, left, right, owned, owned_pid):
    assert Path(left).parent == Path(owned) and Path(right).parent == Path(owned)
    source = Path(left) / "readme.txt"
    folder = Path(left) / "Nested"
    assert source.is_file() and folder.is_dir()
    original = source.read_bytes()
    original_names = {entry.name for entry in Path(left).iterdir()}
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = (
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD))

    def foreground_owned():
        hwnd = user32.GetForegroundWindow()
        pid = wintypes.DWORD()
        if hwnd:
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value == owned_pid

    def row(label):
        matches = [peer for peer in element("LeftFiles").descendants(
            control_type="ListItem") if label in peer.window_text()]
        assert len(matches) <= 1, "ambiguous test-owned row"
        return matches[0] if matches else None

    def select_one(label):
        focus()
        found = eventually(lambda: row(label),
                           "R06 test-owned row missing: " + label, 8)
        found.select()
        eventually(lambda: row(label) and row(label).is_selected(),
                   "R06 test-owned selection not committed", 8)
        assert foreground_owned()

    def right_click_selected(label):
        focus()
        target = row(label)
        assert target is not None and target.is_selected()
        item = target.rectangle()
        view = element("LeftFiles").rectangle()
        x1, x2 = max(item.left, view.left), min(item.right, view.right)
        y1, y2 = max(item.top, view.top), min(item.bottom, view.bottom)
        assert x2 - x1 > 30 and y2 - y1 > 7, "row not inside owned file viewport"
        point = (x1 + min(50, (x2 - x1) // 2), (y1 + y2) // 2)
        assert view.left < point[0] < view.right
        assert view.top < point[1] < view.bottom
        assert foreground_owned(), "refusing input outside owned app"
        mouse.click(button="right", coords=point)

    def app_menu_entry(name):
        matches = []
        for top in Desktop(backend="uia").windows(process=owned_pid):
            try:
                if top.element_info.process_id != owned_pid:
                    continue
                for peer in top.descendants(control_type="MenuItem"):
                    if peer.element_info.process_id != owned_pid:
                        continue
                    if peer.is_visible() and peer.window_text().strip() == name:
                        matches.append(peer)
            except (RuntimeError, LookupError, ValueError):
                continue
        assert len(matches) <= 1, "ambiguous app-owned share menu entry"
        return matches[0] if matches else None

    def assert_menu(direct_enabled):
        def both():
            one = app_menu_entry(DIRECT)
            other = app_menu_entry(FALLBACK)
            return (one, other) if one and other else None
        direct, fallback = eventually(both, "R06 owned Share menu absent", 9)
        assert foreground_owned(), "Share menu unexpectedly opened foreign UI"
        assert direct.is_enabled() is direct_enabled, "direct Share eligibility wrong"
        assert fallback.is_enabled(), "Explorer handoff must remain available"
        # Only dismiss flyExplorer's own context flyout, never a Windows Share sheet.
        assert foreground_owned()
        keyboard.send_keys("{ESC}")
        eventually(lambda: not app_menu_entry(DIRECT),
                   "test-owned context flyout did not close", 8)

    select_one(source.name)
    right_click_selected(source.name)
    assert_menu(True)
    print("R06_GUI_SINGLE_FILE_DIRECT_AND_FALLBACK_ENABLED=PASS", flush=True)

    select_one(folder.name)
    right_click_selected(folder.name)
    assert_menu(False)
    print("R06_GUI_FOLDER_DIRECT_DISABLED_FALLBACK_ENABLED=PASS", flush=True)

    select_one(source.name)
    second = row(folder.name)
    assert second is not None
    second.iface_selection_item.AddToSelection()
    eventually(lambda: row(source.name).is_selected() and
               row(folder.name).is_selected(),
               "R06 owned multi-selection not stable", 8)
    right_click_selected(source.name)
    assert row(source.name).is_selected() and row(folder.name).is_selected()
    assert_menu(False)
    assert row(source.name).is_selected() and row(folder.name).is_selected()
    print("R06_GUI_MULTI_SELECTION_DIRECT_DISABLED_FALLBACK_ENABLED=PASS",
          flush=True)

    assert source.read_bytes() == original
    assert {entry.name for entry in Path(left).iterdir()} == original_names
    print("R06_GUI_OWNED_ORIGINALS_PRESERVED_NO_SHARE_ACTION_INVOKED=PASS",
          flush=True)
