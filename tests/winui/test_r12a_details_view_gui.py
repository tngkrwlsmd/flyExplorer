"""R12a owned Windows GUI: physically toggle the existing Details pane.

Uses only an isolated file and profile. Never enables text reading or alters OS state.
"""
from pathlib import Path
from contextlib import ExitStack
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import shutil
import tempfile
import time

from pywinauto import Desktop, mouse
from pywinauto.keyboard import send_keys
import benchmark_filtered_folder_gui as h
from paths import ROOT, app_exe

BASE=ROOT/"logs"/"r12a-details-owned-gui-r28-events-20261102"


def main():
    if BASE.exists() and any(BASE.iterdir()):
        raise RuntimeError("Retained R12a GUI evidence exists")
    BASE.mkdir(parents=True,exist_ok=True)
    h.BASE=BASE
    folder=Path(tempfile.mkdtemp(prefix="r12a-fixture-",dir=BASE)).resolve()
    source=folder/"r12a-owned-file.txt"
    content=b"r12a-owned-detail-pane-never-auto-preview"
    source.write_bytes(content)
    result={
        "exe_sha256":hashlib.sha256(app_exe("Release").read_bytes()).hexdigest(),
        "owned_topmost_lift":False,
        "owned_topmost_restored":False,
        "owned_topmost_requested":False,
    }
    success=False
    # The existing harness excludes FLY* vars, but forwards this test-only
    # switch to the isolated flyExplorer child process.
    os.environ["R12_UI_TRACE"]="1"
    try:
        with h.App(app_exe("Release"),folder,"r12a-details","dark") as app, ExitStack() as z_order_cleanup:
            def read_owned_trace():
                # Read only the private test profile. Never inspect a desktop
                # trace or a symlink; bound the bytes and accepted field names.
                trace=app.profile/"tmp"/"flyExplorer-r12-events.log"
                if not trace.is_file() or trace.is_symlink():
                    return [],"missing_owned_temp_trace"
                raw=trace.read_bytes()
                if len(raw)>16384:
                    return [],"bounded_file_exceeded"
                names={"pane_state","other_view_click","flyout_open",
                       "details_click","flyout_closed","queue_missing",
                       "action23_dispatch","action23_skipped",
                       "toolbar_gone","queue_added",
                       "details_tap_fallback","action23_stale",
                       "details_press","details_release",
                       "details_pstate","details_rstate","details_ostate",
                       "details_cancel","details_capture_lost",
                       "details_enter","details_exit","details_tap",
                       "other_press","other_release",
                       "other_pstate","other_rstate",
                       "other_cancel","other_capture_lost",
                       "other_enter","other_exit","other_tap"}
                events=[]
                for line in raw.decode("ascii","replace").splitlines():
                    parts=line.split()
                    if (len(parts)!=3 or not parts[0].isdigit() or
                            not parts[2].isdigit() or parts[1] not in names):
                        return [],"unexpected_event_shape"
                    events.append({"tick":int(parts[0]),"phase":parts[1],
                                   "value":int(parts[2])})
                return events,None
            def capture_owned_trace():
                events,error=read_owned_trace()
                if error:
                    result["r12_trace_error"]=error
                    print("R12_EVENT_TRACE_READ_FAILED="+error,flush=True)
                    return
                result["r12_trace_events"]=events[:96]
                result["r12_trace_count"]=len(events)
                print("R12_EVENT_TRACE="+json.dumps(events[:96]),flush=True)
            # This ExitStack unwinds before h.App deletes the private profile.
            z_order_cleanup.callback(capture_owned_trace)
            def owned_file():
                matches=[r for r in app.rows("Left") if source.name in r.window_text()]
                return matches[0] if len(matches)==1 else None
            h.wait(owned_file,"R12a owned file missing",seconds=20).select()
            h.wait(lambda:owned_file() is not None and owned_file().is_selected(),
                   "R12a owned selection not ready",seconds=8)

            def detail_entry():
                matches={}
                for top in Desktop(backend="uia").windows(process=app.app.pid):
                    for item in top.descendants(control_type="MenuItem"):
                        if (item.element_info.process_id==app.app.pid and
                            item.element_info.automation_id=="ViewFileInfoPaneItem"):
                            rect=item.rectangle()
                            matches[(rect.left,rect.top,rect.right,rect.bottom)]=item
                return next(iter(matches.values())) if len(matches)==1 else None

            def place_owned_view_button():
                # Move ONLY this test-owned app window. Do not raise, hide, or
                # inspect unrelated window content. Never click a foreign pixel.
                user=ctypes.windll.user32
                user.WindowFromPoint.argtypes=[wintypes.POINT]
                user.WindowFromPoint.restype=wintypes.HWND
                assert h.owner(app.hwnd)==app.app.pid
                width=user.GetSystemMetrics(0)
                height=user.GetSystemMetrics(1)
                layouts=((20,20,1000,600),(30,65,900,560),(90,50,900,560))
                for left,top,wide,tall in layouts:
                    if left+wide>width or top+tall>height:
                        continue
                    assert user.MoveWindow(app.hwnd,left,top,wide,tall,True)
                    app.win.set_focus()
                    button=app.el("ViewButton")
                    if not button.is_visible() or not button.is_enabled():
                        continue
                    rect=button.rectangle()
                    point=(rect.left+rect.width()//2,
                           rect.top+rect.height()//2)
                    hit=user.WindowFromPoint(wintypes.POINT(*point))
                    if hit and h.owner(hit)==app.app.pid:
                        result["owned_view_placement"]={
                            "window":[left,top,wide,tall],
                            "button_rect":[rect.left,rect.top,
                                           rect.right,rect.bottom],
                            "hit_owned":True,
                        }
                        print("R12A_OWNED_VIEW_PLACEMENT="+json.dumps(
                            result["owned_view_placement"]),flush=True)
                        return
                # The prior layouts were genuinely blocked by another window.
                # R23 lifts ONLY the test-owned app temporarily, never touches
                # the obstructing window or sends input to a foreign pixel.
                user.GetWindowLongW.argtypes=[wintypes.HWND,ctypes.c_int]
                user.GetWindowLongW.restype=ctypes.c_long
                if user.GetWindowLongW(app.hwnd,-20)&0x00000008:
                    raise AssertionError(
                        "Owned View button blocked despite existing topmost state")
                user.SetWindowPos.argtypes=[
                    wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,
                    ctypes.c_int,ctypes.c_int,wintypes.UINT]
                user.SetWindowPos.restype=wintypes.BOOL
                # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
                flags=0x0001|0x0002|0x0010
                if not user.SetWindowPos(
                        app.hwnd,wintypes.HWND(-1),0,0,0,0,flags):
                    raise RuntimeError("Failed to raise test-owned app window")
                result["owned_topmost_requested"]=True

                def restore_owned_z_order():
                    if h.owner(app.hwnd)!=app.app.pid:
                        raise RuntimeError("Lost test-window ownership before restore")
                    if not user.SetWindowPos(
                            app.hwnd,wintypes.HWND(-2),0,0,0,0,flags):
                        raise RuntimeError("Failed to restore test-owned app Z order")
                    result["owned_topmost_restored"]=True

                # ExitStack unwinds before h.App closes the owned app, even
                # when the GUI test fails. Nothing outside this HWND is moved.
                z_order_cleanup.callback(restore_owned_z_order)
                app.win.set_focus()
                button=app.el("ViewButton")
                rect=button.rectangle()
                point=(rect.left+rect.width()//2,
                       rect.top+rect.height()//2)
                hit=user.WindowFromPoint(wintypes.POINT(*point))
                # Record each owned-input prerequisite separately. The R23
                # combined assertion could not distinguish hidden/disabled UI
                # from an actual hit-test ownership failure. Do not record
                # foreign HWND, process metadata, names or screen content.
                gate={
                    "visible":bool(button.is_visible()),
                    "enabled":bool(button.is_enabled()),
                    "hwnd_present":bool(hit),
                    "hit_owned":bool(hit and h.owner(hit)==app.app.pid),
                }
                result["owned_topmost_input_gate"]=gate
                print("R12A_OWNED_TOPMOST_INPUT_GATE="+json.dumps(
                    gate),flush=True)
                if not (gate["visible"] and gate["enabled"] and gate["hit_owned"]):
                    raise AssertionError(
                        "Owned View-button preflight failed: see individual flags")
                result["owned_topmost_lift"]=True
                result["owned_view_placement"]={
                    "method":"temporary-test-owned-topmost",
                    "button_rect":[rect.left,rect.top,rect.right,rect.bottom],
                    "hit_owned":True,
                }
                print("R12A_OWNED_VIEW_PLACEMENT="+json.dumps(
                    result["owned_view_placement"]),flush=True)

            def click_detail(*,inspect_pointer=False):
                app.win.set_focus()
                assert h.owner(h.u.GetForegroundWindow())==app.app.pid
                # R36 reached the owned window but never emitted flyout_open.
                # Let foreground/focus activation settle and ensure the
                # physical hit-point actually belongs to ViewButton in UIA.
                time.sleep(0.25)
                view=app.el("ViewButton")
                rect=view.rectangle()
                point=(rect.left+rect.width()//2,rect.top+rect.height()//2)
                user=ctypes.windll.user32
                user.WindowFromPoint.argtypes=[wintypes.POINT]
                user.WindowFromPoint.restype=wintypes.HWND
                hit=user.WindowFromPoint(wintypes.POINT(*point))
                assert hit and h.owner(hit)==app.app.pid, (
                    "Refusing physical click on foreign View-button pixel")
                peer=Desktop(backend="uia").from_point(*point)
                node=peer
                ancestry=[]
                for depth in range(6):
                    info=node.element_info
                    assert info.process_id==app.app.pid, (
                        "View-button click target left owned app")
                    ancestry.append(info.automation_id or "")
                    if info.automation_id=="ViewButton":
                        break
                    node=node.parent()
                    assert node is not None, (
                        "View-button pixel has no owned UIA ancestor")
                result["view_button_pointer_target"]={
                    "hit_type":peer.element_info.control_type,
                    "hit_id":peer.element_info.automation_id,
                    "ui_ancestry":ancestry,
                    "owned":True,
                    "focus_settle_ms":250,
                }
                print("R12A_VIEW_BUTTON_POINTER_TARGET="+json.dumps(
                    result["view_button_pointer_target"]),flush=True)
                assert "ViewButton" in ancestry, (
                    "Physical View-button point did not hit ViewButton")
                # R42: use an actual mouse click on the already-verified
                # owned ViewButton point, rather than keyboard Enter. This
                # independently tests the full mouse-only two-toggle route.
                assert h.owner(h.u.GetForegroundWindow())==app.app.pid
                mouse.click(button="left",coords=point)
                immediate_owner=h.owner(h.u.GetForegroundWindow())
                result["view_opener_mode"]="physical_mouse_view_button"
                result["view_pointer_immediate"]={
                    "hit_owned":True,
                    "foreground_owned_after_click":immediate_owner==app.app.pid,
                    "item_visible_immediately":detail_entry() is not None,
                }
                print("R12A_VIEW_POINTER_IMMEDIATE="+json.dumps(
                    result["view_pointer_immediate"]),flush=True)
                if immediate_owner!=app.app.pid:
                    raise AssertionError(
                        "View mouse opener lost owned foreground")
                try:
                    item=h.wait(detail_entry,
                                "R12a View details entry not found",seconds=12)
                except AssertionError:
                    # Diagnostic only: preserve the original missing-item failure.
                    # Enumerate owned UIA roots, including any separate popup HWND.
                    desktop=Desktop(backend="uia")
                    roots=desktop.windows(process=app.app.pid)
                    seen=[]
                    for top in roots[:12]:
                        nodes=[]
                        for node in top.descendants():
                            info=node.element_info
                            ident=info.automation_id or ""
                            if ident.startswith("View"):
                                box=node.rectangle()
                                nodes.append({
                                    "id":ident[:80],
                                    "type":info.control_type,
                                    "rect":[box.left,box.top,box.right,box.bottom],
                                })
                            if len(nodes)>=35:
                                break
                        box=top.rectangle()
                        seen.append({
                            "root_type":top.element_info.control_type,
                            "rect":[box.left,box.top,box.right,box.bottom],
                            "menuitems":len(top.descendants(control_type="MenuItem")),
                            "view_controls":nodes,
                        })
                    result["first_view_open_diagnostic"]={
                        "foreground_owned":
                            h.owner(h.u.GetForegroundWindow())==app.app.pid,
                        "view_button_visible":app.el("ViewButton").is_visible(),
                        "view_button_enabled":app.el("ViewButton").is_enabled(),
                        "owner_root_count":len(roots),
                        "owned_roots":seen,
                    }
                    print("R12A_FIRST_VIEW_OPEN_DIAG="+json.dumps(
                        result["first_view_open_diagnostic"],
                        ensure_ascii=False),flush=True)
                    raise
                assert item.is_visible() and item.is_enabled()
                assert item.element_info.process_id==app.app.pid
                assert h.owner(h.u.GetForegroundWindow())==app.app.pid
                if not inspect_pointer:
                    # The item must not be pinned against the screen's top edge.
                    rect=item.rectangle()
                    result["first_menu_item_top"]=rect.top
                    assert rect.top>=45, "Details menu item still against screen top"
                    item.click_input()
                    return
                # R26: isolate pointer gesture symmetry. The preceding R25
                # probe pressed/released near the leading checkmark area,
                # whereas the first successful click used click_input() at
                # the item's center. Keep the same exact product binary and
                # test-owned input/element guards, but match the first gesture.
                rect=item.rectangle()
                assert rect.width()>75 and rect.height()>16
                assert rect.top>=45, "Second Details menu item overlaps titlebar"
                point=((rect.left+rect.right)//2,(rect.top+rect.bottom)//2)
                assert rect.left<point[0]<rect.right
                assert rect.top<point[1]<rect.bottom
                u=ctypes.windll.user32
                u.WindowFromPoint.argtypes=[wintypes.POINT]
                u.WindowFromPoint.restype=wintypes.HWND
                hit=u.WindowFromPoint(wintypes.POINT(*point))
                assert hit and h.owner(hit)==app.app.pid, (
                    "Refusing second centered click outside owned application")
                peer=Desktop(backend="uia").from_point(*point)
                target={
                    "item_rect":[rect.left,rect.top,rect.right,rect.bottom],
                    "point":list(point),
                    "hit_type":peer.element_info.control_type,
                    "hit_id":peer.element_info.automation_id,
                    "hit_name":(peer.element_info.name or "")[:100],
                    "hit_owner":peer.element_info.process_id,
                }
                result["second_pointer_target"]=target
                print("R12A_SECOND_POINTER_TARGET="+json.dumps(
                    target,ensure_ascii=False),flush=True)
                assert peer.element_info.process_id==app.app.pid, (
                    "Refusing centered click on foreign UIA target")
                # A centered pixel may hit the menu item's TextBlock rather
                # than the MenuItem itself. Validate each owner and the
                # bounded UIA ancestry before any physical input.
                node=peer
                owned_lineage=[]
                for depth in range(5):
                    info=node.element_info
                    assert info.process_id==app.app.pid, (
                        "Centered target ancestry left the owned application")
                    owned_lineage.append(info.automation_id or "")
                    if info.automation_id=="ViewFileInfoPaneItem":
                        break
                    node=node.parent()
                    assert node is not None, (
                        "Centered target did not resolve to the owned menu item")
                assert "ViewFileInfoPaneItem" in owned_lineage, (
                    "Centered pixel has no owned Details menu ancestor")
                result["second_pointer_ancestry"]=owned_lineage
                result["second_pointer_gesture"]="same_center_click_input_as_first"
                item.click_input()

            def menu_closed():
                try:
                    entry=detail_entry()
                    return entry is None or not entry.is_visible()
                except (RuntimeError,LookupError):
                    return True

            assert "열기" in app.el("FileInfoToggleButton").element_info.name
            place_owned_view_button()
            click_detail()
            h.wait(lambda:"닫기" in app.el("FileInfoToggleButton").element_info.name,
                   "R12a details pane did not open",seconds=12)
            result["details_opened_by_physical_click"]=True
            assert app.el("TextPreviewBody").window_text().strip()==""
            assert "꺼" in app.el("TextPreviewStatus").window_text()
            result["no_implicit_preview_read"]=True
            # A command can update Details state before its flyout dismissal
            # finishes. Wait for that original menu to close before re-opening.
            h.wait(menu_closed,"R12a first View menu never closed",seconds=8)
            result["first_menu_dismissed"]=True
            # MenuItem disappearance can precede input/focus capture release.
            # Keep the exact product binary and pointer target unchanged; only
            # settle the first flyout on the owned window before reopening.
            status_rect=app.el("StatusText").rectangle()
            neutral=(status_rect.left+12,
                     (status_rect.top+status_rect.bottom)//2)
            user=ctypes.windll.user32
            user.WindowFromPoint.argtypes=[wintypes.POINT]
            user.WindowFromPoint.restype=wintypes.HWND
            neutral_hwnd=user.WindowFromPoint(wintypes.POINT(*neutral))
            assert neutral_hwnd and h.owner(neutral_hwnd)==app.app.pid, (
                "Refusing diagnostic pointer movement outside owned app")
            mouse.move(coords=neutral)
            time.sleep(0.8)
            assert menu_closed(), "First View flyout reopened during settlement"
            assert "닫기" in app.el("FileInfoToggleButton").element_info.name
            result["first_menu_input_settle_ms"]=800

            click_detail(inspect_pointer=True)
            try:
                h.wait(lambda:"열기" in app.el("FileInfoToggleButton").element_info.name,
                       "R12a details pane did not close",seconds=12)
            except AssertionError:
                # Snapshot the second physical attempt BEFORE the fallback
                # View item click or UIA Invoke can contaminate its event list.
                events,trace_error=read_owned_trace()
                if trace_error:
                    result["second_click_trace_error"]=trace_error
                else:
                    opens=[i for i,event in enumerate(events)
                           if event["phase"]=="flyout_open"]
                    if len(opens)>=2:
                        attempt=events[opens[-1]:]
                        stages={e["phase"] for e in attempt}
                        result["second_click_trace_events"]=attempt[:64]
                        result["second_click_trace_count"]=len(attempt)
                        result["second_click_event_gates"]={
                            phase:(phase in stages)
                            for phase in ("details_press","details_release",
                                          "details_pstate","details_rstate",
                                          "details_ostate","details_cancel",
                                          "details_capture_lost",
                                          "details_enter","details_exit",
                                          "details_tap","details_click","flyout_closed",
                                          "queue_added","action23_dispatch")
                        }
                    else:
                        result["second_click_trace_error"]="no_second_flyout_open"
                print("R12A_SECOND_ATTEMPT_TRACE="+json.dumps({
                    "error":result.get("second_click_trace_error"),
                    "gates":result.get("second_click_event_gates"),
                    "count":result.get("second_click_trace_count",0)
                },ensure_ascii=False),flush=True)
                entry=detail_entry()
                result["second_click_diagnostic"]={
                    "pane_toggle":app.el("FileInfoToggleButton").element_info.name[:100],
                    "menu_still_visible":entry is not None and entry.is_visible(),
                    "view_button_focused":app.el("ViewButton").has_keyboard_focus(),
                    "foreground_owner":h.owner(h.u.GetForegroundWindow()),
                    "app_pid":app.app.pid,
                    "status":app.el("StatusText").window_text()[:200],
                }
                print("R12A_SECOND_TOGGLE_DIAG="+json.dumps(
                    result["second_click_diagnostic"],ensure_ascii=False),flush=True)
                # Determine whether the second flyout refuses ALL physical
                # menu clicks, or only the Details item. Use the already
                # selected Details view; clicking it has no file side effects.
                alternatives={}
                for top in Desktop(backend="uia").windows(process=app.app.pid):
                    for menu in top.descendants(control_type="MenuItem"):
                        if (menu.element_info.process_id==app.app.pid and
                            menu.element_info.automation_id=="ViewDetailsItem"):
                            box=menu.rectangle()
                            alternatives[(box.left,box.top,box.right,box.bottom)]=menu
                if len(alternatives)==1:
                    alternate=next(iter(alternatives.values()))
                    box=alternate.rectangle()
                    point=(box.left+18,(box.top+box.bottom)//2)
                    u=ctypes.windll.user32
                    u.WindowFromPoint.argtypes=[wintypes.POINT]
                    u.WindowFromPoint.restype=wintypes.HWND
                    hit=u.WindowFromPoint(wintypes.POINT(*point))
                    peer=Desktop(backend="uia").from_point(*point)
                    assert hit and h.owner(hit)==app.app.pid, (
                        "Other-menu-item probe must hit the owned application")
                    assert peer.element_info.process_id==app.app.pid
                    assert peer.element_info.automation_id=="ViewDetailsItem", (
                        "Other-menu-item pointer missed its owned target")
                    mouse.click(button="left",coords=point)
                    time.sleep(0.25)
                    result["other_menu_item_pointer_probe"]={
                        "item_id":"ViewDetailsItem",
                        "rect":[box.left,box.top,box.right,box.bottom],
                        "point":list(point),
                        "menu_closed":menu_closed(),
                        "details_still_open":"닫기" in app.el(
                            "FileInfoToggleButton").element_info.name,
                    }
                    print("R12A_OTHER_MENU_POINTER_PROBE="+json.dumps(
                        result["other_menu_item_pointer_probe"],
                        ensure_ascii=False),flush=True)
                else:
                    result["other_menu_item_pointer_probe"]={
                        "found_count":len(alternatives)}
                # Diagnostic only: UIA Invoke must never count as a
                # successful physical click or turn this failure into PASS.
                retry=detail_entry()
                if retry is not None and retry.is_visible() and retry.is_enabled():
                    try:
                        retry.invoke()
                        result["second_uia_invoke_dispatched"]=bool(h.wait(
                            lambda:"열기" in app.el("FileInfoToggleButton").element_info.name,
                            "R12a diagnostic UIA Invoke did not close Details",
                            seconds=3))
                    except Exception as diagnostic_error:
                        # Diagnostic error is not the primary physical failure.
                        result["second_uia_invoke_dispatched"]=False
                        result["second_uia_invoke_error"]=type(
                            diagnostic_error).__name__
                    print("R12A_SECOND_INVOKE_DIAG="+json.dumps(
                        {"uia_invoke_dispatched":
                         result["second_uia_invoke_dispatched"]}),flush=True)
                raise
            result["details_closed_by_physical_click"]=True
            h.wait(menu_closed,"R12a second View menu never closed",seconds=8)
            result["second_menu_dismissed"]=True
            # Read the owned opt-in event trace before the profile is removed.
            # Exactly two commands must follow two actual mouse activations.
            events,trace_error=read_owned_trace()
            if trace_error:
                raise AssertionError(
                    "R12a second-click trace unavailable: "+trace_error)
            opens=[e for e in events if e["phase"]=="flyout_open"]
            dispatch=[e for e in events if e["phase"]=="action23_dispatch"]
            closed=[e for e in events if e["phase"]=="flyout_closed"]
            rescued=[e for e in events if e["phase"]=="details_tap_fallback"]
            stale=[e for e in events if e["phase"]=="action23_stale"]
            result["physical_click_event_counts"]={
                "opens":len(opens),"commands":len(dispatch),
                "closed":len(closed),"rescued_taps":len(rescued),
                "stale_commands":len(stale)}
            print("R12A_PHYSICAL_CLICK_EVENT_COUNTS="+json.dumps(
                result["physical_click_event_counts"]),flush=True)
            assert len(opens)==2 and len(dispatch)==2 and len(closed)==2, (
                "Details command not exactly once per physical menu activation")
            assert len(rescued)<=2 and not stale, (
                "Unexpected duplicate rescue or stale command during two clicks")
            # The closed Details pane removes TextPreviewBody/Status from
            # the UIA tree. Requiring those controls to exist is a harness
            # error, not evidence of an implicit file read. Inspect only
            # elements actually present in this test-owned app window.
            assert "열기" in app.el("FileInfoToggleButton").element_info.name
            preview_body_count=0
            for control in app.win.descendants():
                info=control.element_info
                if info.automation_id not in (
                        "TextPreviewBody","TextPreviewStatus"):
                    continue
                assert info.process_id==app.app.pid
                if info.automation_id=="TextPreviewBody":
                    preview_body_count+=1
                    assert control.window_text().strip()=="", (
                        "Preview text unexpectedly filled when Details closed")
                else:
                    assert "꺼" in control.window_text(), (
                        "Preview opt-in unexpectedly enabled")
            result["closed_pane_preview_controls_exposed"]=preview_body_count
            result["no_implicit_preview_read_after_second_click"]=True
            result["original_unchanged"]=source.read_bytes()==content
        result["app"]=app.report
        assert not result.get("owned_topmost_requested") or result.get("owned_topmost_restored")
        assert result["original_unchanged"]
        assert app.report["normal_exit"] and app.report["original_settings_unchanged"]
        assert app.report["profile_removed"]
        success=True
    finally:
        os.environ.pop("R12_UI_TRACE",None)
        result["owned_source_preserved_on_exit"]=source.read_bytes()==content
        if success:
            assert folder.parent==BASE.resolve() and not folder.is_symlink()
            shutil.rmtree(folder)
            result["fixture_removed"]=True
        (BASE/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),
                                         encoding="utf-8")
        print("R12A_DETAILS_GUI_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
