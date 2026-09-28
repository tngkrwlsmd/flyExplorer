"""UXH-04 owned toolbar geometry and discoverability baseline, no source modifications."""
from pathlib import Path
import ctypes as c,os,hashlib,shutil,tempfile,subprocess,time,re,sys
from ctypes import wintypes as w
from PIL import ImageGrab
R=Path(__file__).resolve().parents[1];src=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat","fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
before={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in names}
folder=Path(tempfile.mkdtemp(prefix="uxh04-owned-",dir=R/"logs"))
cp=folder/"conf";cp.mkdir();fixture=folder/"fixture";fixture.mkdir()
for n in names:shutil.copy2(src/n,cp/n)
raw=(cp/"fxfile.conf").read_bytes();enc="utf-16" if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
cfg=raw.decode(enc)
for k,v in (("config.theme_mode","1" if "--light" in sys.argv else "2"),("config.global_hotkey.enable","0"),
 ("config.global_hotkey.show_tray","0"),("config.global_hotkey.windows_startup","0"),
 ("config.register_shell_context_menu","0")):
 cfg,num=re.subn(r"(?m)^(\s*"+re.escape(k)+r"\s*=\s*)[^\r\n]*",lambda m:m.group(1)+v,cfg)
 assert num==1,k
(cp/"fxfile.conf").write_bytes(cfg.encode(enc))
original_saved_band=(cp/"fxfile-coolbar.dat").read_bytes()
if "--fresh" in sys.argv:(cp/"fxfile-coolbar.dat").unlink()
(folder/"appdata").mkdir()
for i in range(3):(fixture/("command-layout-test-%d.txt"%i)).write_text("owned",encoding="utf-8")
owned_bookmarks={}
if "--owned-bookmarks" in sys.argv:
 for i in range(1,13):
  target=fixture/("uxh04-owned-%02d"%i)
  target.mkdir()
  owned_bookmarks["UXH04 Owned %02d"%i]=target
 lines=["[bookmark]"]
 for i,(name,path) in enumerate(owned_bookmarks.items(),1):
  lines += ["bookmark.item%d.name = %s"%(i,name),
            "bookmark.item%d.path = %s"%(i,path)]
 (cp/"fxfile-bookmark.conf").write_text(
     "\n".join(lines)+"\n",encoding="utf-16")
 print("OWNED_SYNTHETIC_BOOKMARK_PATHS",len(owned_bookmarks),flush=True)
u=c.windll.user32
CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
class RECT(c.Structure):_fields_=[(k,c.c_long) for k in ("left","top","right","bottom")]
for name,args in (("EnumWindows",(CALLBACK,w.LPARAM)),("EnumChildWindows",(w.HWND,CALLBACK,w.LPARAM)),
 ("GetWindowThreadProcessId",(w.HWND,c.POINTER(w.DWORD))),("GetWindowRect",(w.HWND,c.POINTER(RECT))),
 ("GetClassNameW",(w.HWND,w.LPWSTR,c.c_int)),("GetWindowTextW",(w.HWND,w.LPWSTR,c.c_int)),
 ("SetWindowPos",(w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT)),
 ("PostMessageW",(w.HWND,w.UINT,w.WPARAM,w.LPARAM)),
 ("SendMessageW",(w.HWND,w.UINT,w.WPARAM,w.LPARAM))):
 getattr(u,name).argtypes=args
u.SendMessageW.restype=c.c_ssize_t
def rect(h):
 a=RECT();u.GetWindowRect(h,c.byref(a));return(a.left,a.top,a.right,a.bottom)
def cl(h):
 a=c.create_unicode_buffer(110);u.GetClassNameW(h,a,len(a));return a.value
def title(h):
 a=c.create_unicode_buffer(210);u.GetWindowTextW(h,a,len(a));return a.value
def en(h,all=False):
 out=[]
 @CALLBACK
 def cb(x,_):
  if all:
   p=w.DWORD();u.GetWindowThreadProcessId(x,c.byref(p))
   if p.value!=h:return True
  out.append(int(x));return True
 if all:u.EnumWindows(cb,0)
 else:u.EnumChildWindows(h,cb,0)
 return out
def wd(r):return r[2]-r[0]
def ht(r):return r[3]-r[1]
proc=None;main=0
try:
 proc=subprocess.Popen([str(R/"bin/x64/fxfile.exe"),"--conf_dir",str(cp),str(fixture)],cwd=folder,
  env={**os.environ,"APPDATA":str(folder/"appdata")},
  stdin=subprocess.DEVNULL,
  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  matches=[h for h in en(proc.pid,True) if title(h).endswith(" - fxfile")]
  if len(matches)==1:main=matches[0];break
  time.sleep(.1)
 assert main
 u.ShowWindow(main,9)
 for outer in (750,1100):
  assert u.SetWindowPos(main,0,65,65,outer,550 if outer==750 else 720,0x0004)
  time.sleep(.9)
  u.PostMessageW(main,0x111,35003,0) if outer==750 else None
  time.sleep(.45)
  toolbar=[];rebars=[]
  for _ in range(65):
   ch=[(cl(h),rect(h),h) for h in en(main) if u.IsWindowVisible(h)]
   toolbar=[(k,r,h) for k,r,h in ch
            if k in ("ToolbarWindow32","ReBarWindow32","CoolBar")]
   rebars=[(k,r,h) for k,r,h in ch
           if "ReBar" in k or "Rebar" in k]
   if rebars and len(toolbar)>=5:break
   time.sleep(.13)
  assert rebars and len(toolbar)>=5,("owned native coolbar startup did not settle",
                                   title(main),toolbar)
  lists=[(k,r,h) for k,r,h in ch if k=="SysListView32"]
  print("SCENARIO",("FRESH" if "--fresh" in sys.argv else "SAVED"),outer,
        "MAIN",rect(main),"TOOLBARS",[(k,r) for k,r,_ in toolbar],
        "REBARS",[(k,r) for k,r,_ in rebars],
        "LISTS",[(r[1],r[3]) for _,r,_ in lists],flush=True)
  for _,r,h in rebars:
   num=int(u.SendMessageW(h,0x40C,0,0))
   print("REBAR_BAND_COUNT",num,"RECT",r,"HEIGHT",ht(r),flush=True)
  if outer==750 or (outer==1100 and ("--diagnose" in sys.argv or "--wide" in sys.argv)):
   from pywinauto import Desktop
   visible=[]
   for control in Desktop(backend="uia").window(handle=main).descendants():
    try:
     if control.is_visible() and control.element_info.control_type in ("Button","MenuItem","SplitButton"):
      b=control.rectangle();visible.append((control.element_info.control_type,
           control.element_info.name.encode("ascii","backslashreplace").decode()[:60],
           (b.left,b.top,b.right,b.bottom)))
    except Exception:pass
   print("UIA_VISIBLE_COMMANDS",len(visible),"SAMPLES",visible[:24],flush=True)
   if "--exercise" in sys.argv or "--persist" in sys.argv or "--diagnose" in sys.argv:
    assert "--fresh" not in sys.argv,"only a saved layout is eligible"
    from pywinauto import mouse,keyboard
    def visible_popups():
     return [h for h in en(proc.pid,True)
             if cl(h)=="#32768" and u.IsWindowVisible(h)]
    def print_menu(hwnd,tag):
     try:
      items=[x for x in Desktop(backend="uia").window(handle=hwnd).descendants()
             if x.element_info.control_type=="MenuItem"]
      names=[(x.element_info.name.encode("ascii","backslashreplace").decode()[:78],
              str(x.rectangle())) for x in items]
      print("REAL_MENU",tag,names[:21],flush=True)
      return items
     except Exception as ex:
      print("REAL_MENU_UNAVAILABLE",tag,str(ex)[:100],flush=True)
      return []
    def click_compact_menu():
     # Actual owned title-bar click ensures Alt+V cannot affect other apps.
     mr=rect(main);mouse.click(coords=(mr[0]+170,mr[1]+14))
     assert u.GetForegroundWindow()==main, "refusing global keys on other app"
     keyboard.send_keys("%v",pause=.03)
     time.sleep(.4)
     before_popups=visible_popups()
     print("VIEW_MENU_POPUPS",[(h,rect(h)) for h in before_popups],flush=True)
     if not before_popups:
      raise AssertionError("Alt+V did not physically open View menu")
     items=print_menu(before_popups[-1],"view")
     first=next((x for x in items if x.is_visible()),None)
     assert first,"View menu exposed no items to UI automation"
     ri=first.rectangle()
     mouse.move(coords=((ri.left+min(65,ri.right-ri.left-7)),(ri.top+ri.bottom)//2))
     time.sleep(.45)
     opened=[h for h in visible_popups() if h not in before_popups]
     if not opened:
      # Normal native arrow-key entry into the first View submenu.
      keyboard.send_keys("{HOME}{RIGHT}")
      time.sleep(.4)
      opened=[h for h in visible_popups() if h not in before_popups]
     assert opened,"Tools submenu could not be opened using pointer or keyboard"
     options=print_menu(opened[-1],"tools")
     # This legacy owner-drawn MFC menu exposes empty UIA item names.
     # Identify the exact native command ID, then click its real screen
     # menu-item rectangle. NEVER guess a menu row index or post WM_COMMAND.
     u.GetMenuItemCount.argtypes=(w.HMENU,)
     u.GetMenuItemCount.restype=c.c_int
     u.GetMenuItemID.argtypes=(w.HMENU,c.c_int)
     u.GetMenuItemID.restype=w.UINT
     u.GetMenuItemRect.argtypes=(w.HWND,w.HMENU,w.UINT,c.POINTER(RECT))
     u.GetMenuItemRect.restype=w.BOOL
     hmenu=int(u.SendMessageW(opened[-1],0x01E1,0,0))
     n=u.GetMenuItemCount(hmenu) if hmenu else -1
     found=[i for i in range(n) if u.GetMenuItemID(hmenu,i)==33049]
     print("NATIVE_COMPACT_MENU_COMMAND_POS",found,"TOTAL",n,flush=True)
     assert len(found)==1,("real native command ID 33049 missing",n,found)
     bound=RECT()
     assert u.GetMenuItemRect(main,hmenu,found[0],c.byref(bound))
     assert bound.right>bound.left and bound.bottom>bound.top
     print("NATIVE_COMPACT_MENU_ITEM_RECT",
           (bound.left,bound.top,bound.right,bound.bottom),flush=True)
     u.GetMenuState.argtypes=(w.HMENU,w.UINT,w.UINT)
     u.GetMenuState.restype=w.UINT
     native_state=int(u.GetMenuState(hmenu,33049,0))
     print("NATIVE_COMPACT_COMMAND_STATE",hex(native_state),
           "IS_DISABLED",bool(native_state&3),flush=True)
     # No RB_GETBANDINFO from the external tester: pointer-bearing
     # WM_USER control messages are NOT marshalled between processes.
     # Cross-process band geometry is assessed by visible HWNDs only.
     print("NATIVE_REBAR_SCREEN_RECT",rect(rebars[0][2]),flush=True)
     if "--diagnose" in sys.argv:
      keyboard.send_keys("{ESC}{ESC}",pause=.05)
      return
     mouse.click(coords=(bound.left+min(110,(bound.right-bound.left)//2),
                         (bound.top+bound.bottom)//2))
     time.sleep(.65)
    def keyboard_compact_menu():
     mr=rect(main);mouse.click(coords=(mr[0]+170,mr[1]+14))
     assert u.GetForegroundWindow()==main, "owned keyboard focus required"
     keyboard.send_keys("%v",pause=.04)
     time.sleep(.23)
     first=visible_popups()
     assert first,"Alt+V did not open native View menu"
     keyboard.send_keys("{HOME}{RIGHT}",pause=.045)
     time.sleep(.23)
     second=[h for h in visible_popups() if h not in first]
     assert second,"View Tools submenu not keyboard reachable"
     sub=second[-1]
     mh=int(u.SendMessageW(sub,0x01E1,0,0))
     u.GetMenuItemCount.argtypes=(w.HMENU,)
     u.GetMenuItemCount.restype=c.c_int
     u.GetMenuItemID.argtypes=(w.HMENU,c.c_int)
     u.GetMenuItemID.restype=w.UINT
     u.GetMenuStringW.argtypes=(w.HMENU,w.UINT,w.LPWSTR,c.c_int,w.UINT)
     u.GetMenuStringW.restype=c.c_int
     positions=[i for i in range(u.GetMenuItemCount(mh))
                if u.GetMenuItemID(mh,i)==33049]
     assert len(positions)==1,"Compact command missing for keyboard"
     label=c.create_unicode_buffer(200)
     u.GetMenuStringW(mh,positions[0],label,199,0x400)
     print("REAL_KEYBOARD_NATIVE_MENU_LABEL",
           label.value.encode("ascii","backslashreplace").decode(),
           flush=True)
     # BCMenu draws this legacy menu itself and returns an empty native
     # GetMenuStringW even for valid mnemonic-capable entries. The actual
     # keyboard action and rebar-height change are the acceptance gate.
     if label.value:
      assert "&J" in label.value.upper(),label.value
     else:
      print("OWNERDRAW_NATIVE_MENU_TEXT_EMPTY=TEST_ACTUAL_J_KEY",flush=True)
     # Owner-drawn text is unavailable through GetMenuStringW.
     # Check the exact live native command ID and enabled state,
     # then use ONLY its declared physical J menu mnemonic.
     u.GetMenuState.argtypes=(w.HMENU,w.UINT,w.UINT)
     u.GetMenuState.restype=w.UINT
     state=int(u.GetMenuState(mh,33049,0))
     assert not state&3,("refuse disabled native command",hex(state))
     keyboard.send_keys("j",pause=.095)
     time.sleep(.55)
     print("REAL_PHYSICAL_KEYBOARD_J_MENU_COMMAND_EXECUTED=True",flush=True)
    def assert_overflow():
     # Only use pointer-free cross-process Win32 reads. The bookmark
     # toolbar's right-end rebar chevron is visibly present in actual
     # compact owned screenshots; click it and inspect its native menu.
     bars=[rect(h) for h in en(main)
          if cl(h)=="ToolbarWindow32" and u.IsWindowVisible(h)]
     rb=rect(rebar_hwnd)
     last_row=max(q[1] for q in bars)
     print("COMPACT_NATIVE_TOOLBARS",bars,"REBAR",rb,flush=True)
     clicked=False
     for yy in (last_row+7,last_row+18):
      mouse.click(coords=(rb[2]-8,yy))
      time.sleep(.34)
      pops=visible_popups()
      # The inherited MFC Chevron popup is a separate Afx HWND, NOT a
      # Win32 #32768 menu. Keep the actual on-screen popup as the gate.
      custom=[h for h in en(proc.pid,True)
              if u.IsWindowVisible(h) and cl(h).startswith("Afx:")
              and rect(h)[0]>=rb[2]-26 and rect(h)[1]>=last_row
              and 45<=wd(rect(h))<=480 and 38<=ht(rect(h))<=400]
      if custom:
       q=rect(custom[0])
       descendant=[(cl(h),rect(h)) for h in en(custom[0])
                   if u.IsWindowVisible(h)]
       print("REAL_MFC_CHEVRON_POPUP",q,
             "CHILDREN",descendant[:9],flush=True)
       try:
        from pywinauto import Desktop
        uiac=[(x.element_info.control_type,
               x.element_info.name.encode("ascii","backslashreplace").decode()[:55])
              for x in Desktop(backend="uia").window(
               handle=custom[0]).descendants() if x.is_visible()]
        print("REAL_CHEVRON_POPUP_UIA",uiac[:12],flush=True)
       except Exception as exc:
        print("CHEVRON_UIA_UNAVAILABLE",repr(exc)[:90],flush=True)
       ImageGrab.grab(bbox=q,include_layered_windows=True).save(
         folder/"actual-chevron-popup.png")
       if "--owned-bookmarks" in sys.argv:
        checkboxes=[x for x in Desktop(backend="uia").window(
          handle=custom[0]).descendants()
          if x.is_visible() and x.element_info.name in owned_bookmarks]
        print("ACTUAL_OWNED_BOOKMARK_OVERFLOW_ITEMS",
              [x.element_info.name for x in checkboxes],flush=True)
        assert checkboxes,"no synthetic bookmark in native overflow"
        target_item=checkboxes[0]
        target_path=owned_bookmarks[target_item.element_info.name]
        target_item.click_input()
        switched=False
        for _ in range(55):
         if target_path.name.lower() in title(main).lower():
          switched=True;break
         time.sleep(.1)
        assert switched,("synthetic bookmark did not navigate",
              str(target_path),title(main))
        print("OWNED_REAL_BOOKMARK_OVERFLOW_NAVIGATION_PASS=True",
              target_path.name,flush=True)
       else:
        keyboard.send_keys("{ESC}")
        time.sleep(.17)
       clicked=True
       break
      if not pops:
       visibles=[(cl(h),title(h)[:36],rect(h)) for h in en(proc.pid,True)
                 if u.IsWindowVisible(h) and h!=main]
       print("NO_MENU_AFTER_CHEVRON_CLICK",yy,
             "OWNED_VISIBLE_WINDOWS",visibles[:9],flush=True)
       ImageGrab.grab(bbox=rect(main),
           include_layered_windows=True).save(
           folder/("chevron-attempt-%d.png"%yy))
      if pops:
       native=int(u.SendMessageW(pops[-1],0x01E1,0,0))
       n=u.GetMenuItemCount(native) if native else 0
       print("REAL_BOOKMARK_OVERFLOW_MENU_ENTRIES",n,flush=True)
       keyboard.send_keys("{ESC}")
       time.sleep(.13)
       if n>0:
        clicked=True;break
     assert clicked,"real owned bookmark chevron popup not observed"
     print("UXH04_REAL_NATIVE_BOOKMARK_CHEVRON_PASS=True",flush=True)
    # The native rebar HWND remains the same while its screen rect changes.
    rebar_hwnd=rebars[0][2]
    rebar_height=lambda:ht(rect(rebar_hwnd))
    assert rebar_height()==141,("saved layout baseline changed",rebar_height())
    if "--command-audit" in sys.argv:
     from pywinauto import mouse
     main_bars=[h for k,bb,h in toolbar
        if k=="ToolbarWindow32" and bb[1]==rebars[0][1][1]+21]
     assert len(main_bars)==1,("main native toolbar ambiguous",main_bars)
     actual_mainbar=main_bars[0]
     u.SendMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
     u.SendMessageW.restype=c.c_ssize_t
     def actual_main_buttons():
      children=Desktop(backend="uia").window(
         handle=actual_mainbar).descendants()
      return [x for x in children
          if x.is_visible() and x.element_info.name and
          x.element_info.control_type in ("Button","SplitButton")]
     original_buttons=actual_main_buttons()
     orig_names=sorted(x.element_info.name for x in original_buttons)
     original_count=int(u.SendMessageW(actual_mainbar,0x418,0,0))
     print("REAL_MAIN_TOOLBAR_BEFORE",
           original_count,
           [n.encode("ascii","backslashreplace").decode() for n in orig_names],
           flush=True)
     assert original_count>=8 and len(orig_names)>=4
     def actual_tooltip(button):
      bounds=button.rectangle()
      mouse.move(coords=((bounds.left+bounds.right)//2,
                         (bounds.top+bounds.bottom)//2))
      for _ in range(16):
       hints=[h for h in en(proc.pid,True)
          if cl(h).lower()=="tooltips_class32" and u.IsWindowVisible(h)]
       if hints:
        names=[]
        for h in hints:
         try:
          names.append(Desktop(backend="uia").window(
                     handle=h).element_info.name)
         except Exception:names.append(title(h))
        print("ACTUAL_HOVER_TOOLTIP_WINDOWS",len(hints),
              [x.encode("ascii","backslashreplace").decode()
               for x in names],flush=True)
        return names
       time.sleep(.12)
      print("ACTUAL_HOVER_TOOLTIP_NOT_EXPOSED",flush=True)
      return None
     first_button=next((x for x in original_buttons if x.is_enabled()),
                       original_buttons[0])
     tip_before=actual_tooltip(first_button)
    if "--keyboard" in sys.argv:
     keyboard_compact_menu()
    else:
     click_compact_menu()
    if "--diagnose" in sys.argv:
     print("NATIVE_COMMAND_DIAGNOSIS_DONE",outer,flush=True)
     continue
    print("REAL_COMPACTED_REBAR_HEIGHT",rebar_height(),flush=True)
    assert rebar_height()==101,("user-click compact mode did not free row",rebar_height())
    if "--command-audit" in sys.argv:
     compressed_buttons=actual_main_buttons()
     compressed_names=sorted(x.element_info.name
                             for x in compressed_buttons)
     compressed_count=int(u.SendMessageW(actual_mainbar,0x418,0,0))
     print("REAL_MAIN_TOOLBAR_AFTER",
           compressed_count,
           [n.encode("ascii","backslashreplace").decode()
            for n in compressed_names],flush=True)
     assert compressed_count==original_count and compressed_names==orig_names,(
        "main native toolbar commands lost or renamed after compaction",
        original_count,compressed_count,orig_names,compressed_names)
     same_button=next((x for x in compressed_buttons
                       if x.element_info.name==first_button.element_info.name),
                      compressed_buttons[0])
     tip_after=actual_tooltip(same_button)
     assert bool(tip_before)==bool(tip_after),(
        "existing native toolbar tooltip availability changed",
        tip_before,tip_after)
     if tip_before and tip_after:
      assert tip_before==tip_after,"native tooltip contents changed"
     print("UXH04_NATIVE_MAIN_COMMANDS_AND_BASELINE_TOOLTIP_UNCHANGED_PASS=True",
           "NATIVE_TOOLTIP_EXPOSED",bool(tip_after),flush=True)
    if "--chevron" in sys.argv:
     assert_overflow()
    if "--exercise" in sys.argv:
     if "--keyboard" in sys.argv:
      keyboard_compact_menu()
     else:
      click_compact_menu()
     print("REAL_RESTORED_REBAR_HEIGHT",rebar_height(),flush=True)
     assert rebar_height()==141,("second user click failed to restore",rebar_height())
     print("UXH04_ACTUAL_"+("KEYBOARD" if "--keyboard" in sys.argv else "POINTER")+"_MENU_TOGGLE_AND_RESTORE_PASS=True",flush=True)
    else:
     print("UXH04_ACTUAL_POINTER_COMPACT_LEFT_ACTIVE_UNTIL_EXIT=True",flush=True)

  ImageGrab.grab(bbox=rect(main),include_layered_windows=True).save(folder/(str(outer)+".png"))
 print("BASELINE_EVIDENCE_FOLDER",folder,flush=True)
finally:
 if proc and proc.poll() is None:
  if main and u.IsWindow(main):u.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=14)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=4)
 if ("--relaunch" in sys.argv and "--persist" in sys.argv and
     "--keyboard" in sys.argv and proc and proc.returncode==0):
  reproc=None;rem=0
  try:
   reproc=subprocess.Popen(
    [str(R/"bin/x64/fxfile.exe"),"--conf_dir",str(cp),str(fixture)],
    cwd=folder,env={**os.environ,"APPDATA":str(folder/"appdata")},
    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL)
   for _ in range(100):
    wins=[h for h in en(reproc.pid,True) if title(h).endswith(" - fxfile")]
    if len(wins)==1:rem=wins[0];break
    time.sleep(.1)
   assert rem,"owned relaunch main frame absent"
   u.ShowWindow(rem,9)
   assert u.SetWindowPos(rem,0,65,65,750,550,0x0004)
   restored=None
   for _ in range(60):
    bars=[h for h in en(rem) if cl(h)=="ReBarWindow32"
          and u.IsWindowVisible(h)]
    if len(bars)==1:
     restored=ht(rect(bars[0]))
     if restored==141:break
    time.sleep(.12)
   assert restored==141,("relaunch did not restore saved rows",restored)
   assert (cp/"fxfile-coolbar.dat").read_bytes()==original_saved_band
   print("UXH04_ACTUAL_KEYBOARD_COMPACT_RELAUNCH_GUI_RESTORED_141_PASS=True",
         flush=True)
  finally:
   if reproc and reproc.poll() is None:
    if rem and u.IsWindow(rem):u.PostMessageW(rem,0x10,0,0)
    try:reproc.wait(timeout=14)
    except subprocess.TimeoutExpired:reproc.terminate();reproc.wait(timeout=5)
   assert reproc and reproc.returncode==0,(
     "owned relaunch clean exit failed",
     reproc.returncode if reproc else None)
 after={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in names}
 copy_saved=(cp/"fxfile-coolbar.dat").read_bytes()
 if "--exercise" in sys.argv or "--persist" in sys.argv or "--diagnose" in sys.argv:
  print("OWNED_COOLBAR_PERSISTED_LAYOUT_IDENTICAL_TO_ORIGINAL",
        copy_saved==original_saved_band,flush=True)
  assert copy_saved==original_saved_band,(
      "temporary compact mode must not persist or erase custom band layout")
 print("ORIGINAL_SETTINGS_IDENTICAL",after==before,"OWNED_EXIT",proc.returncode if proc else None,flush=True)
 assert after==before and proc is not None and proc.returncode==0
