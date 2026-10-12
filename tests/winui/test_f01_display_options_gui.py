"""Owned actual-WinUI F01 selection-checkbox / compact-row functional probe.

Run only through the existing test_shell_gui fixture with FLY_F01_DISPLAY_GUI=YES
and optionally FLY_F01_DISPLAY_ONLY=YES.  The parent owns the app process,
window, private profile and cleanup.  Images use synthetic owned filenames only;
capture markers are NOT proof that pixel review has passed.
"""
from pathlib import Path
from pywinauto import Desktop
from PIL import ImageGrab


def run(*, win, element, safe_click, focus, eventually, base, owned, left, right):
    assert Path(left).is_relative_to(owned)
    assert Path(right).is_relative_to(owned)
    screen = Desktop(backend="uia")

    def list_rows(side):
        files = element("LeftFiles" if side == 0 else "RightFiles")
        return [row for row in files.descendants()
                if row.element_info.control_type == "ListItem"]

    def named_row(side, fragment="readme.txt"):
        return next((r for r in list_rows(side)
                     if fragment in r.window_text()), None)

    def choose(name):
        focus()
        safe_click(element("ViewButton"))
        def target():
            try:
                local = element(name)
                if local.exists(timeout=.15):
                    return local.wrapper_object()
                # WinUI may give a MenuFlyout its own popup UIA root.
                matches = [x for w in screen.windows(process=win.wrapper_object().element_info.process_id)
                           for x in w.descendants()
                           if x.element_info.automation_id == name]
                return matches[0] if len(matches) == 1 else None
            except (LookupError, RuntimeError):
                return None
        menu_item = eventually(target, "F01 view menu item unavailable: " + name, 8)
        assert menu_item is not None, name
        # Refocusing the main window here would dismiss the open WinUI popup.
        # Instead require exact app-process ownership before physical input.
        assert menu_item.element_info.process_id == win.wrapper_object().element_info.process_id
        menu_item.click_input()

    eventually(lambda: named_row(0) is not None,
               "F01 owned readme.txt row not available", 12)
    before = named_row(0)
    original_height = before.rectangle().height()
    assert original_height >= 26, original_height
    left_files = element("LeftFiles")
    focus()
    safe_click(before)
    eventually(lambda: bool(named_row(0) and named_row(0).is_selected()),
               "F01 initial selected file missing", 7)

    # Same owned HWND + fixture before/after mode images; a later reviewer
    # still must inspect actual rendered pixels before visual acceptance.
    def shot(kind):
        rect = win.rectangle()
        assert rect.width() > 400 and rect.height() > 260
        assert rect.left >= 0 and rect.top >= 0
        focus()
        dest = base / ("f01-" + kind + "-owned.png")
        ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom),
                       include_layered_windows=True).save(dest)
        return dest

    before_image = shot("default")
    choose("ViewCheckboxesItem")
    eventually(lambda: named_row(0) is not None and named_row(0).is_selected(),
               "F01 selection identity lost after checkbox toggle", 10)
    # Do not confuse selected item text with a visual checkbox: explicitly
    # inspect the checked-state control descendants when UIA exposes them.
    row = named_row(0)
    assert row is not None
    checkboxes = [x for x in row.descendants()
                  if x.element_info.control_type == "CheckBox"]
    print("F01_CHECKBOX_UIA_DESCENDANTS", len(checkboxes), flush=True)

    choose("ViewCompactRowsItem")
    eventually(lambda: named_row(0) is not None and
               named_row(0).rectangle().height() < original_height,
               "F01 compact Details row did not reduce height", 10)
    compact_height = named_row(0).rectangle().height()
    after_image = shot("checkbox-compact")
    print("F01_OWNED_ROW_HEIGHTS", original_height, compact_height, flush=True)
    print("F01_CAPTURE_PAIRS", before_image.name, after_image.name, flush=True)

    # Turning modes off must keep the same selected filesystem item.
    choose("ViewCompactRowsItem")
    choose("ViewCheckboxesItem")
    eventually(lambda: named_row(0) is not None and named_row(0).is_selected(),
               "F01 selected item lost after restore", 10)
    eventually(lambda: named_row(0).rectangle().height() >= original_height,
               "F01 default row pitch did not restore", 10)
    print("F01_DISPLAY_TOGGLE_SELECTION_PRESERVED", True, flush=True)

    # New F01-B action changes only the displayed name. The Automation
    # Name must preserve the original full filename while hidden; selection
    # remains identified by the unchanged native Shell parsing path.
    choose("ViewFileExtensionsItem")
    def extension_hidden():
        row = named_row(0)
        return bool(row and row.is_selected() and
                    "실제 파일 이름: readme.txt" in row.window_text())
    eventually(extension_hidden,
               "F01 hidden extension or original-name UIA contract failed", 10)
    hidden_image = shot("filename-extension-hidden")
    choose("ViewFileExtensionsItem")
    def extension_restored():
        row = named_row(0)
        return bool(row and row.is_selected() and
                    "실제 파일 이름:" not in row.window_text())
    eventually(extension_restored,
               "F01 displayed extension did not restore with native selection", 10)
    print("F01_EXTENSION_HIDDEN_ACCESSIBLE_FULLNAME", True, flush=True)
    print("F01_EXTENSION_CAPTURE", hidden_image.name, flush=True)
