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
 print("REAL_M23_LOCAL_KOREAN_EXTENSION_TYPE_IN_DETAIL_ROW",True,flush=True)
 print("REAL_M22_ASYNC_NATIVE_METADATA_KOREAN_SIZE_AND_SORT",True,flush=True)
 def select_one(name):
  target=row("Left",name)
  assert target is not None
  focus();target.select()
  eventually(lambda:sum(bool(x.is_selected()) for x in rows("Left"))==1 and
            row("Left",name).is_selected(),
            "UIA select-one retained stale prior multiple selection: "+name,10)
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
