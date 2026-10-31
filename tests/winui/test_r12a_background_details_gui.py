"""R12a: physical blank-background > View > Details toggle on owned files.

Mirrors the previously accepted R02 native pointer route and never reads file text.
"""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

from pywinauto import Desktop, mouse
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

BASE=ROOT/"logs"/"r12a-background-details-gui-20261031"

def main():
    if BASE.exists() and any(BASE.iterdir()):
        raise RuntimeError("Retained R12a background evidence exists")
    BASE.mkdir(parents=True,exist_ok=True)
    h.BASE=BASE
    folder=Path(tempfile.mkdtemp(prefix="r12a-bg-fixture-",dir=BASE)).resolve()
    source=folder/"r12a-bg-owned.txt"
    content=b"r12a-owned-background-view-details"
    source.write_bytes(content)
    result={"exe_sha256":hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    success=False
    try:
        with h.App(app_exe("Release"),folder,"r12a-bg-details","dark") as app:
            def visible_menu(label):
                matches={}
                roots=[app.win]
                roots += [w for w in Desktop(backend="uia").windows(process=app.app.pid)
                          if w.handle!=app.hwnd]
                for root in roots:
                    for item in root.descendants(control_type="MenuItem"):
                        if item.window_text()!=label or not item.is_visible():
                            continue
                        rect=item.rectangle()
                        if rect.width()<12 or rect.height()<12:
                            continue
                        if item.element_info.process_id!=app.app.pid:
                            continue
                        matches[(rect.left,rect.top,rect.right,rect.bottom)]=item
                return next(iter(matches.values())) if len(matches)==1 else None

            def blank_point():
                rect=app.el("LeftFiles").rectangle()
                rows=app.rows("Left")
                bottoms=[r.rectangle().bottom for r in rows]
                assert bottoms
                point=(rect.left+45,max(rect.top+120,max(bottoms)+35))
                assert rect.left<point[0]<rect.right and rect.top<point[1]<rect.bottom-8
                return point

            def open_details_menu():
                app.win.set_focus()
                h.wait(lambda:h.owner(h.u.GetForegroundWindow())==app.app.pid,
                       "R12a owned app not foreground",seconds=8)
                mouse.click(button="right",coords=blank_point())
                view=h.wait(lambda:visible_menu("보기"),
                            "R12a owned background View submenu absent",seconds=12)
                assert view.element_info.process_id==app.app.pid
                view.click_input()
                choice=h.wait(lambda:visible_menu("세부 정보 창"),
                              "R12a owned Details toggle absent",seconds=12)
                assert choice.is_enabled() and choice.element_info.process_id==app.app.pid
                assert h.owner(h.u.GetForegroundWindow())==app.app.pid
                return choice

            h.wait(lambda:any(source.name in r.window_text() for r in app.rows("Left")),
                   "R12a owned source not loaded",seconds=20)
            assert "열기" in app.el("FileInfoToggleButton").element_info.name
            choice=open_details_menu()
            assert int(choice.iface_toggle.CurrentToggleState)==0
            rect=choice.rectangle()
            mouse.click(coords=(rect.mid_point().x,rect.mid_point().y))
            h.wait(lambda:"닫기" in app.el("FileInfoToggleButton").element_info.name,
                   "R12a background Details did not open",seconds=12)
            result["background_opened_by_physical_click"]=True
            assert app.el("TextPreviewBody").window_text().strip()==""
            assert "꺼" in app.el("TextPreviewStatus").window_text()
            result["no_implicit_preview_read"]=True
            app.capture("r12a-background-details-open")

            choice=open_details_menu()
            assert int(choice.iface_toggle.CurrentToggleState)==1
            rect=choice.rectangle()
            mouse.click(coords=(rect.mid_point().x,rect.mid_point().y))
            h.wait(lambda:"열기" in app.el("FileInfoToggleButton").element_info.name,
                   "R12a background Details did not close",seconds=12)
            result["background_closed_by_physical_click"]=True
            result["original_unchanged"]=source.read_bytes()==content
        result["app"]=app.report
        assert result["original_unchanged"] and app.report["normal_exit"]
        assert app.report["original_settings_unchanged"] and app.report["profile_removed"]
        success=True
    finally:
        result["owned_source_preserved_on_exit"]=source.read_bytes()==content
        if success:
            assert folder.parent==BASE.resolve() and not folder.is_symlink()
            shutil.rmtree(folder)
            result["fixture_removed"]=True
        (BASE/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),
                                         encoding="utf-8")
        print("R12A_BACKGROUND_DETAILS_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
