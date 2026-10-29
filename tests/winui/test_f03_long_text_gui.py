"""Owned long-text visual diagnostic at the existing 8192 UTF-16-unit limit."""
from pathlib import Path
import base64,ctypes as c,hashlib,json,os,platform,shutil,subprocess,sys,tempfile,time
from ctypes import wintypes as w
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'/'winui'))
from profile_guard import snapshot_legacy_profile,assert_legacy_profile_unchanged
from uia_polling import wait_until
from pywinauto import Desktop
from PIL import ImageGrab
import psutil
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--phase',choices=('before','after'),required=True)
PHASE=parser.parse_args().phase
BASE=ROOT/'logs'/'f03-long-text-owned'
BASE.mkdir(parents=True,exist_ok=True)
owned=Path(tempfile.mkdtemp(prefix=PHASE+'-',dir=BASE)).resolve()
fixture=owned/'fixture';fixture.mkdir()
# 8191 BMP units, then one supplementary character straddling the UI cap.
prefix=''.join(f'OWNED line {i:02d}: local preview scroll verification.\n' for i in range(90))
prefix += 'x'*(8191-len(prefix))
assert len(prefix)==8191
content=prefix+'\U0001f600'+' END-OF-OWNED-FILE'
file=fixture/'owned-long-preview.txt';file.write_bytes(content.encode('utf-8'))
assert file.read_bytes()==content.encode('utf-8')
sentinel=hashlib.sha256(file.read_bytes()).hexdigest()
env={k:v for k,v in os.environ.items() if not k.startswith('FLY')}
for key in ('APPDATA','LOCALAPPDATA','USERPROFILE','TEMP','TMP'):
    p=owned/key.lower();p.mkdir();env[key]=str(p)
legacy_root,legacy=snapshot_legacy_profile()
u=c.windll.user32
u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
u.MoveWindow.argtypes=(w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.BOOL)
u.PostMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
u.GetDpiForWindow.argtypes=(w.HWND,);u.GetDpiForWindow.restype=w.UINT
exe=ROOT/'out'/'winui'/'Release'/'flyExplorer.exe'
app=subprocess.Popen([str(exe),str(fixture)],cwd=exe.parent,env=env)
hwnd=None;complete=False;images=[]
result={'phase':PHASE,'windows':platform.version(),'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'input_utf8_bytes':len(file.read_bytes()),'input_utf16_units':len(file.read_bytes().decode('utf-8').encode('utf-16-le'))//2,'captures':[]}
def wait(fn,label,seconds=20):return wait_until(fn,label,seconds=seconds,interval=.15)
def pid(h):
    n=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(n));return n.value
def screenshot(label):
    win.set_focus();assert pid(u.GetForegroundWindow())==app.pid
    from pywinauto import mouse
    r=win.rectangle();mouse.move(coords=(r.left+400,r.top+15))
    time.sleep(.3);r=win.rectangle()
    assert 0<=r.left<r.right<=u.GetSystemMetrics(0) and 0<=r.top<r.bottom<=u.GetSystemMetrics(1)
    p=BASE/(PHASE+'-'+label+'.png');ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom),include_layered_windows=True).save(p)
    images.append((label,p));result['captures'].append({'label':label,'rect':[r.left,r.top,r.right,r.bottom],'dpi':u.GetDpiForWindow(hwnd)})
try:
    def view():
        global hwnd
        assert app.poll() is None
        assert Path(psutil.Process(app.pid).exe()).resolve()==exe.resolve()
        wins=[v for v in Desktop(backend='uia').windows(process=app.pid) if 'flyExplorer' in v.window_text()]
        if len(wins)!=1:return None
        hwnd=wins[0].handle;assert pid(hwnd)==app.pid
        return Desktop(backend='uia').window(handle=hwnd)
    win=wait(view,'owned window absent')
    el=lambda name:win.child_window(auto_id=name,visible_only=False)
    row=wait(lambda:next((v for v in el('LeftFiles').descendants(control_type='ListItem') if file.name in v.window_text()),None),'owned row absent')
    el('FileInfoToggleButton').invoke()
    row=wait(lambda:next((v for v in el('LeftFiles').descendants(control_type='ListItem') if file.name in v.window_text()),None),'owned row after Details absent')
    row.select()
    wait(lambda:el('FileInfoName').window_text()==file.name,'selected file metadata missing')
    el('TextPreviewRevealButton').invoke()
    el('TextPreviewToggleButton').invoke()
    def body():
        nodes=[v for v in win.descendants(control_type='Text') if v.element_info.automation_id=='TextPreviewBody']
        return nodes[0].window_text() if nodes else ''
    text=wait(body,'owned text preview missing')
    result['display_utf16_units']=len(text.encode('utf-16-le',errors='surrogatepass'))//2
    result['display_tail_codepoints']=[ord(ch) for ch in text[-4:]]
    result['unpaired_surrogate']=any(0xd800<=ord(ch)<=0xdfff for ch in text)
    result['matches_complete_prefix']=text==prefix
    result['status']=el('TextPreviewStatus').window_text()
    # Locate the two real ScrollViewers by the owned Details subtree.
    pane=el('FileInfoPane').wrapper_object()
    scrolls=pane.descendants(control_type='Pane')
    patterns=[]
    from pywinauto.uia_defines import NoPatternInterfaceError
    for node in scrolls:
        try:
            pat=node.iface_scroll
            if pat.CurrentVerticallyScrollable:patterns.append((node,pat))
        except NoPatternInterfaceError:pass
    result['scrollable_viewports']=len(patterns)
    assert patterns,'no scrollable owned preview viewport'
    for theme,index in (('light',1),('dark',2)):
        el('ThemePicker').select(index)
        wait(lambda:('라이트' if index==1 else '다크') in el('ThemeStateText').window_text(),'theme missing')
        for label,width,height in (('wide',1220,700),('compact',960,519)):
            assert u.MoveWindow(hwnd,20,20,width,height,True)
            time.sleep(.4)
            # Scroll outer metadata to Preview; then capture the final body region.
            for node,pat in patterns:pat.SetScrollPercent(-1,100)
            screenshot(theme+'-'+label+'-end')
    if PHASE=='after':
        assert result['matches_complete_prefix'] and not result['unpaired_surrogate'],result
        assert result['display_utf16_units']==8191
    complete=True
finally:
    if app.poll() is None:
        if hwnd:u.PostMessageW(hwnd,0x10,0,0)
        try:app.wait(timeout=15)
        except subprocess.TimeoutExpired:app.terminate();app.wait(timeout=6)
    result['normal_exit']=app.returncode==0
    assert_legacy_profile_unchanged(legacy_root,legacy);result['legacy_profile_unchanged']=True
    assert hashlib.sha256(file.read_bytes()).hexdigest()==sentinel;result['original_bytes_preserved']=True
    if complete and result['normal_exit']:
        assert owned.parent==BASE and not owned.is_symlink();shutil.rmtree(owned);result['fixture_profiles_removed']=True
    print('PREVIEW_BOUNDARY_RESULT='+json.dumps(result),flush=True)
    for label,p in images:print('OWNED_PNG_'+PHASE+'-'+label+'='+base64.b64encode(p.read_bytes()).decode(),flush=True)
assert complete and result['normal_exit']
