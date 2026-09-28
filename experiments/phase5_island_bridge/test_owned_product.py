"""Only run against a separately built test-owned flyExplorer on a private profile.
The opt-in DLL is loaded INSIDE the real product's existing MFC UI process.
"""
from pathlib import Path
import ctypes as C,hashlib,os,re,shutil,subprocess,tempfile,time
from ctypes import wintypes as W
from pywinauto import Desktop,mouse,keyboard
from stage_test_host import stage_test_host

folder=Path(__file__).resolve().parent
repo=folder.parents[1]
product=repo/'bin/x64/fxfile.exe'
build_mode=os.environ.get('FLYEXP_PHASE5_BUILD_CONFIG','Debug')
assert build_mode in ('Debug','Release'),"invalid isolated WinUI build configuration"
dll=folder/'x64'/build_mode/'FlyExplorerIslandBridge'/'FlyExplorerIslandBridge.dll'
source=Path(os.environ['APPDATA'])/'fxfile'/'conf'
names=('fxfile.conf','fxfile-main.conf','fxfile-toolbar.dat',
       'fxfile-coolbar.dat','fxfile-dlg_state.conf','fxfile-folder_layout.conf')
# Optional crash-isolation modes; never enable in ordinary product tests.
textbox_mode=os.environ.get('FLYEXP_PHASE5_DIAG_TEXTBOX','')
extra_ui=os.environ.get('FLYEXP_PHASE5_EXTRA_UI_GATES','')=='1'
assert textbox_mode in ('','plain','resources','app'),'invalid TextBox diagnostic mode'
assert product.is_file() and dll.is_file(),'build both isolated products before running'
assert source.is_dir() and all((source/f).is_file() for f in names),'read-only profile prerequisite'
original={f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in names}
out=folder/'out'
out.mkdir(exist_ok=True)
work=Path(tempfile.mkdtemp(prefix='real-owned-island-',dir=out))
copy=work/'conf'
copy.mkdir()
for f in names:shutil.copy2(source/f,copy/f)
raw=(copy/'fxfile.conf').read_bytes()
enc='utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8'
content=raw.decode(enc)
for key in ('config.global_hotkey.enable','config.global_hotkey.show_tray',
            'config.global_hotkey.windows_startup','config.register_shell_context_menu',
            'config.single_process'):
 content,n=re.subn(r'(?m)^(\s*'+re.escape(key)+r'\s*=\s*)[^\r\n]*',
                   lambda m:m.group(1)+'0',content)
 assert n==1,'cloned side effect key not uniquely found: '+key
(copy/'fxfile.conf').write_bytes(content.encode(enc))
fixture=work/'fixture'/'My Documents'/'My Music'
fixture.mkdir(parents=True)
(fixture/'synthetic.txt').write_text('test fixture only\n')
trace=work/'island-dll-trace.log'
env={**os.environ,'APPDATA':str(work/'appdata'),
     'FLYEXP_PHASE5_TEST_ISLAND_DLL':str(dll),
     'FLYEXP_MFC_DLL_TRACE':str(trace)}
(work/'appdata').mkdir()
u=C.windll.user32
CB=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CB,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
def title(hwnd):
 buffer=C.create_unicode_buffer(1024)
 u.GetWindowTextW(hwnd,buffer,1024)
 return buffer.value
def main_window(pid):
 matches=[]
 @CB
 def scan(hwnd,_):
  p=W.DWORD()
  u.GetWindowThreadProcessId(hwnd,C.byref(p))
  if p.value==pid and title(hwnd).endswith(' - fxfile') and u.IsWindowVisible(hwnd):
   matches.append(int(hwnd))
  return True
 u.EnumWindows(scan,0)
 return matches[0] if len(matches)==1 else None
def eventually(fn,description,timeout=9):
 stop=time.monotonic()+timeout
 while time.monotonic()<stop:
  try:
   result=fn()
   if result:return result
  except Exception:pass
  time.sleep(.15)
 raise AssertionError(description+'; DLL trace='+trace.read_text(errors='replace') if trace.exists() else description)
proc=None
hwnd=None
pri_target=None
pri_source=dll.parent/'FlyExplorerIslandBridge.pri'
owned_product=product
try:
 if textbox_mode=='app':
  # No write to normal product bin directory: create a disposable host image.
  owned_product,pri_target=stage_test_host(
      product,pri_source,work/'packaged-host',bridge_dll=dll)
  assert owned_product.parent != product.parent
  env['FLYEXP_PHASE5_TEST_ISLAND_DLL']=str(owned_product.parent/dll.name)
  print('EXPERIMENTAL_HOST_PRI_AND_BRIDGE_STAGED',build_mode,flush=True)
 proc=subprocess.Popen([str(owned_product),'--conf_dir',str(copy),str(fixture)],
                       cwd=str(work),env=env,stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 hwnd=eventually(lambda:main_window(proc.pid),'actual isolated MFC MainFrame',13)
 eventually(lambda:title(hwnd).lower().endswith('my music - fxfile'),'initial folder')
 frame=Desktop(backend='uia').window(handle=hwnd)
 # Trigger native layout after DLL attachment, then identify the exact child HWND
 # reported by the in-process XAML bridge itself.
 dimensions=frame.rectangle()
 assert u.MoveWindow(hwnd,100,100,(max)(1200,dimensions.width()),(max)(780,dimensions.height()),True)
 time.sleep(.45)
 def island_handle():
  if not trace.exists(): return 0
  values=re.findall(r'dll-island-hwnd=(\d+) visible=1',trace.read_text(errors='replace'))
  return int(values[-1]) if values else 0
 island=eventually(island_handle,'visible in-process XAML child HWND')
 island_pid=W.DWORD()
 u.GetWindowThreadProcessId(island,C.byref(island_pid))
 assert island_pid.value==proc.pid and u.IsChild(hwnd,island),'island must be a child in the real product PID'
 print('REAL_PRODUCT_SAME_PROCESS_ISLAND_MFC_PASS','PID',proc.pid,'ISLAND_HWND',island,flush=True)
 island_ui=Desktop(backend='uia').window(handle=island)
 descendants=[(d.element_info.automation_id,d.friendly_class_name(),d.window_text())
              for d in island_ui.descendants()]
 print('ISLAND_DIRECT_UIA_DESCENDANTS',descendants[:16],flush=True)
 controls={name:island_ui.child_window(auto_id='Phase5Island'+name+'Button',
                                     control_type='Button')
           for name in ('Up','Back','Forward')}
 for name,control in controls.items():
  assert control.exists(timeout=3),'missing actual XAML '+name+' button'
 assert 'Phase5IslandCurrentFolderText' in {item[0] for item in descendants}
 if textbox_mode:
  eventually(lambda:trace.exists() and 'dll-textbox-loaded' in trace.read_text(errors='replace'),
             'test-only WinUI TextBox never loaded',9)
  probe=island_ui.child_window(auto_id='Phase5IslandDiagnosticTextBox',
                                control_type='Edit')
  assert probe.exists(timeout=3),'test-only WinUI TextBox UIA edit missing'
  if textbox_mode=='app':
   eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
              'editable TextBox not bound to real active pane')
   print('REAL_PRODUCT_ACTIVE_PANE_ADDRESS_SYNC_PASS',flush=True)
   probe.set_focus()
   keyboard.send_keys('^a')
   keyboard.send_keys('Phase5-Input-20260928',with_spaces=True)
   eventually(lambda:probe.window_text()=='Phase5-Input-20260928',
              'WinUI TextBox Ctrl+A failed to replace initial native address')
   print('REAL_PRODUCT_EDITABLE_TEXTBOX_CTRL_A_PASS',flush=True)
   keyboard.send_keys('{ESC}')
   eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
              'Escape failed to cancel edit and restore active pane address')
   print('REAL_PRODUCT_EDITABLE_TEXTBOX_ESCAPE_PASS',flush=True)
   # Native MFC-issued navigation must update the XAML TextBox without
   # requiring any WinUI button command.
   controls['Up'].set_focus()
   assert u.PostMessageW(hwnd,0x111,32004,0),'native MFC Up post failed'
   eventually(lambda:title(hwnd).lower().endswith('my documents - fxfile'),
              'external native MFC Up command did not navigate')
   eventually(lambda:probe.window_text().lower()==str(fixture.parent).lower(),
              'external native navigation did not update XAML address')
   print('REAL_PRODUCT_EXTERNAL_MFC_NAV_TO_XAML_SYNC_PASS',flush=True)
   assert u.PostMessageW(hwnd,0x111,32006,0),'native MFC Back post failed'
   eventually(lambda:title(hwnd).lower().endswith('my music - fxfile'),
              'external native MFC Back command did not navigate')
   eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
              'external native Back did not update XAML address')
   print('REAL_PRODUCT_EXTERNAL_MFC_BACK_SYNC_PASS',flush=True)
   # A focused but unchanged address must still track native navigation.
   probe.set_focus()
   assert u.PostMessageW(hwnd,0x111,32004,0),'clean-focus native Up post failed'
   eventually(lambda:probe.window_text().lower()==str(fixture.parent).lower(),
              'focused but unmodified address failed native path refresh')
   assert u.PostMessageW(hwnd,0x111,32006,0),'clean-focus native Back post failed'
   eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
              'focused but unmodified address failed native Back refresh')
   print('REAL_PRODUCT_PRISTINE_FOCUS_STILL_SYNCS_NATIVE_PASS',flush=True)
   # A native folder change must not overwrite an in-progress text edit
   # while the actual WinUI TextBox remains focused.
   probe.set_focus()
   keyboard.send_keys('^a')
   keyboard.send_keys('Draft-Not-A-Folder',with_spaces=True)
   eventually(lambda:probe.window_text()=='Draft-Not-A-Folder',
              'unable to start editable address draft')
   assert probe.has_keyboard_focus(),'lost TextBox focus before external change'
   assert u.PostMessageW(hwnd,0x111,32004,0),'external Up while editing failed'
   eventually(lambda:title(hwnd).lower().endswith('my documents - fxfile'),
              'native folder failed to change during address edit')
   if probe.has_keyboard_focus():
    assert probe.window_text()=='Draft-Not-A-Folder', (
           'native pane change silently overwrote focused user input')
    print('REAL_PRODUCT_DRAFT_SURVIVES_NATIVE_CHANGE_PASS',flush=True)
   else:
    print('REAL_PRODUCT_DRAFT_SURVIVES_NATIVE_CHANGE_NOT_TESTED_FOCUS_MOVED',flush=True)
   probe.set_focus()
   keyboard.send_keys('{ESC}')
   eventually(lambda:probe.window_text().lower()==str(fixture.parent).lower(),
              'Escape failed to restore latest native path after edit')
   print('REAL_PRODUCT_DRAFT_ESCAPE_RESTORES_LATEST_PANE_PASS',flush=True)
   controls['Back'].set_focus()
   assert u.PostMessageW(hwnd,0x111,32006,0),'restore native Back failed'
   eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
              'native Back did not restore test fixture before UI command tests')
  else:
   assert 'isolated' in probe.window_text().lower(),'diagnostic TextBox initial text missing'
  print('REAL_PRODUCT_ISOLATED_TEXTBOX_LOAD_UIA_PASS',textbox_mode,flush=True)
 print('REAL_PRODUCT_TEST_DPI',u.GetDpiForWindow(hwnd),flush=True)
 rect_t=W.RECT()
 assert u.GetWindowRect(island,C.byref(rect_t))
 before=(rect_t.left,rect_t.top,rect_t.right,rect_t.bottom)
 command_id={'Up':32004,'Back':32006,'Forward':32007}
 for command,ending in [('Up','my documents - fxfile'),
                        ('Back','my music - fxfile'),
                        ('Forward','my documents - fxfile')]:
  actual=controls[command].rectangle()
  assert actual.width()>0 and actual.height()>0,'invalid actual XAML button geometry'
  mouse.click(coords=(actual.left+actual.width()//2,actual.top+actual.height()//2))
  observed=eventually(lambda:title(hwnd) if title(hwnd).lower().endswith(ending) else None,
                      'native product ignored in-process XAML pointer '+command)
  marker='dll-command='+str(command_id[command])+' result='
  eventually(lambda:marker in trace.read_text(errors='replace'),'missing XAML command trace '+command)
  eventually(lambda:'dll-focus-'+command.lower() in trace.read_text(errors='replace'),
             'XAML focus did not reach '+command)
  print('REAL_PRODUCT_COMMAND_VIA_IN_PROCESS_MFC_WINUI_PASS',command,observed,flush=True)
 # Keyboard activation through the real XAML button and the MFC message loop.
 controls['Back'].set_focus()
 keyboard.send_keys('{ENTER}')
 eventually(lambda:title(hwnd) if title(hwnd).lower().endswith('my music - fxfile') else None,
            'keyboard ENTER on XAML Back did not reach product')
 keyboard.send_keys('{TAB}')
 eventually(lambda:controls['Forward'].has_keyboard_focus(),
            'TAB did not move XAML focus Back -> Forward')
 keyboard.send_keys('{ENTER}')
 eventually(lambda:title(hwnd) if title(hwnd).lower().endswith('my documents - fxfile') else None,
            'keyboard ENTER on tab-focused XAML Forward did not reach product')
 print('REAL_PRODUCT_IN_PROCESS_KEYBOARD_TAB_ENTER_PASS',flush=True)
 if textbox_mode=='app':
  # UIA ValuePattern sets the long synthetic absolute path exactly;
  # physical keyboard editing and Ctrl+A/Esc are exercised separately above.
  probe.set_edit_text(str(fixture))
  probe.set_focus()
  eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
             'WinUI TextBox did not accept target folder path')
  keyboard.send_keys('{ENTER}')
  eventually(lambda:title(hwnd).lower().endswith('my music - fxfile'),
             'native engine did not navigate from WinUI address Enter')
  eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
             'address not refreshed after native navigation')
  print('REAL_PRODUCT_ADDRESS_ENTER_NATIVE_ENGINE_PASS',flush=True)
  if extra_ui:
   long_ok=True
   if os.environ.get('FLYEXP_PHASE5_RUN_LONG_KEYS','')=='1':
    # Start in the parent so that a complete keyboard-entered path must
    # actually navigate the native product to the target, not merely match
    # a pre-existing address in the field.
    controls['Up'].click_input()
    eventually(lambda:title(hwnd).lower().endswith('my documents - fxfile'),
               'native Up before physical long-address test failed')
    eventually(lambda:probe.window_text().lower()==str(fixture.parent).lower(),
               'native Up did not synchronize address before keyboard input')
    probe.set_focus()
    keyboard.send_keys('^a')
    keyboard.send_keys(str(fixture),with_spaces=True,pause=0.035)
    time.sleep(.25)
    typed=probe.window_text()
    long_ok=typed.lower()==str(fixture).lower()
    print('LONG_PATH_RATE_LIMITED_KEY_EVENT_RESULT',long_ok,
          'actual_length',len(typed),'expected_length',len(str(fixture)),flush=True)
    if not long_ok:
     import difflib
     changes=[(tag,str(fixture)[i:j],typed[k:l])
              for tag,i,j,k,l in difflib.SequenceMatcher(
                  None,str(fixture),typed).get_opcodes() if tag!='equal']
     print('LONG_INPUT_MISMATCH_EDITS',changes[:9],flush=True)
     # Compare the default Unicode VK_PACKET injector with native virtual-key
     # translation. Missing separators alone must not trigger a product edit.
     probe.set_edit_text('')
     probe.set_focus()
     keyboard.send_keys(str(fixture),with_spaces=True,
                        pause=0.035,vk_packet=False)
     time.sleep(.2)
     physical_vk=probe.window_text()
     vk_ok=physical_vk.lower()==str(fixture).lower()
     print('LONG_PATH_NATIVE_VK_EVENT_RESULT',vk_ok,
           'actual_length',len(physical_vk),'expected_length',len(str(fixture)),
           flush=True)
     long_ok=vk_ok
    if long_ok:
     # This Enter acts on the exact path typed with actual keyboard events.
     keyboard.send_keys('{ENTER}')
     eventually(lambda:title(hwnd).lower().endswith('my music - fxfile'),
                'fully keyboard-typed long address did not navigate native engine')
     eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
                'XAML path did not refresh after keyboard-only long address')
     print('REAL_PRODUCT_PHYSICAL_LONG_PATH_ENTER_NATIVE_ENGINE_PASS',
           len(str(fixture)),flush=True)
    # Restore synthetic field for subsequent independent product path gates.
    probe.set_edit_text(str(fixture))
    controls['Up'].set_focus()
    eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
               'synthetic address not restored after long-input diagnosis')
   status=island_ui.child_window(auto_id='Phase5IslandStatusText',
                                  control_type='Text')
   invalid=str(fixture)+'\\__phase5_missing_test_directory__'
   probe.set_edit_text(invalid)
   probe.set_focus()
   keyboard.send_keys('{ENTER}')
   eventually(lambda:'rejected' in status.window_text().lower(),
              'invalid native path did not show an explicit rejection')
   assert title(hwnd).lower().endswith('my music - fxfile')
   keyboard.send_keys('{ESC}')
   eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
              'invalid address Escape failed to restore active pane')
   print('REAL_PRODUCT_INVALID_LOCAL_PATH_REJECT_AND_RESTORE_PASS',flush=True)

   # Open a separate native tab, navigate only that active tab through the
   # existing C++ engine, and switch between two distinct real tab paths.
   controls['Up'].set_focus()
   assert u.PostMessageW(hwnd,0x111,35012,0),'native new tab dispatch failed'
   time.sleep(.45)
   probe.set_edit_text(str(fixture.parent))
   probe.set_focus()
   keyboard.send_keys('{ENTER}')
   eventually(lambda:title(hwnd).lower().endswith('my documents - fxfile'),
              'new native tab cannot navigate through WinUI address')
   controls['Up'].set_focus()
   assert u.PostMessageW(hwnd,0x111,35021,0),'native previous tab failed'
   eventually(lambda:title(hwnd).lower().endswith('my music - fxfile'),
              'switching to original tab did not restore original folder')
   eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
              'address not synced after previous tab')
   assert u.PostMessageW(hwnd,0x111,35022,0),'native next tab failed'
   eventually(lambda:title(hwnd).lower().endswith('my documents - fxfile'),
              'switching to new tab did not restore its folder')
   eventually(lambda:probe.window_text().lower()==str(fixture.parent).lower(),
              'address not synced after next tab')
   print('REAL_PRODUCT_NATIVE_TAB_SWITCH_ADDRESS_SYNC_PASS',flush=True)

   # The real splitter activates one of two native ExplorerViews; native
   # window-next/previous must refresh the address of the active pane.
   assert u.PostMessageW(hwnd,0x111,35003,0),'split 1x2 dispatch failed'
   time.sleep(.65)
   controls['Up'].set_focus()
   assert u.PostMessageW(hwnd,0x111,35000,0),'next native pane dispatch failed'
   time.sleep(.4)
   probe.set_edit_text(str(fixture))
   probe.set_focus()
   keyboard.send_keys('{ENTER}')
   eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
              'cannot navigate second active native pane')
   controls['Up'].set_focus()
   assert u.PostMessageW(hwnd,0x111,35001,0),'previous native pane dispatch failed'
   eventually(lambda:probe.window_text().lower()==str(fixture.parent).lower(),
              'switching to other pane did not restore its own address')
   assert u.PostMessageW(hwnd,0x111,35000,0),'next native pane second dispatch failed'
   eventually(lambda:probe.window_text().lower()==str(fixture).lower(),
              'returning to second pane did not restore its own address')
   print('REAL_PRODUCT_NATIVE_MULTI_PANE_ADDRESS_SYNC_PASS',flush=True)
   if not long_ok:raise AssertionError(
      'rate-limited Win32 keyboard event injection still dropped long path characters')
 assert not u.IsHungAppWindow(hwnd)
 host=frame.rectangle()
 assert u.MoveWindow(hwnd,host.left,host.top,host.width()+90,host.height()+60,True)
 time.sleep(.35)
 assert not u.IsHungAppWindow(hwnd)
 after_rect=W.RECT()
 assert u.GetWindowRect(island,C.byref(after_rect))
 after_island=(after_rect.left,after_rect.top,after_rect.right,after_rect.bottom)
 assert after_island!=before,'XAML child did not move/resize with MFC host'
 print('REAL_PRODUCT_IN_PROCESS_RESIZE_RESPONSIVE_PASS',before,'->',after_island,flush=True)
 if textbox_mode:print('REAL_PRODUCT_TEXTBOX_DIAGNOSTIC_END_TO_END_PASS',textbox_mode,flush=True)
finally:
 try:del controls,island_ui,frame
 except NameError:pass
 import gc
 gc.collect()
 if proc is not None and proc.poll() is None:
  if hwnd and u.IsWindow(hwnd):assert u.PostMessageW(hwnd,0x10,0,0)
  try:proc.wait(timeout=9)
  except subprocess.TimeoutExpired:
   proc.terminate()
   proc.wait(timeout=5)
   print('OWN_PRODUCT_FORCED_SHUTDOWN',flush=True)
 after={f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in names}
 print('ORIGINAL_SIX_USER_CONFIG_HASHES_UNCHANGED',after==original,
       'PRODUCT_EXIT',None if proc is None else proc.returncode,
       'DLL_TRACE',trace.read_text(errors='replace') if trace.exists() else 'missing',flush=True)
 if pri_target is not None:
  # The disposable owned host retains its PRI for postmortem test evidence,
  # while neither normal product output nor any user installation is touched.
  assert pri_target.is_file() and hashlib.sha256(pri_target.read_bytes()).digest()==hashlib.sha256(pri_source.read_bytes()).digest(),'owned-host PRI unexpectedly modified'
  print('EXPERIMENTAL_HOST_PRI_ISOLATED',owned_product.parent != product.parent,flush=True)
  assert not (product.parent/'resources.pri').exists(),'unexpected normal-product PRI'
 assert after==original,'Original user configuration was modified'
 if proc is not None:assert proc.returncode==0,'Owned product did not exit cleanly'
