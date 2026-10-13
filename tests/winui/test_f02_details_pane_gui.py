"""F02 focused, owned GUI acceptance for the read-only selected-item pane."""
def run(*,win,element,safe_click,eventually,left,right):
    button=element("FileInfoToggleButton")
    panel=element("FileInfoPane")
    assert button.exists(timeout=4)
    assert not panel.is_visible(),"F02 must be opt-in"
    safe_click(button)
    eventually(lambda:panel.is_visible(),"F02 detail pane did not open",7)
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
    assert element("FileInfoSize").window_text()
    assert element("FileInfoModified").window_text()
    print("F02_LEFT_READONLY_FILE_INFORMATION=PASS",flush=True)

    right_row=eventually(lambda:row(1,"Secondary"),
                         "F02 owned right folder row unavailable",9)
    safe_click(right_row)
    eventually(lambda:element("FileInfoName").window_text()=="Secondary",
               "F02 right selection did not replace stale left metadata",9)
    assert element("FileInfoHint").window_text()=="오른쪽 창 선택 항목"
    assert element("FileInfoLocation").window_text().lower()==str(right).lower()
    assert element("FileInfoSize").window_text()=="폴더"
    print("F02_ACTIVE_PANE_SELECTION_ISOLATION=PASS",flush=True)

    safe_click(button)
    eventually(lambda:not panel.is_visible(),"F02 details did not collapse",7)
    safe_click(button)
    eventually(lambda:panel.is_visible() and
               element("FileInfoName").window_text()=="Secondary",
               "F02 reopened panel retained wrong selection",7)
    print("F02_TOGGLE_AND_REOPEN=PASS",flush=True)
