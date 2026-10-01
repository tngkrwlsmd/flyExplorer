"""v7 real WinUI functional top-level window-tab acceptance."""
from pywinauto.keyboard import send_keys

def run(*,win,element,safe_click,focus,eventually,owned):
    strip=element("WindowTabStrip").wrapper_object()
    def tabs():
        return [x for x in strip.descendants() if x.element_info.control_type=="TabItem"]
    def address(): return element("AddressBox").get_value().lower()
    eventually(lambda:len(tabs())==1,"v7 initial window tab missing",8)
    left=element("LeftFiles")
    def nested_rows():
        return [x for x in left.descendants()
                if x.element_info.control_type=="ListItem" and "Nested" in x.window_text()]
    eventually(lambda:len(nested_rows())==1,"owned Nested row missing",8)
    # Metadata/watcher completion can replace ListViewItem containers. Resolve
    # the exact row immediately before the physical double-click.
    nested_rows()[0].double_click_input()
    eventually(lambda:"nested" in address(),"v7 tab A did not navigate to Nested",14)
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
    tabs()[0].click_input()
    eventually(lambda:"nested" in address(),"A->B->A lost tab A path",14)
    eventually(lambda:"단일 창" in element("SplitButton").window_text(),
               "A->B->A lost tab A split state",8)
    # Click B, then exercise keyboard rotation using the distinct addresses.
    tabs()[1].click_input()
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
    send_keys("^w");eventually(lambda:len(tabs())==1,"cleanup close after + button failed",10)
    print("REAL_V7_FUNCTIONAL_WINDOW_TABS_STATE_ISOLATION",True,flush=True)
    print("REAL_V7_WINDOW_TAB_KEYBOARD_AND_ADD_BUTTON",True,flush=True)
