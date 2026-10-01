"""Actual M2.3 private session GUI, fully owned disposable directories/profile.

Never call Windows clipboard write/read or mutate the user's Recycle Bin.
"""
from pathlib import Path
import ctypes
import os
import subprocess
import psutil
from pywinauto import Desktop

def run(*,win,element,safe_click,focus,eventually,
        left,right,localdata,env,exe):
    assert left.is_dir() and right.is_dir() and left!=right
    profile=localdata/"flyExplorer"/"winui-session-v1.bin"
    assert profile.parent.parent==localdata
    def visit(side,path,child):
        focus()
        safe_click(element("PrimaryPaneTitle" if side==0 else "SecondaryPaneTitle"))
        box=element("AddressBox")
        box.set_edit_text(str(path))
        focus()
        box.type_keys("{ENTER}",set_foreground=True)
        directory=element("LeftFiles" if side==0 else "RightFiles")
        eventually(lambda:any(child in e.window_text()
             for e in directory.descendants()),
             "isolated native child not loaded in pane "+str(side),17)
    visit(0,left,"Nested")
    focus();element("SortPicker").select(2)
    visit(1,right,"Secondary")
    focus();element("SortPicker").select(3)
    if os.environ.get("FLY_M23_OWNED_DRAG_TEST")=="YES":
        # Physical in-window drag: strictly owned source and destination.
        from pywinauto import mouse
        import time
        source=next((e for e in element("LeftFiles").descendants()
             if e.element_info.control_type=="ListItem" and
                "끌기.txt" in e.window_text()),None)
        assert source is not None,"owned drag source row missing"
        dst=element("RightFiles").rectangle()
        origin=source.rectangle().mid_point()
        target=(dst.left+min(130,int(dst.width()/3)),
                dst.top+min(160,int(dst.height()/2)))
        focus()
        mouse.move(coords=(origin.x,origin.y))
        mouse.press(button="left",coords=(origin.x,origin.y))
        try:
            time.sleep(.12)
            mouse.move(coords=(origin.x+27,origin.y+18))
            time.sleep(.19)
            if os.environ.get("FLY_M23_OWNED_DRAG_TRACE")=="YES":
                print("M23_DRAG_TRACE_AFTER_START",
                      element("StatusText").window_text().encode("unicode_escape").decode("ascii"),flush=True)
            mouse.move(coords=target)
            time.sleep(.20)
            if os.environ.get("FLY_M23_OWNED_DRAG_TRACE")=="YES":
                print("M23_DRAG_TRACE_OVER_TARGET",
                      element("StatusText").window_text().encode("unicode_escape").decode("ascii"),flush=True)
        finally:
            mouse.release(button="left",coords=target)
        print("M23_DRAG_OWNED_COORDINATES",
              (origin.x,origin.y),target,flush=True)
        print("M23_DRAG_OWNED_NATIVE_STATUS",
              element("StatusText").window_text().encode("unicode_escape").decode("ascii"),
              flush=True)
        eventually(lambda:(right/"끌기.txt").is_file(),
           "WinUI same-app drag/drop failed to copy owned Korean file",16)
        assert (right/"끌기.txt").read_text(encoding="utf-8")=="owned M23 drag-copy"
        assert (left/"끌기.txt").is_file()
        print("REAL_M23_WINUI_INTERNAL_TWO_PANE_OWNED_KOREAN_DRAG_COPY",True,flush=True)
    focus()
    if not element("SaveSessionButton").exists(timeout=.4):
        safe_click(element("WorkspacePanelButton"))
    assert element("SaveSessionButton").exists(timeout=4)
    safe_click(element("SaveSessionButton"))
    eventually(lambda:profile.is_file() and profile.stat().st_size>=72
               and "저장했습니다" in element("StatusText").window_text(),
        "explicit opt-in local session file not atomically saved",15)
    original=profile.read_bytes()
    assert original.startswith(b"FXSESS23")
    print("REAL_M23_EXPLICIT_KOREAN_PRIVATE_SESSION_SAVE_WITH_REAL_TABS",True,flush=True)
    # Restart this EXACT owned private-preview binary and explicitly permit
    # the synthetic initial folder override for testing auto restore.
    child_env={**env,"FLY_M23_OWNED_SESSION":"YES"}
    child=subprocess.Popen(
        [str(exe),str(left),"--m23-owned-auto-restore"],cwd=exe.parent,
        env=child_env)
    owned_hwnd=None
    try:
        def ready():
            nonlocal owned_hwnd
            if child.poll() is not None:return False
            proc=psutil.Process(child.pid)
            if Path(proc.exe()).resolve()!=exe.resolve():
                raise AssertionError("Foreign executable inherited owned PID")
            assert proc.cmdline()[1]==str(left)
            matches=[w for w in Desktop(backend="uia").windows(process=child.pid)
                     if "flyExplorer" in w.window_text()]
            if len(matches)!=1:return False
            target=Desktop(backend="uia").window(handle=matches[0].handle)
            rightlist=target.child_window(auto_id="RightFiles")
            leftlist=target.child_window(auto_id="LeftFiles")
            sort=target.child_window(auto_id="SortPicker")
            if not (rightlist.exists(timeout=.25) and
                    leftlist.exists(timeout=.25) and sort.exists(timeout=.25)):
                return False
            if not (any("Secondary" in x.window_text()
                        for x in rightlist.descendants()) and
                    any("Nested" in x.window_text()
                        for x in leftlist.descendants())):
                return False
            owned_hwnd=matches[0].handle
            return True
        eventually(ready,"owned restarted preview did not restore both distinct private folders",25)
        print("REAL_M23_SECOND_OWNED_PROCESS_AUTO_RESTORED_BOTH_KOREAN_PANES",True,flush=True)
        assert profile.read_bytes()==original
    finally:
        if child.poll() is None:
            assert Path(psutil.Process(child.pid).exe()).resolve()==exe.resolve()
            assert psutil.Process(child.pid).cmdline()[1]==str(left)
            if owned_hwnd is None:
                child.terminate()
                child.wait(timeout=10)
                raise AssertionError("Exact owned restart child did not finish native restore")
            user32=ctypes.WinDLL("user32",use_last_error=True)
            user32.GetWindowThreadProcessId.argtypes=(
                ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong))
            owner=ctypes.c_ulong()
            user32.GetWindowThreadProcessId(owned_hwnd,ctypes.byref(owner))
            assert owner.value==child.pid
            assert user32.PostMessageW(owned_hwnd,0x10,0,0)
            try:child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.terminate();child.wait(timeout=8)
                raise AssertionError("Exact owned auto-restored child failed to exit")
        assert child.returncode==0,child.returncode
    focus()
    # Diagnose the original parent's real UIA state after an owned child exits.
    # Never silently reopen/accept an unobservable control.
    controls=("WorkspacePanelButton","WorkspaceFileBox",
              "SaveSessionButton","RestoreSessionButton","ClearSessionButton")
    observed={key:element(key).exists(timeout=.25) for key in controls}
    print("M23_PARENT_AFTER_CHILD_PANEL_UIA",observed,
          "WINDOW",win.rectangle(),flush=True)
    assert observed["ClearSessionButton"], (
      "original parent lost ClearSessionButton after owned child",observed)
    button=element("ClearSessionButton").wrapper_object()
    bounds=button.rectangle()
    window_bounds=win.rectangle()
    print("M23_CLEAR_BUTTON_BOUNDS",bounds,"PARENT",window_bounds,
          "VISIBLE",button.is_visible(),flush=True)
    if (bounds.right>window_bounds.right or
        bounds.left<window_bounds.left or
        bounds.bottom>window_bounds.bottom):
        raise AssertionError("ClearSessionButton outside owned parent bounds")
    safe_click(button)
    eventually(lambda:not profile.exists() and
        "지웠습니다" in element("StatusText").window_text(),
        "explicit opt-out failed to remove only the private session",14)
    print("REAL_M23_PRIVATE_SESSION_CLEAR_REVOKES_FUTURE_AUTO_RESTORE",True,flush=True)
    # Exact same fixture enforces the original MFC six profile hashes in
    # the outer test_shell_gui.py finally block.
