"""F02 focused, owned GUI acceptance for the read-only selected-item pane."""
def run(*,win,element,safe_click,eventually,left,right):
    button=element("FileInfoToggleButton")
    hint=element("FileInfoHint")
    assert button.exists(timeout=4)
    assert not hint.exists(timeout=.3),"F02 details must be opt-in"
    safe_click(button)
    eventually(lambda:hint.exists(timeout=.3) and "닫기" in button.window_text(),
               "F02 details text did not enter accessibility tree",7)
    assert element("FileInfoHint").window_text()=="항목 하나를 선택하세요."

    def row(side,name):
        view=element("LeftFiles" if side==0 else "RightFiles")
        return next((x for x in view.descendants()
                     if x.element_info.control_type=="ListItem"
                     and name in x.window_text()),None)

    left_row=eventually(lambda:row(0,"readme.txt"),
                        "F02 owned file row not displayed",9)
    safe_click(left_row)
    eventually(lambda:element("FileInfoName").window_text()=="readme.txt",
               "F02 left file metadata did not track selection",9)
    assert element("FileInfoLocation").window_text().lower()==str(left).lower()
    assert element("FileInfoHint").window_text()=="왼쪽 창 선택 항목"
    # Size/date can be below the in-layout ScrollViewer viewport on
    # smaller windows. Reveal them using the owned file-info region.
    from pywinauto import mouse
    location=element("FileInfoLocation")
    rect=location.rectangle()
    mouse.scroll(wheel_dist=-5,coords=(rect.mid_point().x,rect.mid_point().y))
    eventually(lambda:element("FileInfoSize").window_text() and
               element("FileInfoModified").window_text(),
               "F02 size/date not exposed after details scroll",12)
    mouse.scroll(wheel_dist=5,coords=(rect.mid_point().x,rect.mid_point().y))
    print("F02_LEFT_READONLY_FILE_INFORMATION=PASS",flush=True)

    right_row=eventually(lambda:row(1,"Secondary"),
                         "F02 owned right folder row unavailable",9)
    safe_click(right_row)
    eventually(lambda:element("FileInfoName").window_text()=="Secondary",
               "F02 right selection did not replace stale left metadata",9)
    assert element("FileInfoHint").window_text()=="오른쪽 창 선택 항목"
    assert element("FileInfoLocation").window_text().lower()==str(right).lower()
    location=element("FileInfoLocation")
    rect=location.rectangle()
    mouse.scroll(wheel_dist=-5,coords=(rect.mid_point().x,rect.mid_point().y))
    eventually(lambda:element("FileInfoSize").window_text()=="폴더",
               "F02 right folder size absent after details scroll",12)
    mouse.scroll(wheel_dist=5,coords=(rect.mid_point().x,rect.mid_point().y))
    print("F02_ACTIVE_PANE_SELECTION_ISOLATION=PASS",flush=True)

    safe_click(button)
    eventually(lambda:not hint.exists(timeout=.3) and "열기" in button.window_text(),
               "F02 details did not collapse",7)
    safe_click(button)
    eventually(lambda:hint.exists(timeout=.3) and
               element("FileInfoName").window_text()=="Secondary",
               "F02 reopened panel retained wrong selection",7)
    print("F02_TOGGLE_AND_REOPEN=PASS",flush=True)
