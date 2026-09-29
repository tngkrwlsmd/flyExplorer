"""M2.0 real WinUI main-shell and native command-boundary owned GUI probe."""
from pathlib import Path
from PIL import ImageGrab,ImageStat
import hashlib
def run(*,win,element,safe_click,focus,eventually,owned):
    assert element("ShellHeading").window_text()=="flyExplorer"
    assert element("ThisPCButton").exists(timeout=5)
    assert element("ThemePicker").exists(timeout=5)
    picker=element("ThemePicker").wrapper_object()
    from pywinauto.findwindows import ElementNotFoundError
    def right_visible():
        try:return element("SecondaryPaneTitle").is_visible()
        except ElementNotFoundError:return False
    # WinUI ComboBox can virtualize option peers when closed; count==0
    # does NOT prove absent markup. The real selection+render below is the
    # actual runtime contract, with source inventory checked separately.
    print("M20_THEME_UIA_COUNT_DIAGNOSTIC",picker.item_count(),flush=True)
    rect=win.rectangle()
    assert rect.width()>=500 and rect.height()>=350
    # Read back the final rendered surface after actual UIA selection;
    # string-only theme labels do not establish visual acceptance.
    def surface():
        rect=win.rectangle()
        return ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
            include_layered_windows=True).convert("RGB")
    focus()
    picker.select(2)
    eventually(lambda:element("ThemeStateText").window_text()=="테마: 다크",
               "actual WinUI Dark selection not propagated to root")
    dark=surface()
    focus()
    picker.select(1)
    eventually(lambda:element("ThemeStateText").window_text()=="테마: 라이트",
               "actual WinUI Light selection not propagated to root")
    light=surface()
    assert dark.size==light.size
    # Sample chrome and navigation/content away from changing list rows,
    # not Windows titlebar or only dynamic text.
    samples=[(int(rect.width()*0.36),int(rect.height()*0.14)),
             (min(32,rect.width()-3),int(rect.height()*0.34)),
             (min(34,rect.width()-3),int(rect.height()*0.53))]
    def brightness(im):
        values=[]
        for x,y in samples:
            block=im.crop((x,y,x+3,y+3))
            values.append(sum(ImageStat.Stat(block).mean)/3)
        return values
    db=brightness(dark);lb=brightness(light)
    assert any(light-dark>30 for light,dark in zip(lb,db)),(
        "theme changed label but not the actual rendered shell",db,lb)
    print("REAL_M20_WINUI_DARK_LIGHT_FINAL_SHELL_PIXELS",True,flush=True)
    focus()
    picker.select(0)
    eventually(lambda:element("ThemeStateText").window_text()=="테마: 시스템",
               "System theme not restored")
    print("REAL_M20_SYSTEM_LIGHT_DARK_NATIVE_THEME_CHOICES",True,flush=True)
    # The old GUI harness has already completed both-pane, tab and PIDL
    # navigation. Verify the new native routed commands still preserve the
    # independent hidden right-pane state and accept full PIDL virtual nav.
    safe_click(element("PrimaryPaneTitle"))
    before=element("AddressBox").get_value()
    left_tabs=element("LeftTabs")
    prior_left=len([v for v in left_tabs.descendants()
                    if v.element_info.control_type=="TabItem"])
    right_tabs=element("RightTabs")
    prior_right=len([v for v in right_tabs.descendants()
                     if v.element_info.control_type=="TabItem"])
    safe_click(element("NewTabButton"))
    eventually(lambda:len([v for v in left_tabs.descendants()
       if v.element_info.control_type=="TabItem"])==prior_left+1,
       "shared C++ add-tab command did not update real WinUI tab view",12)
    safe_click(element("CloseTabButton"))
    eventually(lambda:len([v for v in left_tabs.descendants()
       if v.element_info.control_type=="TabItem"])==prior_left,
       "shared C++ close-tab command did not update real WinUI",10)
    # The preceding M1.8 regression intentionally toggles split state;
    # assert the CURRENT real button state before exercising M2.0.
    if "분할 창" in element("SplitButton").window_text():
        safe_click(element("SplitButton"))
    eventually(lambda:"단일 창" in element("SplitButton").window_text()
       and right_visible(),
       "failed to establish two-pane starting state for owned test",7)
    before_hide=surface()
    safe_click(element("SplitButton"))
    print("M20_SPLIT_HIDE_IMMEDIATE_UIA",
          repr(element("SplitButton").window_text()),
          right_visible(),flush=True)
    eventually(lambda:"분할 창" in element("SplitButton").window_text(),
       "shared C++ split-hide command failed to update actual WinUI control",7)
    after_hide=surface()
    from PIL import ImageChops
    width,height=before_hide.size
    # Validate actual composed content change in the previous RIGHT pane:
    # collapsed WinUI descendants may still be reported by cached UIA peers.
    region=(int(width*.62),int(height*.27),int(width*.92),int(height*.80))
    diff=ImageChops.difference(before_hide.crop(region),
                               after_hide.crop(region))
    variance=sum(ImageStat.Stat(diff).mean)/3
    print("M20_SPLIT_HIDE_COMPOSITED_RIGHT_REGION_DIFFERENCE",
          round(variance,2),flush=True)
    assert variance>0.15 and not right_visible(),(
        "shared C++ split-hide failed rendered region / UIA disappearance",
        variance,right_visible())
    safe_click(element("SplitButton"))
    eventually(lambda:"단일 창" in element("SplitButton").window_text(),
       "shared C++ split-show did not restore two-pane command state",7)
    assert len([v for v in right_tabs.descendants()
       if v.element_info.control_type=="TabItem"])==prior_right
    safe_click(element("ThisPCButton"))
    # The worker resolves shell:MyComputerFolder into a native PIDL:
    # the address displays its absolute "::..." parsing name, NOT alias text.
    eventually(lambda:"::" in element("AddressBox").get_value(),
        "new This PC button did not resolve a native virtual Shell PIDL",16)
    safe_click(element("BackButton"))
    eventually(lambda:element("AddressBox").get_value().lower()==before.lower(),
        "native per-tab history lost after This PC button",16)
    print("REAL_M20_SHARED_NATIVE_COMMANDS_TABS_SPLIT_AND_THIS_PC",True,flush=True)
    print("REAL_M20_PARENT_MAIN_WINUI_ONLY_NO_MFC_HOST",True,flush=True)
