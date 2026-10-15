"""F05 opt-in grouped list real GUI, using disposable shell-owned files.

Requires FLY_F05_GROUP_ONLY=YES. Never modifies user folders, display DPI,
system accessibility, private preferences, or remote windows.
"""
from pathlib import Path
from uuid import uuid4
import ctypes
from ctypes import wintypes
from pywinauto import Desktop
from paths import ROOT


def run(*,win,element,safe_click,eventually,left,right):
    assert (left/"readme.txt").is_file()
    assert (left/"group-guide.md").is_file()
    assert (left/"group-events.log").is_file()
    assert right.is_dir()
    app=win.wrapper_object()
    owner=app.element_info.process_id

    def rows():
        return [x for x in element("LeftFiles").descendants()
                if x.element_info.control_type=="ListItem"]

    def row(name):
        return next((x for x in rows() if name in x.window_text()),None)

    def buttons(term):
        return [x for x in element("LeftFiles").descendants()
                if x.element_info.control_type=="Button"
                and term in x.window_text()]

    def snap(stage):
        user=ctypes.windll.user32
        user.GetForegroundWindow.restype=wintypes.HWND
        user.GetWindowThreadProcessId.argtypes=[
            wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        hwnd=user.GetForegroundWindow()
        pid=wintypes.DWORD()
        if hwnd:user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        assert pid.value==owner, "Refuse screenshot outside owned app process"
        path=ROOT/"logs"/"f05-visual"
        assert path.resolve(strict=False).is_relative_to(
            (ROOT/"logs").resolve())
        path.mkdir(parents=True,exist_ok=True)
        img=app.capture_as_image()
        assert img.width>=650 and img.height>=400
        name=path/("f05-"+stage+"-"+uuid4().hex+".png")
        img.save(name,format="PNG")
        assert 1000<name.stat().st_size<3000000
        print("F05_GROUP_SCREENSHOT_"+stage.upper()+"_PNG="+str(name),flush=True)

    eventually(lambda:row("readme.txt") and row("group-guide.md")
               and row("group-events.log"),
               "Owned grouping fixture rows missing",12)
    snap("before")
    # Group mode is opt-in and must remain disabled until clicked.
    bar=element("ViewButton")
    assert bar.exists(timeout=2)
    # A registered Windows file-type description need not literally
    # contain "txt 파일". Do not treat localized Shell labels as proof
    # of worker metadata completion.
    bar.invoke()
    def owned_group_menu():
        # Desktop is a root wrapper, not a UIA window specification;
        # Desktop(...).child_window() does not exist in this pywinauto.
        # MenuFlyout may be a popup HWND, so search ONLY owned-process
        # windows (never interact with unrelated desktop controls).
        for top in Desktop(backend="uia").windows():
            if top.element_info.process_id!=owner:
                continue
            for item in [top,*top.descendants()]:
                if item.element_info.automation_id=="ViewGroupByTypeItem":
                    return item
        return None
    menu=eventually(owned_group_menu,
                    "Owned View grouping menu item not accessible",9)
    assert menu.element_info.process_id==owner, (
        "Refuse invoking a foreign popup control")
    menu.invoke()
    eventually(lambda:buttons(".txt") and buttons(".md")
               and buttons(".log"),
               "Full model group headings did not render",9)
    assert row("readme.txt") and row("group-guide.md")
    assert not any("전체 목록과 파일 유형 정보가 준비된" in
                   x.window_text() for x in
                   [element("StatusText")]), (
        "Group mode refused incomplete metadata")
    print("F05_GROUP_COMPLETE_LOCAL_MODEL=PASS",flush=True)
    snap("grouped")

    # Real file remains selectable; disclosure must be a distinct non-file
    # action. Collapse .md while .txt is selected and restore both identities.
    safe_click(row("readme.txt"))
    eventually(lambda:bool(row("readme.txt").iface_selection_item.CurrentIsSelected),
               "Selected original file lost identity under grouping",8)
    md=eventually(lambda:buttons(".md")[0] if buttons(".md") else None,
                  "Markdown disclosure missing",8)
    safe_click(md)
    eventually(lambda:row("group-guide.md") is None,
               "Collapsing Markdown retained its file row",9)
    assert row("readme.txt"), "Collapsing another group erased TXT rows"
    print("F05_GROUP_COLLAPSE_ISOLATED=PASS",flush=True)
    expand=eventually(lambda:buttons(".md")[0] if buttons(".md") else None,
                      "Collapsed Markdown button unavailable",8)
    safe_click(expand)
    eventually(lambda:row("group-guide.md") is not None,
               "Expanding Markdown did not restore file row",9)
    print("F05_GROUP_EXPAND_RESTORES_ROWS=PASS",flush=True)
    snap("expanded")
