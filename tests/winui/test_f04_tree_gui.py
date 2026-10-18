"""Focused F04 tree GUI acceptance in the disposable Left/Nested fixture."""
from pathlib import Path
from uuid import uuid4
import ctypes
from ctypes import wintypes
import os
from pywinauto import mouse

from paths import ROOT


def run(*, win, element, safe_click, eventually, left, right):
    assert (left / "Nested").is_dir() and right.is_dir()
    toggle = element("FolderTreeToggle")
    tree = element("FolderTreeView")
    assert toggle.exists(timeout=4)
    # WinUI omits descendants of a Collapsed parent from the UIA tree.
    # WindowSpecification.is_visible() resolves a missing control by polling
    # until TimeoutError, so test UIA existence before accessing visibility.
    def tree_visible():
        return tree.exists(timeout=.2) and tree.is_visible()

    assert not tree_visible()
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
    eventually(tree_visible, "F04 tree did not open", 6)
    safe_click(toggle)
    eventually(lambda: not tree_visible(), "F04 tree did not collapse", 6)
    capture("collapsed")
    safe_click(toggle)
    eventually(tree_visible, "F04 tree did not reopen", 6)

    def nested_row():
        for item in tree.descendants():
            if item.element_info.control_type == "TreeItem":
                if item.window_text() == "Nested":
                    return item
        return None

    row = eventually(nested_row, "F04 test-owned Nested child missing", 15)
    assert row.element_info.process_id == owner_pid
    capture("expanded")
    # Clicking a full TreeItem bounding rectangle can hit the chevron or
    # empty padding, which expands a node rather than invoking its content.
    # Use the actual test-owned label's pixel rectangle for physical input.
    label = next((x for x in row.descendants()
                  if x.element_info.control_type == "Text"
                  and x.window_text() == "Nested"), None)
    assert label is not None, "F04 node content text not exposed to UIA"
    # At a 960x519 window, the tree's nested child starts below the
    # outer sidebar ScrollViewer viewport. UIA can find/select it even
    # while the user cannot click it. Scroll first, then send REAL input.
    try:
        row.ensure_visible()
        print("F04_SCROLL_ITEM=REQUESTED", flush=True)
    except Exception as error:
        print("F04_SCROLL_ITEM=UNAVAILABLE", type(error).__name__, flush=True)

    click_point, has_point = row.element_info.element.GetClickablePoint()
    before = label.rectangle()
    visible_window = app.rectangle()
    label_y = (before.top + before.bottom) // 2
    if not (visible_window.top + 115 < label_y <
            visible_window.bottom - 45):
        # Scroll the app-owned navigation sidebar (not the desktop or an
        # arbitrary element) when the nested node remains out of view.
        user = ctypes.windll.user32
        hwnd = user.GetForegroundWindow()
        pid = wintypes.DWORD()
        if hwnd:
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        assert pid.value == owner_pid, "Refuse scroll on non-owned foreground"
        btn = toggle.rectangle()
        screen = app.rectangle()
        scroll_x = (btn.left + btn.right) // 2
        scroll_y = min((btn.top + btn.bottom) // 2, screen.bottom - 65)
        assert (screen.left + 5 < scroll_x < screen.right - 5 and
                screen.top + 115 < scroll_y < screen.bottom - 48), (
            "Refuse sidebar scroll outside owned app viewport")
        mouse.scroll(coords=(scroll_x, scroll_y), wheel_dist=-8)
        row = eventually(nested_row, "F04 Nested missing after sidebar scroll", 6)
        assert row.element_info.process_id == owner_pid
        label = next((x for x in row.descendants()
                      if x.element_info.control_type == "Text"
                      and x.window_text() == "Nested"), None)
        assert label is not None, "F04 Nested label missing after scroll"
        click_point, has_point = row.element_info.element.GetClickablePoint()
        print("F04_PHYSICAL_SIDEBAR_SCROLL=YES",
              "UIA_POINT_AVAILABLE=", bool(has_point), flush=True)

    bounds = row.rectangle()
    window_bounds = app.rectangle()
    text_bounds = label.rectangle()
    if has_point and (text_bounds.left <= click_point.x < text_bounds.right
                      and text_bounds.top <= click_point.y < text_bounds.bottom):
        x, y = click_point.x, click_point.y
        target = "UIA_LABEL_POINT"
    else:
        # GetClickablePoint may return False for a WinUI TreeItem even
        # when its text is visible. Prefer the precisely bounded label
        # rather than treating an accessibility limitation as app failure.
        x = (text_bounds.left + text_bounds.right) // 2
        y = (text_bounds.top + text_bounds.bottom) // 2
        target = "VISIBLE_TEXT_CENTER"
    assert (text_bounds.left <= x < text_bounds.right and
            text_bounds.top <= y < text_bounds.bottom and
            bounds.left <= x < bounds.right and bounds.top <= y < bounds.bottom), (
        "F04 physical point outside owned item and label")
    assert (window_bounds.left + 5 < x < window_bounds.right - 5 and
            window_bounds.top + 115 < y < window_bounds.bottom - 45), (
        "F04 Nested label not visible in owned app viewport")
    capture("expanded-scrolled")
    print("F04_MOUSE_TARGET=", target, "ROW_WIDTH=", bounds.width(),
          "ROW_HEIGHT=", bounds.height(), "OFFSET_X=", x - bounds.left,
          "OFFSET_Y=", y - bounds.top, flush=True)
    safe_click(row, coords=(x - bounds.left, y - bounds.top))
    try:
        eventually(lambda: str(left / "Nested").casefold() in
                   element("AddressBox").get_value().casefold(),
                   "F04 row click did not navigate active pane", 10)
    except AssertionError:
        current = element("AddressBox").get_value().casefold()
        print("F04_CLICK_DIAG_ROOT_STILL_ACTIVE=",
              current == str(left).casefold(), flush=True)
        print("F04_CLICK_DIAG_STATUS=",
              element("StatusText").window_text()[:110], flush=True)
        tree_status = element("FolderTreeStatus")
        print("F04_TREE_SELECTION_STAGE=",
              tree_status.window_text()[:80] if tree_status.exists(timeout=.2)
              else "UNEXPOSED", flush=True)
        try:
            print("F04_TREE_UIA_SELECTED=",
                  bool(row.iface_selection_item.CurrentIsSelected), flush=True)
        except Exception:
            print("F04_TREE_UIA_SELECTED=UNAVAILABLE", flush=True)
        # Diagnostic only: an accessibility selection is not a physical
        # click pass, and the original click assertion is re-raised below.
        try:
            row.iface_selection_item.Select()
            eventually(lambda: str(left / "Nested").casefold() in
                       element("AddressBox").get_value().casefold(),
                       "UIA selection did not navigate", 5)
            print("F04_DIAG_UIA_SELECTION_NAVIGATED=YES", flush=True)
        except Exception as diagnostic_error:
            print("F04_DIAG_UIA_SELECTION_NAVIGATED=NO",
                  type(diagnostic_error).__name__, flush=True)
        try:
            capture("after-click-failed")
        except AssertionError as evidence_error:
            # The failure screenshot must never replace the primary
            # input->navigation assertion. Do not capture another window.
            print("F04_FAILURE_CAPTURE_SKIPPED=",
                  str(evidence_error)[:100], flush=True)
        raise
    print("F04_TREE_OWNED_LOCAL_NAVIGATION=PASS", flush=True)
    eventually(lambda: any(
               str(left / "Nested").casefold() in x.window_text().casefold()
               for x in tree.descendants()),
               "F04 tree retained previous root after in-tab navigation", 9)
    capture("navigated")
    safe_click(toggle)
    eventually(lambda: not tree_visible(), "F04 tree did not hide", 6)
    print("F04_TREE_TOGGLE_EXPAND_NAVIGATE=PASS", flush=True)
