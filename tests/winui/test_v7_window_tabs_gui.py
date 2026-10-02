"""v7 real WinUI functional top-level window-tab acceptance."""
from pathlib import Path
import ctypes
import os
import subprocess
import psutil
from pywinauto import Desktop,mouse
from pywinauto.keyboard import send_keys

def run(*,win,element,safe_click,focus,eventually,owned,localdata,env,exe):
    strip=element("WindowTabStrip").wrapper_object()
    def tabs():
        return [x for x in strip.descendants() if x.element_info.control_type=="TabItem"]
    def address(): return element("AddressBox").get_value().lower()
    def click_tab(index):
        item=tabs()[index];r=item.rectangle();pt=(r.left+min(24,max(8,r.width()//4)),r.mid_point().y)
        mouse.click(coords=pt)
    eventually(lambda:len(tabs())==1,"v7 initial window tab missing",8)
    initial_address=address()
    left=element("LeftFiles")
    def nested_rows():
        return [x for x in element("LeftFiles").descendants()
                if x.element_info.control_type=="ListItem" and "Nested" in x.window_text()]
    eventually(lambda:len(nested_rows())==1,"v7 Nested folder row missing",10)
    # AddressBox Enter has its own full-suite contract. Here use the actual
    # folder activation route so this targeted test measures WindowTab-owned
    # navigation/history rather than keyboard-edit focus timing.
    nested_rows()[0].double_click_input()
    eventually(lambda:element("BackButton").is_enabled() and
               not any(x.element_info.control_type=="ListItem"
                       for x in element("LeftFiles").descendants()),
               "v7 tab A did not commit navigation to empty Nested folder",14)
    # Explorer Ctrl+T opens the configured default location (This PC on the
    # benchmark machine), not a shallow clone of A's active path/history.
    focus();safe_click(element("LeftFiles"));send_keys("^t")
    eventually(lambda:len(tabs())==2,"Ctrl+T did not create functional window tab",10)
    eventually(lambda:"nested" not in address() and bool(address()),
               "new window tab did not open an independent default location",14)
    b_address=address()
    safe_click(element("SplitButton"))
    eventually(lambda:"분할 창" in element("SplitButton").window_text(),
               "tab B split state did not become single-pane",8)
    # Click A and prove its path and split state were retained.
    click_tab(0)
    eventually(lambda:"nested" in address(),"A->B->A lost tab A path",14)
    eventually(lambda:"단일 창" in element("SplitButton").window_text(),
               "A->B->A lost tab A split state",8)
    # Click B, then exercise keyboard rotation using the distinct addresses.
    click_tab(1)
    eventually(lambda:address()==b_address,"tab B path lost",10)
    focus();safe_click(element("LeftFiles"));send_keys("^+{TAB}")
    eventually(lambda:"nested" in address(),"Ctrl+Shift+Tab did not activate previous window tab",10)
    send_keys("^{TAB}");eventually(lambda:address()==b_address,
                                    "Ctrl+Tab did not activate next window tab",10)
    send_keys("^w");eventually(lambda:len(tabs())==1,"Ctrl+W did not close active window tab",10)
    eventually(lambda:"nested" in address(),"closing B did not return to intact A",12)
    # The actual TabView add button must also be exposed/clickable.
    add=None
    for b in strip.descendants(control_type="Button"):
        aid=(getattr(b.element_info,"automation_id","") or "").lower()
        name=(b.window_text() or "").lower()
        if "add" in aid or "new tab" in name or "새 탭" in name:
            add=b;break
    assert add is not None,"TabView add button not exposed to UIA"
    add.click_input();eventually(lambda:len(tabs())==2,"TabView + button did not create window tab",10)
    eventually(lambda:address()==b_address,"TabView + did not use Explorer-like default location",12)
    if os.environ.get("FLY_V7_WINDOW_TABS_SESSION")=="YES":
        # The private session deliberately accepts fixed local filesystem
        # folders only. Seed BOTH durable panes with owned local paths before
        # collapsing B; the hidden right pane must round-trip too.
        def visit(side,path,child):
            focus();safe_click(element("LeftFiles" if side==0 else "RightFiles"))
            box=element("AddressBox");box.set_edit_text(str(path));focus()
            box.type_keys("{ENTER}",set_foreground=True)
            surface=element("LeftFiles" if side==0 else "RightFiles")
            eventually(lambda:any(child in x.window_text() for x in surface.descendants()),
                       "v7 session pane did not load owned local path",17)
        visit(0,Path(owned)/"Right","Secondary")
        visit(1,Path(owned)/"Left","Nested")
        safe_click(element("LeftFiles"))
        b_address=address()
        safe_click(element("SplitButton"))
        eventually(lambda:"분할 창" in element("SplitButton").window_text(),
                   "session tab B split state did not become single-pane",8)
        profile=localdata/"flyExplorer"/"winui-session-v1.bin"
        if not element("SaveSessionButton").exists(timeout=.4):
            safe_click(element("WorkspacePanelButton"))
        assert element("SaveSessionButton").exists(timeout=4)
        safe_click(element("SaveSessionButton"))
        eventually(lambda:profile.is_file() and profile.stat().st_size>=96 and
                   "저장했습니다" in element("StatusText").window_text(),
                   "v7 multi-window private session was not saved",16)
        original=profile.read_bytes();assert original.startswith(b"FXSESS23")
        child_env={**env,"FLY_M23_OWNED_SESSION":"YES"}
        child=subprocess.Popen([str(exe),str(owned),"--m23-owned-auto-restore"],
                               cwd=exe.parent,env=child_env)
        child_hwnd=None
        try:
            def restored():
                nonlocal child_hwnd
                if child.poll() is not None:return False
                proc=psutil.Process(child.pid)
                if Path(proc.exe()).resolve()!=exe.resolve():
                    raise AssertionError("foreign executable inherited v7 session child PID")
                matches=[w for w in Desktop(backend="uia").windows(process=child.pid)
                         if "flyExplorer" in w.window_text()]
                if len(matches)!=1:return False
                target=Desktop(backend="uia").window(handle=matches[0].handle)
                strip2=target.child_window(auto_id="WindowTabStrip")
                address2=target.child_window(auto_id="AddressBox")
                split2=target.child_window(auto_id="SplitButton")
                if not (strip2.exists(timeout=.2) and address2.exists(timeout=.2) and
                        split2.exists(timeout=.2)):return False
                top=[x for x in strip2.descendants() if x.element_info.control_type=="TabItem"]
                if len(top)!=2:return False
                if address2.get_value().lower()!=b_address:return False
                if "분할 창" not in split2.window_text():return False
                child_hwnd=matches[0].handle
                return True
            eventually(restored,"v7 child did not restore active WindowTab B",28)
            target=Desktop(backend="uia").window(handle=child_hwnd)
            strip2=target.child_window(auto_id="WindowTabStrip")
            top=[x for x in strip2.descendants() if x.element_info.control_type=="TabItem"]
            top[0].click_input()
            address2=target.child_window(auto_id="AddressBox")
            eventually(lambda:"nested" in address2.get_value().lower(),
                       "v7 child did not restore WindowTab A path",12)
            split2=target.child_window(auto_id="SplitButton")
            eventually(lambda:"단일 창" in split2.window_text(),
                       "v7 child did not restore WindowTab A split state",8)
            # Activating a restored WindowTab queues an owned Refresh. During
            # that refresh the navigation chrome is deliberately disabled, so
            # re-resolve the live UIA peer and wait for the refresh to settle
            # before judging the restored history.
            def restored_back_ready():
                back=target.child_window(auto_id="BackButton")
                return back.exists(timeout=.2) and back.is_enabled()
            eventually(restored_back_ready,
                       "v7 child did not restore WindowTab A back history",16)
            assert profile.read_bytes()==original
            print("REAL_V7_MULTI_WINDOW_SESSION_RESTART_RESTORE",True,flush=True)
            print("REAL_V7_WINDOW_TAB_HISTORY_AND_SPLIT_RESTORE",True,flush=True)
        finally:
            if child.poll() is None:
                if child_hwnd is not None:
                    assert ctypes.WinDLL("user32",use_last_error=True).PostMessageW(child_hwnd,0x10,0,0)
                else: child.terminate()
                child.wait(timeout=16)
            assert child.returncode==0,child.returncode
        focus()
        if not element("ClearSessionButton").exists(timeout=.4):
            safe_click(element("WorkspacePanelButton"))
        safe_click(element("ClearSessionButton"))
        eventually(lambda:not profile.exists(),"v7 private session cleanup failed",12)
    focus();safe_click(element("LeftFiles"));send_keys("^w")
    eventually(lambda:len(tabs())==1,"cleanup close after v7 session test failed",10)
    # A still owns the history created at the start of this test. Use that
    # committed route for cleanup instead of depending on AddressBox UIA edit/
    # focus timing after the session child closes.
    safe_click(element("BackButton"))
    eventually(lambda:address().rstrip("\/")==initial_address.rstrip("\/").lower(),
               "v7 cleanup did not restore the original owned folder",14)
    print("REAL_V7_FUNCTIONAL_WINDOW_TABS_STATE_ISOLATION",True,flush=True)
    print("REAL_V7_WINDOW_TAB_KEYBOARD_AND_ADD_BUTTON",True,flush=True)
