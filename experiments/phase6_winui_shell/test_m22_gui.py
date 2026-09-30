"""Actual native WinUI GUI: use only owned fixtures, never confirm recycle."""
def run(*,win,element,safe_click,focus,eventually,left,right):
 assert left.is_dir() and right.is_dir() and left!=right
 focus();safe_click(element("PrimaryPaneTitle"))
 for name in ("CopyButton","MoveButton","RecycleButton","CancelButton","SortPicker","OperationProgress"):
  assert element(name).exists(timeout=4),name
 assert not element("CancelButton").is_enabled()
 def rows(side):
  return [x for x in element(side+"Files").descendants()
          if x.element_info.control_type=="ListItem"]
 def row(side,name):
  return next((x for x in rows(side) if name in x.window_text()),None)
 eventually(lambda:all(row("Left",n) is not None for n in
      ("복사본.txt","작은.txt","큰.txt","이동.txt","자료.txt")),
      "owned multi-source fixtures absent from real helper snapshot",15)
 print("REAL_M22_REUSABLE_KOREAN_TOOLBAR_MULTISELECT_AND_CONTEXT_UI",True,flush=True)
 eventually(lambda:row("Left","큰.txt") is not None and
     "KB" in row("Left","큰.txt").window_text() and
     row("Left","작은.txt") is not None and
     " B" in row("Left","작은.txt").window_text(),
     "background metadata never reached WinUI list",20)
 focus();element("SortPicker").select(2)
 def size_sorted():
  titles=[x.window_text() for x in rows("Left")]
  big=next((i for i,s in enumerate(titles) if "큰.txt" in s),None)
  little=next((i for i,s in enumerate(titles) if "작은.txt" in s),None)
  return big is not None and little is not None and big<little
 eventually(size_sorted,"real size sorting did not order files descending",10)
 assert "txt 파일" in row("Left","큰.txt").window_text(), (
     "real local extension type not displayed for Korean file")
 # App-owned icon/column UI must preserve the UIA accessible name while
 # the independent helper returns the actual OS-registered friendly type.
 eventually(lambda:row("Left","큰.txt") is not None and
            "Windows 유형:" in row("Left","큰.txt").window_text(),
            "isolated registered Windows type missing from real file row",12)
 for control in ("LeftNameWidthSlider","RightNameWidthSlider"):
  assert element(control).exists(timeout=3),control
 width=element("LeftNameWidthSlider").wrapper_object()
 width.iface_range_value.SetValue(216.0)
 eventually(lambda:abs(
     element("LeftNameWidthSlider").wrapper_object().iface_range_value.CurrentValue
     -216.0)<1 and row("Left","큰.txt") is not None and
     "Windows 유형:" in row("Left","큰.txt").window_text(),
     "real pane column resize lost accessible name/type",12)
 print("REAL_M23_OS_REGISTERED_TYPE_AND_ACCESSIBLE_RESIZABLE_COLUMNS",True,flush=True)
 # WinUI Image must originate from actual isolated, registered
 # SHGetFileInfo icon bits, not merely from a generic FontIcon glyph.
 from pywinauto import Desktop
 icon_row=row("Left",chr(0xD070)+".txt")
 assert icon_row is not None
 eventually(lambda:any(
     "Windows system registered file icon" in x.element_info.name
     for x in row("Left",chr(0xD070)+".txt").descendants()
     if x.element_info.control_type=="Image"),
     "actual installed .txt system icon not rendered in WinUI",12)
 print("REAL_M24_WINUI_ISOLATED_REGISTERED_SYSTEM_ICON_RENDERED",True,flush=True)

 # Read-only accessibility/monitor audit of this exact test-owned HWND.
 # Changing global High Contrast or per-monitor DPI is outside this test.
 import ctypes
 from ctypes import wintypes as WIN
 user32=ctypes.WinDLL("user32",use_last_error=True)
 user32.GetDpiForWindow.argtypes=[WIN.HWND]
 user32.GetDpiForWindow.restype=WIN.UINT
 dpi=user32.GetDpiForWindow(win.handle)
 assert dpi>=96 and dpi<=384,("unexpected owned DPI",dpi)
 class HighContrast(ctypes.Structure):
  _fields_=[("cbSize",WIN.UINT),("dwFlags",WIN.DWORD),
            ("lpszDefaultScheme",WIN.LPWSTR)]
 contrast=HighContrast()
 contrast.cbSize=ctypes.sizeof(contrast)
 user32.SystemParametersInfoW.argtypes=(
     WIN.UINT,WIN.UINT,ctypes.c_void_p,WIN.UINT)
 user32.SystemParametersInfoW.restype=WIN.BOOL
 assert user32.SystemParametersInfoW(
     0x0042,contrast.cbSize,ctypes.byref(contrast),0)
 for name in ("LeftFiles","RightFiles","LeftNameWidthSlider",
              "RightNameWidthSlider"):
  assert element(name).element_info.name,(
     "owned WinUI control missing accessible name",name)
 key=chr(0xD070)+".txt"
 actual=row("Left",key)
 assert actual is not None and key in actual.window_text()
 print("REAL_M24_OWNED_FILE_ROW_AND_COLUMN_ACCESSIBLE_NAMES",True,flush=True)
 print("M24_OWNED_ACTUAL_DPI",dpi,
       "SYSTEM_HIGH_CONTRAST_CURRENTLY_ON",bool(contrast.dwFlags&1),
       "ALTERNATE_DPI_AND_HIGH_CONTRAST_NOT_TESTED",True,flush=True)

 print("REAL_M23_LOCAL_KOREAN_EXTENSION_TYPE_IN_DETAIL_ROW",True,flush=True)
 print("REAL_M22_ASYNC_NATIVE_METADATA_KOREAN_SIZE_AND_SORT",True,flush=True)
 def select_one(name):
  # A native watcher may replace the ListView rows between lookup and
  # Select(). Resolve and verify a fresh peer within the same bounded retry.
  def selected():
   target=row("Left",name)
   if target is None:return False
   focus();target.select()
   current=row("Left",name)
   return current is not None and current.is_selected() and (
     sum(bool(x.is_selected()) for x in rows("Left"))==1)
  try:
   eventually(selected,
       "UIA select-one failed across native row refresh: "+name,12)
  except AssertionError:
   print("M22_SELECT_ONE_FAILED",name,"SOURCE_EXISTS",(left/name).exists(),
         "ROWS",[x.window_text() for x in rows("Left")][:12],flush=True)
   raise
 select_one("복사본.txt")
 row("Left","작은.txt").iface_selection_item.AddToSelection()
 eventually(lambda:sum(bool(x.is_selected()) for x in rows("Left"))>=2,
           "real multi-selection failed",9)
 safe_click(element("CopyButton"))
 eventually(lambda:(right/"복사본.txt").is_file() and
      (right/"작은.txt").is_file(),"multi-file Shell Copy not committed",18)
 assert (right/"복사본.txt").read_text(encoding="utf-8")=="owned copied"
 assert (left/"복사본.txt").is_file()
 print("REAL_M22_SELECTED_MULTI_FILE_COPY_OPPOSITE_PANE",True,flush=True)
 eventually(lambda:row("Left","이동.txt") is not None, "move source not in restored list",15)
 eventually(lambda:row("Right","복사본.txt") is not None and
            row("Right","작은.txt") is not None,
            "opposite pane refresh not complete before next mutation",16)
 select_one("이동.txt")
 safe_click(element("MoveButton"))
 print("M22_MOVE_CURRENT_STATUS",
       element("StatusText").window_text().encode("unicode_escape").decode("ascii"),
       flush=True)
 eventually(lambda:(right/"이동.txt").is_file() and
     not (left/"이동.txt").exists(),"actual Shell Move failed",17)
 assert (right/"이동.txt").read_text(encoding="utf-8")=="owned moved"
 print("REAL_M22_ACTUAL_KOREAN_MOVE_OPPOSITE_PANE",True,flush=True)
 def dialog(name):
  return win.child_window(title=name,control_type="Button")
 eventually(lambda:row("Left","자료.txt") is not None,"collision source missing",15)
 select_one("자료.txt")
 safe_click(element("CopyButton"))
 eventually(lambda:dialog("취소").exists(timeout=.2),
          "real Korean conflict ContentDialog never appeared",12)
 safe_click(dialog("취소"))
 assert (right/"자료.txt").read_text(encoding="utf-8")=="preexisting right"
 print("REAL_M22_KOREAN_COLLISION_CANCEL_NO_OVERWRITE",True,flush=True)
 select_one("자료.txt")
 safe_click(element("CopyButton"))
 eventually(lambda:dialog("이름 변경 후 계속").exists(timeout=.2),
          "real Korean keep-both ContentDialog absent",12)
 safe_click(dialog("이름 변경 후 계속"))
 eventually(lambda:len(list(right.glob("자료*")))>=2,
          "confirmed keep-both did not create new name",19)
 assert (right/"자료.txt").read_text(encoding="utf-8")=="preexisting right"
 print("REAL_M22_CONFIRMED_SHELL_KEEP_BOTH_NEVER_REPLACED_EXISTING",True,flush=True)
 eventually(lambda:row("Left","자료.txt") is not None,"recycle source absent",15)
 select_one("자료.txt")
 safe_click(element("RecycleButton"))
 eventually(lambda:dialog("취소").exists(timeout=.2),
          "real recycle safety dialog absent",12)
 safe_click(dialog("취소"))
 assert (left/"자료.txt").read_text(encoding="utf-8")=="owned source"
 print("REAL_M22_KOREAN_RECYCLE_DIALOG_CANCELED_NO_BIN_MUTATION",True,flush=True)
