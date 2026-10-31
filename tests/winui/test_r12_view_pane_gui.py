"""R12 owned View-menu details/opt-in preview entrypoint acceptance.

Never enables text reading or touches another app, clipboard, or OS settings.
"""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

from pywinauto import Desktop
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

BASE = ROOT/"logs"/"r12-view-pane-owned-gui-r3-20261031"


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
            preview.click_input()
            h.wait(lambda:app.el("TextPreviewToggleButton").has_keyboard_focus(),
                   "R12 preview opt-in button did not receive focus",seconds=10)
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
        if success:
            assert folder.parent==BASE.resolve() and not folder.is_symlink()
            shutil.rmtree(folder)
            result["fixture_removed"]=True
        (BASE/"result.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print("R12_VIEW_PANE_GUI_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
