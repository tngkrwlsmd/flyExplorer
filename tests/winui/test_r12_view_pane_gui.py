"""R12 owned View-menu details/opt-in preview entrypoint acceptance.

Never enables text reading or touches another app, clipboard, or OS settings.
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

BASE = ROOT/"logs"/"r12-view-pane-owned-gui-r7-hit-20261031"


def main():
    if BASE.exists() and any(BASE.iterdir()):
        raise RuntimeError("Retained R12 GUI evidence exists; preserve it")
    BASE.mkdir(parents=True, exist_ok=True)
    h.BASE=BASE
    folder=Path(tempfile.mkdtemp(prefix="r12-fixture-",dir=BASE)).resolve()
    source=folder/"r12-owned-preview.txt"
    content=b"r12-owned-text-preview-should-not-be-read"
    source.write_bytes(content)
    result={"exe_sha256":hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    success=False
    try:
        with h.App(app_exe("Release"),folder,"r12-view-pane","dark") as app:
            def owned_file():
                matches=[r for r in app.rows("Left") if source.name in r.window_text()]
                return matches[0] if len(matches)==1 else None
            h.wait(owned_file,"R12 source row absent",seconds=20).select()
            h.wait(lambda:owned_file() is not None and owned_file().is_selected(),
                   "R12 owned file selection did not settle",seconds=8)

            def view_item(item_id):
                matches={}
                for top in Desktop(backend="uia").windows(process=app.app.pid):
                    try:
                        for entry in top.descendants(control_type="MenuItem"):
                            if (entry.element_info.process_id==app.app.pid and
                                entry.element_info.automation_id==item_id):
                                r=entry.rectangle()
                                matches[(r.left,r.top,r.right,r.bottom)]=entry
                    except (RuntimeError,LookupError):
                        continue
                return next(iter(matches.values())) if len(matches)==1 else None

            def open_view(item_id):
                app.win.set_focus()
                assert h.owner(h.u.GetForegroundWindow())==app.app.pid
                app.el("ViewButton").click_input()
                item=h.wait(lambda:view_item(item_id),
                            "R12 owned View item absent: "+item_id,seconds=12)
                assert item.is_enabled()
                assert item.element_info.process_id==app.app.pid
                assert h.owner(h.u.GetForegroundWindow())==app.app.pid
                return item

            assert "열기" in app.el("FileInfoToggleButton").element_info.name
            detail=open_view("ViewFileInfoPaneItem")
            detail.click_input()
            h.wait(lambda:"닫기" in app.el("FileInfoToggleButton").element_info.name,
                   "R12 View did not show existing details pane",seconds=12)
            result["details_opened"]=True
            assert app.el("TextPreviewBody").window_text().strip()==""
            assert "꺼" in app.el("TextPreviewStatus").window_text()
            result["no_implicit_preview_read_on_details"]=True

            preview=open_view("ViewTextPreviewAccessItem")
            rect=preview.rectangle()
            result["preview_entry"]={
                "id":preview.element_info.automation_id,
                "name":preview.element_info.name[:120],
                "rect":[rect.left,rect.top,rect.right,rect.bottom],
                "enabled":preview.is_enabled()
            }
            # Avoid UIAWrapper.click_input(), which failed to dispatch while
            # Invoke on this same owned item succeeded in the R5 diagnosis.
            # Only send a real pointer event if Windows hit-testing confirms
            # the exact coordinate belongs to this flyExplorer process.
            center=((rect.left+rect.right)//2,(rect.top+rect.bottom)//2)
            assert preview.is_visible() and rect.width()>120 and rect.height()>16
            fn=ctypes.windll.user32.WindowFromPoint
            fn.argtypes=[wintypes.POINT]
            fn.restype=wintypes.HWND
            hit=fn(wintypes.POINT(*center))
            assert hit and h.owner(hit)==app.app.pid, (
                "R12 pointer target not owned by this application")
            assert h.owner(h.u.GetForegroundWindow())==app.app.pid
            result["owned_pointer_hit_verified"]=True
            result["pointer_center"]=center
            actual=Desktop(backend="uia").from_point(*center)
            assert actual.element_info.process_id==app.app.pid
            result["uia_pointer_target"]={
                "id":actual.element_info.automation_id,
                "name":actual.element_info.name[:100],
                "control_type":actual.element_info.control_type,
                "rect":list(actual.rectangle())
            }
            print("R12_POINTER_TARGET="+json.dumps(result["uia_pointer_target"],ensure_ascii=False),flush=True)
            mouse.click(button="left",coords=center)
            try:
                h.wait(lambda:"미리보기는 .txt" in app.el("StatusText").window_text(),
                       "R12 pointer click did not dispatch",seconds=4)
                result["preview_command_dispatched"]=True
            except AssertionError:
                result["pointer_dispatched"]=False
                result["status_after_pointer"]=app.el("StatusText").window_text()[:180]
                result["menu_still_visible"]=view_item("ViewTextPreviewAccessItem") is not None
                print("R12_POINTER_DIAG="+json.dumps(result,ensure_ascii=False),flush=True)
                # Diagnostic only: use WinUI/UIA Invoke on the same owned menu
                # item to distinguish pointer hit-testing from Click routing.
                retry=view_item("ViewTextPreviewAccessItem")
                if retry is None:
                    retry=open_view("ViewTextPreviewAccessItem")
                assert retry.element_info.process_id==app.app.pid
                assert h.owner(h.u.GetForegroundWindow())==app.app.pid
                retry.invoke()
                try:
                    h.wait(lambda:"미리보기는 .txt" in app.el("StatusText").window_text(),
                           "R12 UIA Invoke did not dispatch",seconds=5)
                    result["uia_invoke_dispatched"]=True
                except AssertionError:
                    result["uia_invoke_dispatched"]=False
                result["uia_invoke_focus"]=app.el("TextPreviewToggleButton").has_keyboard_focus()
                print("R12_INVOKE_DIAG="+json.dumps(result,ensure_ascii=False),flush=True)
                raise AssertionError("R12 pointer menu action not accepted; see bounded diagnostics")
            try:
                h.wait(lambda:app.el("TextPreviewToggleButton").has_keyboard_focus(),
                       "R12 preview opt-in button did not receive focus",seconds=10)
            except AssertionError:
                print("R12_FOCUS_DIAG="+json.dumps({
                    "status":app.el("StatusText").window_text()[:200],
                    "preview_status":app.el("TextPreviewStatus").window_text()[:160],
                    "preview_button_visible":app.el("TextPreviewToggleButton").is_visible(),
                    "preview_button_focus":app.el("TextPreviewToggleButton").has_keyboard_focus(),
                    "view_button_focus":app.el("ViewButton").has_keyboard_focus(),
                    "foreground_pid":h.owner(h.u.GetForegroundWindow()),
                    "owned_pid":app.app.pid
                },ensure_ascii=False),flush=True)
                raise
            assert "닫기" in app.el("FileInfoToggleButton").element_info.name
            assert app.el("TextPreviewBody").window_text().strip()==""
            assert "꺼" in app.el("TextPreviewStatus").window_text()
            result["preview_button_focused_without_read"]=True

            detail=open_view("ViewFileInfoPaneItem")
            detail.click_input()
            h.wait(lambda:"열기" in app.el("FileInfoToggleButton").element_info.name,
                   "R12 details pane did not close",seconds=12)
            assert source.read_bytes()==content
            result["details_closed"]=True
            result["original_unchanged"]=True
        result["app"]=app.report
        assert app.report["normal_exit"] and app.report["original_settings_unchanged"]
        assert app.report["profile_removed"]
        success=True
    finally:
        result["owned_source_preserved_on_exit"]=source.read_bytes()==content
        if success:
            assert folder.parent==BASE.resolve() and not folder.is_symlink()
            shutil.rmtree(folder)
            result["fixture_removed"]=True
        (BASE/"result.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print("R12_VIEW_PANE_GUI_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
