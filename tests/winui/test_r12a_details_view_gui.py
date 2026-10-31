"""R12a owned Windows GUI: physically toggle the existing Details pane.

Uses only an isolated file and profile. Never enables text reading or alters OS state.
"""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

from pywinauto import Desktop, mouse
import ctypes
from ctypes import wintypes
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

BASE=ROOT/"logs"/"r12a-details-owned-gui-r3-20261031"


def main():
    if BASE.exists() and any(BASE.iterdir()):
        raise RuntimeError("Retained R12a GUI evidence exists")
    BASE.mkdir(parents=True,exist_ok=True)
    h.BASE=BASE
    folder=Path(tempfile.mkdtemp(prefix="r12a-fixture-",dir=BASE)).resolve()
    source=folder/"r12a-owned-file.txt"
    content=b"r12a-owned-detail-pane-never-auto-preview"
    source.write_bytes(content)
    result={"exe_sha256":hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    success=False
    try:
        with h.App(app_exe("Release"),folder,"r12a-details","dark") as app:
            def owned_file():
                matches=[r for r in app.rows("Left") if source.name in r.window_text()]
                return matches[0] if len(matches)==1 else None
            h.wait(owned_file,"R12a owned file missing",seconds=20).select()
            h.wait(lambda:owned_file() is not None and owned_file().is_selected(),
                   "R12a owned selection not ready",seconds=8)

            def detail_entry():
                matches={}
                for top in Desktop(backend="uia").windows(process=app.app.pid):
                    for item in top.descendants(control_type="MenuItem"):
                        if (item.element_info.process_id==app.app.pid and
                            item.element_info.automation_id=="ViewFileInfoPaneItem"):
                            rect=item.rectangle()
                            matches[(rect.left,rect.top,rect.right,rect.bottom)]=item
                return next(iter(matches.values())) if len(matches)==1 else None

            def click_detail():
                app.win.set_focus()
                assert h.owner(h.u.GetForegroundWindow())==app.app.pid
                app.el("ViewButton").click_input()
                item=h.wait(detail_entry,"R12a View details entry not found",seconds=12)
                assert item.is_visible() and item.is_enabled()
                assert item.element_info.process_id==app.app.pid
                assert h.owner(h.u.GetForegroundWindow())==app.app.pid
                item.click_input()

            def menu_closed():
                try:
                    entry=detail_entry()
                    return entry is None or not entry.is_visible()
                except (RuntimeError,LookupError):
                    return True

            assert "열기" in app.el("FileInfoToggleButton").element_info.name
            click_detail()
            h.wait(lambda:"닫기" in app.el("FileInfoToggleButton").element_info.name,
                   "R12a details pane did not open",seconds=12)
            result["details_opened_by_physical_click"]=True
            assert app.el("TextPreviewBody").window_text().strip()==""
            assert "꺼" in app.el("TextPreviewStatus").window_text()
            result["no_implicit_preview_read"]=True
            # A command can update Details state before its flyout dismissal
            # finishes. Wait for that original menu to close before re-opening.
            h.wait(menu_closed,"R12a first View menu never closed",seconds=8)
            result["first_menu_dismissed"]=True

            app.win.set_focus()
            assert h.owner(h.u.GetForegroundWindow())==app.app.pid
            app.el("ViewButton").click_input()
            entry=h.wait(detail_entry,"R12a second View menu missing",seconds=12)
            assert entry.is_visible() and entry.is_enabled()
            box=entry.rectangle()
            point=(box.left+10,(box.top+box.bottom)//2)
            assert box.width()>100 and box.height()>18
            fn=ctypes.windll.user32.WindowFromPoint
            fn.argtypes=[wintypes.POINT]
            fn.restype=wintypes.HWND
            hit=fn(wintypes.POINT(*point))
            assert hit and h.owner(hit)==app.app.pid
            ui_hit=Desktop(backend="uia").from_point(*point)
            assert ui_hit.element_info.process_id==app.app.pid
            result["second_pointer_hit"]={
                "point":point,
                "ui_automation_id":ui_hit.element_info.automation_id,
                "ui_control_type":ui_hit.element_info.control_type,
                "menu_rect":[box.left,box.top,box.right,box.bottom]
            }
            mouse.click(button="left",coords=point)
            try:
                h.wait(lambda:"열기" in app.el("FileInfoToggleButton").element_info.name,
                       "R12a details pane did not close",seconds=8)
            except AssertionError:
                current=detail_entry()
                result["second_click_diagnostic"]={
                    "pane_toggle":app.el("FileInfoToggleButton").element_info.name[:100],
                    "menu_still_visible":current is not None and current.is_visible(),
                    "foreground_owner":h.owner(h.u.GetForegroundWindow()),
                    "app_pid":app.app.pid,
                    "status":app.el("StatusText").window_text()[:200]
                }
                retry=current if current is not None and current.is_visible() else None
                if retry is not None:
                    retry.invoke()
                    try:
                        h.wait(lambda:"열기" in app.el("FileInfoToggleButton").element_info.name,
                               "R12a UIA invoke did not close Details",seconds=5)
                        result["uia_invoke_closed"]=True
                    except AssertionError:
                        result["uia_invoke_closed"]=False
                print("R12A_SECOND_POINTER_DIAG="+json.dumps(
                    result,ensure_ascii=False),flush=True)
                raise AssertionError("R12a physical close failed; diagnostics retained")
            result["details_closed_by_physical_click"]=True
            h.wait(menu_closed,"R12a second View menu never closed",seconds=8)
            result["second_menu_dismissed"]=True
            result["original_unchanged"]=source.read_bytes()==content
        result["app"]=app.report
        assert result["original_unchanged"]
        assert app.report["normal_exit"] and app.report["original_settings_unchanged"]
        assert app.report["profile_removed"]
        success=True
    finally:
        result["owned_source_preserved_on_exit"]=source.read_bytes()==content
        if success:
            assert folder.parent==BASE.resolve() and not folder.is_symlink()
            shutil.rmtree(folder)
            result["fixture_removed"]=True
        (BASE/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),
                                         encoding="utf-8")
        print("R12A_DETAILS_GUI_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
