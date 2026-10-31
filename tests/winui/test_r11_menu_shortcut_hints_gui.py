"""R11 owned selected-file context menu smoke and screenshot evidence.

Shortcut text is only visually accepted after reviewing the owned menu image;
this test does not claim UIA exposes KeyboardAcceleratorTextOverride.
"""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

from pywinauto import Desktop
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

BASE=ROOT/"logs"/"r11-shortcut-hints-owned-gui-20261031"
EXPECTED=("잘라내기","복사","경로 복사","이름 바꾸기","삭제")


def main():
    if BASE.exists() and any(BASE.iterdir()):
        raise RuntimeError("Retained R11 GUI evidence exists; preserve it")
    BASE.mkdir(parents=True,exist_ok=True)
    h.BASE=BASE
    folder=Path(tempfile.mkdtemp(prefix="r11-fixture-",dir=BASE)).resolve()
    original=folder/"r11-owned-source.txt"
    payload=b"r11 owned menu-only check\n"
    original.write_bytes(payload)
    result={"exe_sha256":hashlib.sha256(app_exe("Release").read_bytes()).hexdigest()}
    completed=False
    try:
        with h.App(app_exe("Release"),folder,"r11-shortcut-hints","dark") as app:
            def source_row():
                found=[r for r in app.rows("Left") if original.name in r.window_text()]
                return found[0] if len(found)==1 else None
            row=h.wait(source_row,"owned source row unavailable",seconds=20)
            row.select()
            h.wait(lambda:source_row() is not None and source_row().is_selected(),
                   "owned row not selected",seconds=8)
            app.win.set_focus()
            assert h.owner(h.u.GetForegroundWindow())==app.app.pid
            source_row().click_input(button="right")

            def owned_menu():
                for top in Desktop(backend="uia").windows(process=app.app.pid):
                    try:
                        if top.element_info.process_id!=app.app.pid:
                            continue
                        items=[x for x in top.descendants(control_type="MenuItem")
                               if x.element_info.process_id==app.app.pid]
                        names=[x.window_text().strip() for x in items]
                        if all(any(n==label or n.startswith(label+" ")
                                   for n in names) for label in EXPECTED):
                            return top,items,names
                    except (RuntimeError,LookupError):
                        continue
                return None

            top,items,names=h.wait(owned_menu,"owned file menu missing",seconds=12)
            assert h.owner(h.u.GetForegroundWindow())==app.app.pid
            assert all(any(x.is_enabled() and
                           (x.window_text().strip()==label or
                            x.window_text().strip().startswith(label+" "))
                           for x in items) for label in EXPECTED)
            result["selected_items_visible"]=True
            result["observed_item_names"]=names[:30]
            # Capture only a window belonging to this isolated app process.
            image=top.capture_as_image()
            assert image.width>100 and image.height>50
            image.save(BASE/"owned-selected-menu.png")
            result["owned_menu_screenshot"]="owned-selected-menu.png"
            result["accelerator_text_visual_review"]="pending"
            app.keys("{ESC}")
            assert original.read_bytes()==payload
            result["source_unchanged"]=True
        result["app"]=app.report
        assert app.report["normal_exit"] and app.report["original_settings_unchanged"]
        assert app.report["profile_removed"]
        completed=True
    finally:
        if completed:
            assert folder.parent==BASE.resolve() and not folder.is_symlink()
            shutil.rmtree(folder)
            result["fixture_removed"]=True
        (BASE/"result.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print("R11_SHORTCUT_HINTS_GUI_RESULT="+
              json.dumps(result,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
