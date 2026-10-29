"""Owned PX17 menu actions and matched Light/Dark native-caption captures."""
from __future__ import annotations
import argparse
import base64
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from paths import ROOT, app_exe
from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase",choices=("before","after"),required=True)
    args=parser.parse_args()
    from pywinauto import Desktop, keyboard
    from PIL import ImageGrab
    from uia_polling import wait_until
    import psutil
    exe=app_exe("Release")
    base=ROOT/"logs"/"px17-caption-owned"
    base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix=args.phase+"-",dir=base)).resolve()
    fixture=owned/"fixture"
    fixture.mkdir()
    (fixture/"Nested").mkdir()
    sentinel=fixture/"owned-original.txt"
    sentinel.write_bytes(b"owned-menu-caption-original")
    env={k:v for k,v in os.environ.items() if not k.startswith("FLY")}
    for key in ("APPDATA","LOCALAPPDATA","USERPROFILE","TEMP","TMP"):
        path=owned/key.lower()
        path.mkdir()
        env[key]=str(path)
    legacy_root,legacy=snapshot_legacy_profile()
    user=c.windll.user32
    user.GetForegroundWindow.restype=w.HWND
    user.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
    user.PostMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
    user.SendMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
    user.MoveWindow.argtypes=(w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.BOOL)
    app=subprocess.Popen([str(exe),str(fixture)],cwd=exe.parent,env=env)
    hwnd=None
    completed=False
    result={"phase":args.phase,"exe_sha256":hashlib.sha256(exe.read_bytes()).hexdigest()}
    screenshots=[]

    def wait(fn,label,seconds=20):
        return wait_until(fn,label,seconds=seconds,interval=.15)

    def pid(handle):
        value=w.DWORD()
        user.GetWindowThreadProcessId(handle,c.byref(value))
        return value.value

    try:
        def view():
            nonlocal hwnd
            assert app.poll() is None,"owned app exited"
            assert Path(psutil.Process(app.pid).exe()).resolve()==exe.resolve()
            wins=[x for x in Desktop(backend="uia").windows(process=app.pid)
                  if "flyExplorer" in x.window_text()]
            if len(wins)!=1:return None
            hwnd=wins[0].handle
            assert pid(hwnd)==app.pid
            return Desktop(backend="uia").window(handle=hwnd)
        win=wait(view,"owned app unavailable")
        element=lambda name:win.child_window(auto_id=name)
        wait(lambda:"owned-original.txt" in " ".join(
            r.window_text() for r in element("LeftFiles").descendants(control_type="ListItem")),
            "owned folder not rendered")
        win.set_focus()
        user.MoveWindow(hwnd,60,60,960,519,True)

        def guard():
            assert pid(user.GetForegroundWindow())==app.pid,"foreign foreground"

        def capture(label,caption=False):
            guard()
            time.sleep(.35)
            rect=win.rectangle()
            box=(rect.right-220,rect.top,rect.right,rect.top+50) if caption else (
                rect.left,rect.top,rect.right,rect.bottom)
            path=base/(args.phase+"-"+label+".png")
            ImageGrab.grab(bbox=box,include_layered_windows=True).save(path)
            screenshots.append((label,path))

        for theme,index in (("light",1),("dark",2)):
            element("ThemePicker").select(index)
            wait(lambda:("라이트" if index==1 else "다크") in
                 element("ThemeStateText").window_text(),"theme not applied")
            capture(theme+"-caption",True)
        result["window_pixels"]=[win.rectangle().width(),win.rectangle().height()]
        result["dpi"]=user.GetDpiForWindow(w.HWND(hwnd))
        element("ThemePicker").select(1)

        # Exercise standard Windows caption commands on the owned HWND only.
        user.SendMessageW(hwnd,0x112,0xF020,0)
        wait(lambda:user.IsIconic(w.HWND(hwnd)),"native minimize failed",5)
        user.SendMessageW(hwnd,0x112,0xF120,0)
        user.SendMessageW(hwnd,0x112,0xF030,0)
        wait(lambda:user.IsZoomed(w.HWND(hwnd)),"native maximize failed",5)
        user.SendMessageW(hwnd,0x112,0xF120,0)
        result["native_minimize_maximize_restore"]=True

        def open_more():
            guard()
            keyboard.send_keys("{ESC}{ESC}")
            element("MoreButton").invoke()

        def menu(key):
            for top in Desktop(backend="uia").windows(process=app.pid):
                for node in top.descendants(control_type="MenuItem"):
                    if node.element_info.automation_id==key:return node
            return None

        open_more()
        if args.phase=="before":
            capture("more-menu")
            keyboard.send_keys("{ESC}")
        else:
            def open_new_submenu():
                def submenu():
                    return next((node for top in Desktop(backend="uia").windows(process=app.pid)
                        for node in top.descendants(control_type="MenuItem")
                        if node.window_text()=="현재 폴더에 새 항목 만들기"),None)
                wait(submenu,"new-item parent menu absent",8).iface_expand_collapse.Expand()
                return wait(lambda:menu("NewTextFileMenuItem"),"new-item submenu absent",8)
            open_new_submenu()
            capture("new-menu")
            nodes=[menu("NewFolderMenuItem"),menu("NewTextFileMenuItem")]
            rects=[node.rectangle() for node in nodes]
            path=base/(args.phase+"-new-submenu.png")
            ImageGrab.grab(bbox=(min(r.left for r in rects),min(r.top for r in rects),
                max(r.right for r in rects),max(r.bottom for r in rects)),
                include_layered_windows=True).save(path)
            screenshots.append(("new-submenu",path))
            menu("NewTextFileMenuItem").invoke()
            edit=element("FileNameBox")
            wait(lambda:edit.get_value()=="새 텍스트 문서.txt","name editor not opened")
            edit.set_edit_text("menu-created.txt")
            edit.type_keys("{ENTER}")
            created=fixture/"menu-created.txt"
            wait(created.is_file,"toolbar text command did not create file")
            assert created.read_bytes()==b""
            print("PX17_FIRST_CREATE=PASS",flush=True)
            assert not (fixture/"Nested"/created.name).exists()
            # Duplicate and invalid names must never overwrite existing bytes.
            def new_text():
                open_more()
                open_new_submenu().invoke()
                wait(lambda:edit.get_value()=="새 텍스트 문서.txt","name editor unavailable")
            new_text()
            edit.set_edit_text("owned-original.txt")
            edit.type_keys("{ENTER}")
            wait(lambda:"이미 존재" in element("StatusText").window_text(),"collision not reported")
            assert sentinel.read_bytes()==b"owned-menu-caption-original"
            print("PX17_COLLISION_PRESERVED=PASS",flush=True)
            new_text()
            edit.set_edit_text("../escape.txt")
            edit.type_keys("{ENTER}")
            wait(lambda:"파일 이름만" in element("StatusText").window_text(),"invalid name not rejected")
            assert not (owned/"escape.txt").exists()
            print("PX17_INVALID_NAME=PASS",flush=True)
            new_text()
            edit.set_edit_text("canceled.txt")
            edit.type_keys("{ESC}")
            assert not (fixture/"canceled.txt").exists()
            print("PX17_CANCEL=PASS",flush=True)
            # Activate the other pane, navigate it to an owned folder, then use
            # the same menu. The command must target that pane's current tab.
            element("SecondaryPaneTitle").invoke()
            guard()
            address=element("AddressBox")
            address.set_edit_text(str(fixture/"Nested"))
            address.type_keys("{ENTER}")
            wait(lambda:address.get_value().casefold()==str(fixture/"Nested").casefold(),
                 "right owned folder did not settle")
            new_text()
            edit.set_edit_text("right-created.txt")
            edit.type_keys("{ENTER}")
            wait((fixture/"Nested"/"right-created.txt").is_file,"active pane target incorrect")
            assert not (fixture/"right-created.txt").exists()
            wait(lambda:"right-created.txt" in " ".join(r.window_text()
                 for r in element("RightFiles").descendants(control_type="ListItem")),
                 "right pane did not display its created file")
            print("PX17_ACTIVE_RIGHT_PANE=PASS",flush=True)
            result["px17_create_collision_invalid_cancel_active_pane"]=True

        completed=True
    finally:
        if app.poll() is None:
            if hwnd and pid(hwnd)==app.pid:
                user.PostMessageW(hwnd,0x10,0,0)
                try:app.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    app.terminate();app.wait(timeout=6)
            else:
                app.terminate();app.wait(timeout=6)
        result["normal_exit"]=app.returncode==0
        assert_legacy_profile_unchanged(legacy_root,legacy)
        result["legacy_profile_unchanged"]=True
        assert sentinel.read_bytes()==b"owned-menu-caption-original"
        result["owned_original_preserved"]=True
        if completed and result["normal_exit"]:
            assert owned.parent==base.resolve() and not owned.is_symlink()
            shutil.rmtree(owned)
            result["owned_fixture_profiles_removed"]=True
        print("PX17_CAPTION_RESULT="+json.dumps(result),flush=True)
        for label,path in screenshots:
            print("OWNED_PNG_"+args.phase+"_"+label+"="+
                  base64.b64encode(path.read_bytes()).decode("ascii"),flush=True)
    assert completed and result["normal_exit"]
    return 0


if __name__=="__main__":
    raise SystemExit(main())
