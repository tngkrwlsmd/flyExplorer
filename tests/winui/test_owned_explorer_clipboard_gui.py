"""Four actual app-owned WinUI <-> newly opened Explorer file clipboard flows.

GLOBAL clipboard is intentionally cleared (user approved). Only exact fresh
test-owned files, one new Explorer HWND matching exact private folder, and an
exact owned WinUI child process may receive physical keys. Never close, focus,
navigate or automate pre-existing Explorer windows. The original global
clipboard is NOT preserved and cannot be losslessly restored.
"""
import argparse
import ctypes as c
from ctypes import wintypes as w
import hashlib
import os
from pathlib import Path
from paths import ROOT, APP, app_exe
from uia_polling import wait_until
import shutil
import subprocess
import sys
import tempfile
import time

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
u=c.WinDLL("user32",use_last_error=True)
u.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
u.GetWindowThreadProcessId.restype=w.DWORD
u.GetAncestor.argtypes=[w.HWND,w.UINT]
u.GetAncestor.restype=w.HWND
u.GetForegroundWindow.restype=w.HWND
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
u.PostMessageW.restype=w.BOOL

def until(f,why,seconds=17):
    return wait_until(f, why, seconds=seconds, interval=.19)

def own_focus(win,hwnd,allowed_pid=None):
    win.set_focus()
    until(lambda: int(u.GetAncestor(u.GetForegroundWindow(),2))==int(hwnd),
          "Foreground window changed; no input delivered",5)
    if allowed_pid is not None:
        pid=w.DWORD()
        u.GetWindowThreadProcessId(w.HWND(hwnd),c.byref(pid))
        assert pid.value==allowed_pid,"Owned WinUI HWND PID mismatch"

def clipboard_clear():
    import win32clipboard as cb
    for attempt in range(10):
        try:
            cb.OpenClipboard()
            try:cb.EmptyClipboard()
            finally:cb.CloseClipboard()
            return True
        except Exception:
            time.sleep(.13)
    return False

def clipboard_formats():
    import win32clipboard as cb
    cb.OpenClipboard()
    try:
        found=set()
        value=0
        while True:
            value=cb.EnumClipboardFormats(value)
            if not value:break
            found.add(value)
        preferred=cb.RegisterClipboardFormat("Preferred DropEffect")
        paths=[]
        if cb.IsClipboardFormatAvailable(15):
            # Must copy only owned filenames; never inspect user clipboard
            # before this harness has explicitly cleared it.
            import win32api
            import win32gui
            from ctypes import windll
            handle=cb.GetClipboardDataHandle(15)
            windll.shell32.DragQueryFileW.argtypes=[
                w.HANDLE,w.UINT,w.LPWSTR,w.UINT]
            windll.shell32.DragQueryFileW.restype=w.UINT
            count=windll.shell32.DragQueryFileW(int(handle),0xffffffff,None,0)
            for i in range(min(count,32)):
                chars=windll.shell32.DragQueryFileW(int(handle),i,None,0)
                path=c.create_unicode_buffer(chars+1)
                windll.shell32.DragQueryFileW(int(handle),i,path,chars+1)
                paths.append(path.value)
        effect=None
        if preferred in found:
            import struct
            # For a registered binary clipboard format the Win32 HGLOBAL
            # handle, not pywin32's format-dependent conversion, is truth.
            handle=cb.GetClipboardDataHandle(preferred)
            if handle:
                kernel=c.windll.kernel32
                kernel.GlobalSize.argtypes=[w.HGLOBAL]
                kernel.GlobalSize.restype=c.c_size_t
                kernel.GlobalLock.argtypes=[w.HGLOBAL]
                kernel.GlobalLock.restype=c.c_void_p
                kernel.GlobalUnlock.argtypes=[w.HGLOBAL]
                kernel.GlobalUnlock.restype=w.BOOL
                native=w.HGLOBAL(int(handle))
                size=kernel.GlobalSize(native)
                if 4<=size<=65536:
                    ptr=kernel.GlobalLock(native)
                    if ptr:
                        try:
                            effect=struct.unpack("<I",c.string_at(ptr,4))[0]
                        finally:
                            kernel.GlobalUnlock(native)
            print("OWNED_OS_PREFERRED_DROP_EFFECT",effect,flush=True)
        return paths,effect
    finally:cb.CloseClipboard()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration",choices=("Debug","Release"),
                        default="Debug")
    parser.add_argument("--apply-clear-clipboard",action="store_true")
    parser.add_argument("--only-explorer-cut",action="store_true",
                        help="Isolated regression for fourth flow")
    args=parser.parse_args()
    if os.name!="nt" or not args.apply_clear_clipboard:
        print("BLOCKED: explicit user-approved --apply-clear-clipboard required")
        return 2
    import psutil
    import pythoncom
    import win32com.client
    from pywinauto import Desktop
    pythoncom.CoInitialize()
    a=APP
    root=ROOT
    exe=app_exe(args.configuration)
    assert exe.is_file(),"Missing exact owned preview"
    mfc=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    hashes={n:hashlib.sha256((mfc/n).read_bytes()).digest()
            for n in LEGACY if (mfc/n).is_file()}
    base=root/"logs"/"m24"
    base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="interop-owned-",dir=base))
    left,right=owned/"left",owned/"right"
    left.mkdir()
    right.mkdir()
    fixture={}
    for folder,label,body in [
        (left,"winui-copy","winui copy"),
        (left,"winui-cut","winui move"),
        (right,"explorer-copy","explorer copy"),
        (right,"explorer-cut","explorer move")]:
        name=label+"-"+chr(0xD55C)+chr(0xAE00)+".txt"
        p=folder/name
        p.write_text(body,encoding="utf-8")
        fixture[label]=(p,body)
    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        dest=owned/key.lower()
        dest.mkdir()
        env[key]=str(dest)
    for key in ("FLY_M23_OWNED_SESSION","FLY_M23_OWNED_DRAG_TEST",
                "FLY_M23_OWNED_DRAG_TRACE"):
        env.pop(key,None)
    shell=win32com.client.Dispatch("Shell.Application")
    preexisting={int(s.HWND) for s in shell.Windows()}
    print("PREEXISTING_EXPLORER_HANDLES_COUNT_ONLY",len(preexisting),flush=True)
    preview=None;winui=None;explorer=None;owned_explorer=None
    results={}
    try:
        assert clipboard_clear(),"Could not clear approved global clipboard"
        print("USER_APPROVED_GLOBAL_CLIPBOARD_CLEARED",True,flush=True)
        preview=subprocess.Popen([str(exe),str(left)],cwd=exe.parent,env=env,
                                 stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        def ready_winui():
            nonlocal winui
            if preview.poll() is not None:return False
            if Path(psutil.Process(preview.pid).exe()).resolve()!=exe.resolve():
                raise AssertionError("WinUI process ownership mismatch")
            candidates=[v for v in Desktop(backend="uia").windows(process=preview.pid)
                        if "flyExplorer" in v.window_text()]
            if len(candidates)!=1:return False
            winui=Desktop(backend="uia").window(handle=candidates[0].handle)
            return winui.child_window(auto_id="LeftFiles").exists(timeout=.2)
        until(ready_winui,"Exact owned WinUI preview not ready",22)
        # Ask the real Explorer Shell to create a fresh window. Require both
        # a previously unseen HWND and its COM LocationURL matching our own
        # fixture folder before ANY interaction.
        shell.Explore(str(right))
        target=right.resolve().as_uri().rstrip("/").casefold()
        def ready_explorer():
            nonlocal explorer,owned_explorer
            found=[]
            for v in shell.Windows():
                try:
                    if int(v.HWND) not in preexisting and \
                       str(v.LocationURL).rstrip("/").casefold()==target:
                        found.append(v)
                except Exception:pass
            if len(found)!=1:return False
            owned_explorer=found[0]
            explorer=Desktop(backend="uia").window(
                handle=int(owned_explorer.HWND))
            return explorer.exists(timeout=.2)
        until(ready_explorer,
              "No uniquely new test-folder Explorer window; refuse any Explorer automation",20)
        print("FRESH_EXPLORER_OWNED_WINDOW_IDENTIFIED",True,flush=True)

        def winui_row(label):
            file=fixture[label][0].name
            return next((v for v in winui.child_window(
                auto_id="LeftFiles").descendants()
                if v.element_info.control_type=="ListItem" and
                file in v.window_text()),None)
        def winui_select(label):
            until(lambda:winui_row(label) is not None,
                  "Owned WinUI source item not present: "+label,15)
            own_focus(winui,winui.handle,preview.pid)
            winui_row(label).select()
            until(lambda:winui_row(label) is not None and
                  winui_row(label).is_selected(),
                  "Owned WinUI source row selection failed: "+label,5)
        def winui_shortcut(keys):
            own_focus(winui,winui.handle,preview.pid)
            area=winui.child_window(auto_id="LeftFiles")
            area.set_focus()
            own_focus(winui,winui.handle,preview.pid)
            area.type_keys(keys,set_foreground=False)
        def explorer_validate():
            assert int(owned_explorer.HWND)==int(explorer.handle)
            assert int(owned_explorer.HWND) not in preexisting
            assert str(owned_explorer.LocationURL).rstrip("/").casefold()==target
            own_focus(explorer,explorer.handle)
        def explorer_shortcut(keys):
            explorer_validate()
            explorer.type_keys(keys,set_foreground=False)
        def explorer_select(label):
            explorer_validate()
            name=fixture[label][0].name
            item=owned_explorer.Document.Folder.Items().Item(name)
            assert item is not None,"Explorer cannot find exact owned fixture"
            owned_explorer.Document.SelectItem(item,1|4|8|16)
            def selected():
                picked=owned_explorer.Document.SelectedItems()
                return picked.Count==1 and picked.Item(0).Name==name
            until(selected,"Only exact owned Explorer item may be selected",7)
        def clipboard_expected(label,effect):
            expected=fixture[label][0].resolve()
            reported_error=False
            def correct():
                nonlocal reported_error
                try:
                    paths,got_effect=clipboard_formats()
                    if len(paths)!=1 or Path(paths[0]).resolve()!=expected:
                        return False
                    # Effect is mandatory for cut; Explorer may use delayed
                    # representation so don't call any cut success silently.
                    return got_effect==effect if effect==2 else True
                except Exception as exc:
                    if not reported_error:
                        print("OWNED_CLIPBOARD_OBSERVATION_ERROR",
                              type(exc).__name__,flush=True)
                        reported_error=True
                    return False
            until(correct,"Actual OS CF_HDROP/effect differs from owned selection",5)
            print("REAL_OS_CF_HDROP_OWNED",label,
                  "CUT" if effect==2 else "COPY",flush=True)
        def file_result(label,target_dir,is_cut):
            original,text=fixture[label]
            output=target_dir/original.name
            until(lambda:output.is_file() and
                  output.read_text(encoding="utf-8")==text and
                  (not is_cut or not original.exists()),
                  "Actual file copy/move didn't complete: "+label,25)
            assert original.exists()==(not is_cut)
            results[label]=True
            print("ACTUAL_OWNED_EXPLORER_INTEROP",label,"PASS",flush=True)
        if not args.only_explorer_cut:
            winui_select("winui-copy")
            winui_shortcut("^c")
            clipboard_expected("winui-copy",1)
            explorer_shortcut("^v")
            file_result("winui-copy",right,False)
            explorer_select("explorer-copy")
            explorer_shortcut("^c")
            clipboard_expected("explorer-copy",1)
            winui_shortcut("^v")
            file_result("explorer-copy",left,False)
            # An actual IFileOperation may publish files before its UI
            # completion callback clears the pending transfer state.
            until(lambda:winui.child_window(
                auto_id="CopyButton").is_enabled(),
                "Prior WinUI Shell transfer is still pending",15)
            winui_select("winui-cut")
            winui_shortcut("^x")
            clipboard_expected("winui-cut",2)
            explorer_shortcut("^v")
            file_result("winui-cut",right,True)
            # The native directory watcher may temporarily mark the
            # source pane as pending when Explorer moves our file out.
            until(lambda:winui_row("winui-cut") is None and
                  winui_row("explorer-copy") is not None and
                  winui.child_window(auto_id="CopyButton").is_enabled(),
                  "Source pane has not settled after Explorer paste",18)
        explorer_select("explorer-cut")
        explorer_shortcut("^x")
        clipboard_expected("explorer-cut",2)
        until(lambda:winui.child_window(auto_id="CopyButton").is_enabled(),
              "Target pane is still performing previous Shell work",12)
        winui_shortcut("^v")
        time.sleep(1.2)
        print("LAST_CUT_WINUI_STATUS",
              winui.child_window(auto_id="StatusText").window_text().encode(
                  "unicode_escape").decode("ascii")[:225],flush=True)
        file_result("explorer-cut",left,True)
    finally:
        # Never destroy a preexisting Explorer window; at most close the
        # fresh new exact HWND that remains on our exact owned folder.
        if owned_explorer is not None:
            try:
                if int(owned_explorer.HWND) not in preexisting and \
                   str(owned_explorer.LocationURL).rstrip("/").casefold()==right.resolve().as_uri().rstrip("/").casefold():
                    u.PostMessageW(int(owned_explorer.HWND),0x10,0,0)
            except Exception:pass
        if preview is not None and preview.poll() is None:
            try:
                if winui is not None and Path(
                    psutil.Process(preview.pid).exe()).resolve()==exe.resolve():
                    u.PostMessageW(int(winui.handle),0x10,0,0)
                    preview.wait(timeout=9)
            except Exception:
                if preview.poll() is None:
                    preview.terminate()
                    preview.wait(timeout=8)
        cleared=clipboard_clear()
        unchanged=all((mfc/n).is_file() and
           hashlib.sha256((mfc/n).read_bytes()).digest()==h
           for n,h in hashes.items())
        print("GLOBAL_CLIPBOARD_CLEARED_AFTER_TEST",cleared,flush=True)
        print("ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL",unchanged,flush=True)
        print("ACTUAL_INTEROP_PASSED_COUNT",len(results),flush=True)
        if len(results)==(1 if args.only_explorer_cut else 4) and cleared and unchanged:
            shutil.rmtree(owned)
        else:
            print("OWNED_INTEROP_FIXTURE_RETAINED",str(owned),flush=True)
    return 0 if len(results)==(1 if args.only_explorer_cut else 4) and cleared and unchanged else 1

if __name__=="__main__":
    sys.exit(main())
