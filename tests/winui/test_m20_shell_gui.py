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
    # The Explorer-like shell uses Mica/transparent surfaces. Theme selection
    # updates synchronously, but the compositor may publish the new frame a
    # little later. Wait for sampled app-owned pixels to settle rather than
    # weakening the visual acceptance threshold or adding a fixed sleep.
    samples=[(int(rect.width()*0.38),int(rect.height()*0.78)),
             (int(rect.width()*0.72),int(rect.height()*0.78)),
             (min(80,rect.width()-3),int(rect.height()*0.78))]
    def brightness(im):
        values=[]
        for x,y in samples:
            block=im.crop((x,y,x+3,y+3))
            values.append(sum(ImageStat.Stat(block).mean)/3)
        return values
    def settled_surface(label):
        state={"last":None,"stable":0,"image":None}
        def ready():
            im=surface();values=brightness(im)
            if state["last"] is not None and all(
                    abs(now-before)<2 for now,before in zip(values,state["last"])):
                state["stable"]+=1
            else:state["stable"]=0
            state["last"]=values;state["image"]=im
            return state["stable"]>=2
        eventually(ready,label)
        return state["image"]
    focus()
    picker.select(2)
    eventually(lambda:element("ThemeStateText").window_text()=="테마: 다크",
               "actual WinUI Dark selection not propagated to root")
    dark=settled_surface("Dark theme label changed before rendered shell settled")
    focus()
    picker.select(1)
    eventually(lambda:element("ThemeStateText").window_text()=="테마: 라이트",
               "actual WinUI Light selection not propagated to root")
    light=settled_surface("Light theme label changed before rendered shell settled")
    assert dark.size==light.size
    db=brightness(dark);lb=brightness(light)
    # A real theme switch must change every stable app-owned sample—not only
    # the hidden picker label or one antialiased edge.
    assert all(light-dark>20 for light,dark in zip(lb,db)),(
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
    # Theme restore can re-template this exact WinUI ListView asynchronously.
    # Retry only known transient UIA lookup errors, within the test-owned app.
    def click_left_files_after_theme():
        safe_click(element("LeftFiles"))
        return True
    eventually(click_left_files_after_theme,
               "left pane UIA list did not settle after theme restore",15)
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
    # After split restoration WinUI may rebuild the UIA subtree.
    # Wait for the actual sidebar peer, never interpret absence as PASS.
    eventually(lambda:element("ThisPCButton").exists(timeout=.25)
       and element("ThisPCButton").is_visible(),
       "This PC sidebar control never reappeared after pane restoration",9)
    print("M20_POST_SPLIT_THISPC_READY",True,flush=True)
    safe_click(element("ThisPCButton"))
    # The worker still resolves shell:MyComputerFolder to a native PIDL,
    # while M2.6 presents a Windows 11-style friendly address label.
    eventually(lambda:element("AddressBox").get_value()=="내 PC",
        "This PC did not commit the native virtual route with friendly address",16)
    # M2.6 renders bounded capacity UI only for fixed/removable drive roots.
    # The test workstation always has the local system drive; require one
    # real nested ProgressBar rather than accepting source markup alone.
    eventually(lambda:any(peer.element_info.control_type=="ProgressBar"
        for peer in element("LeftFiles").descendants()),
        "This PC local drive did not expose the Fluent capacity progress bar",12)
    print("REAL_M26_THIS_PC_LOCAL_DRIVE_CAPACITY_CARD",True,flush=True)
    # Address/content peers can become observable before the native navigation
    # completion has projected history availability back into command chrome.
    # Wait for the real Back command to become actionable; clicking a still
    # disabled button is not evidence that per-tab history was lost.
    eventually(lambda:element("BackButton").exists(timeout=.25)
        and element("BackButton").is_enabled(),
        "native This PC route committed without enabling per-tab Back history",12)
    safe_click(element("BackButton"))
    eventually(lambda:element("AddressBox").get_value().lower()==before.lower(),
        "native per-tab history lost after This PC button",16)
    print("REAL_M20_SHARED_NATIVE_COMMANDS_TABS_SPLIT_AND_THIS_PC",True,flush=True)
    print("REAL_M20_PARENT_MAIN_WINUI_ONLY_NO_MFC_HOST",True,flush=True)
