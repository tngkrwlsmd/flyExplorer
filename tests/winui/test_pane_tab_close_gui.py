"""Focused real-mouse pane-tab X and paste-discoverability acceptance.

Only test-owned files and a private app profile. Does not invoke clipboard,
delete, system Settings, or non-owned GUI elements.
"""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

from pywinauto import mouse
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

BASE = ROOT / "logs" / "pane-tabs-gui-owned-20261103"


def main():
    assert not BASE.exists(), "PANE_TABS_GUI_EVIDENCE_ALREADY_EXISTS"
    BASE.mkdir(parents=True)
    h.BASE = BASE
    fixture = Path(tempfile.mkdtemp(prefix="pane-fixture-", dir=BASE)).resolve()
    pane_a = fixture / "PaneA"
    pane_a.mkdir()
    root_file = fixture / "owned-root-marker.txt"
    a_file = pane_a / "pane-a-marker.txt"
    root_file.write_bytes(b"owned root original")
    a_file.write_bytes(b"owned tab A original")
    expected = {str(p.relative_to(fixture)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in fixture.rglob("*") if p.is_file()}
    result = {"source_test": "pane-tab-close-v1", "exe_sha256":
              hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    success = False
    try:
        with h.App(app_exe("Release"), fixture, "pane-tabs-close", "dark") as app:
            def tabs(side):
                strip = app.el(side + "Tabs")
                return [x for x in strip.descendants(control_type="TabItem")
                        if x.element_info.process_id == app.app.pid]

            def ready(side, needle):
                return any(needle in r.window_text() for r in app.rows(side))

            def selected(side):
                return [i for i, t in enumerate(tabs(side))
                        if t.iface_selection_item.CurrentIsSelected]

            def click_tab(side, index):
                t = tabs(side)[index]
                rect = t.rectangle()
                pt = (rect.left + min(35, max(10, rect.width() // 4)),
                      rect.mid_point().y)
                assert h.owner(h.u.GetForegroundWindow()) == app.app.pid
                mouse.click(coords=pt)
                h.wait(lambda: selected(side) == [index],
                       "desired owned tab did not select", seconds=12)

            def close_x(side, index):
                item = tabs(side)[index]
                buttons = item.descendants(control_type="Button")
                names = [(b.element_info.automation_id or "") + " " +
                         (b.element_info.name or "") for b in buttons]
                matching = [b for b, name in zip(buttons, names)
                            if "close" in name.casefold() or "닫" in name]
                if len(matching) == 1:
                    target = matching[0]
                elif len(buttons) == 1:
                    target = buttons[0]
                else:
                    raise AssertionError(
                        "Cannot identify exactly one owned native tab close button: "
                        + repr(names[:8]))
                assert target.element_info.process_id == app.app.pid
                assert h.owner(h.u.GetForegroundWindow()) == app.app.pid
                target.click_input()

            h.wait(lambda: len(tabs("Left")) == 1 and
                   len(tabs("Right")) == 1 and ready("Left", root_file.name),
                   "initial disposable split-pane state missing")
            paste = app.el("WindowsPasteButton").wrapper_object()
            paste_name = paste.element_info.name or ""
            assert "붙여넣기" in paste_name and "Ctrl+V" in paste_name, paste_name
            result["paste_accessibility_hint"] = True
            assert ready("Right", root_file.name)
            app.el("LeftFiles").set_focus()
            app.el("NewTabButton").click_input()
            h.wait(lambda: len(tabs("Left")) == 2 and
                   ready("Left", root_file.name),
                   "second pane tab was not created", seconds=18)
            app.navigate(pane_a, a_file.name)
            result["second_tab_independent_folder"] = True
            app.el("NewTabButton").click_input()
            h.wait(lambda: len(tabs("Left")) == 3,
                   "third pane tab not created", seconds=18)
            app.navigate(fixture, root_file.name)
            click_tab("Left", 1)
            h.wait(lambda: ready("Left", a_file.name),
                   "second tab did not restore its folder", seconds=15)
            before = app.el("AddressBox").get_value().casefold()
            assert "panea" in before and selected("Left") == [1]
            close_x("Left", 0)
            h.wait(lambda: len(tabs("Left")) == 2 and
                   selected("Left") == [0] and ready("Left", a_file.name),
                   "closing earlier inactive tab changed active folder", seconds=18)
            assert app.el("AddressBox").get_value().casefold() == before
            assert ready("Right", root_file.name)
            result["earlier_background_x_preserves_active_route"] = True
            close_x("Left", 1)
            h.wait(lambda: len(tabs("Left")) == 1 and
                   ready("Left", a_file.name),
                   "closing later inactive tab changed active folder", seconds=18)
            result["later_background_x_preserves_active_route"] = True
            close_x("Left", 0)
            assert len(tabs("Left")) == 1 and ready("Left", a_file.name)
            result["last_pane_tab_guard"] = True
            app.el("NewTabButton").click_input()
            h.wait(lambda: len(tabs("Left")) == 2,
                   "toolbar add after native close failed", seconds=16)
            app.el("CloseTabButton").click_input()
            h.wait(lambda: len(tabs("Left")) == 1 and
                   ready("Left", a_file.name),
                   "toolbar close after native X did not work", seconds=16)
            result["shared_toolbar_close_preserved"] = True
            assert ready("Right", root_file.name)
            result["other_pane_unmodified"] = True
        result["app"] = app.report
        assert app.report["normal_exit"] and app.report["original_settings_unchanged"]
        assert app.report["profile_removed"]
        success = True
    finally:
        current = {str(p.relative_to(fixture)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in fixture.rglob("*") if p.is_file()}
        result["original_files_unchanged"] = current == expected
        if success and current == expected:
            assert fixture.parent == BASE.resolve() and not fixture.is_symlink()
            shutil.rmtree(fixture)
            result["fixture_removed"] = True
        (BASE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
        print("PANE_TAB_GUI_SUMMARY=" + json.dumps(result, ensure_ascii=False), flush=True)
    assert success and result["original_files_unchanged"]


if __name__ == "__main__":
    main()
