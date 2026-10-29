"""Owned Preview button focus after keyboard reveal and compact restore."""
from pathlib import Path
import base64,ctypes as c,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from ctypes import wintypes as w
ROOT=Path(__file__).resolve().parents[2]
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--phase',choices=('before','after'),required=True)
parser.add_argument('--theme',choices=('light','dark'),default='light')
args=parser.parse_args()
BASE=ROOT/'logs'/'f03-preview-resize-owned'
BASE.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tests'/'winui'))
from profile_guard import snapshot_legacy_profile,assert_legacy_profile_unchanged
from uia_polling import wait_until
from pywinauto import Desktop,keyboard,mouse
from PIL import ImageGrab
import psutil
owned=Path(tempfile.mkdtemp(prefix='probe-',dir=BASE)).resolve()
fixture=owned/'fixture';fixture.mkdir();file=fixture/'owned-tip.txt';file.write_bytes(b'owned tooltip diagnostic only')
sentinel=hashlib.sha256(file.read_bytes()).hexdigest()
env={k:v for k,v in os.environ.items() if not k.startswith('FLY')}
for key in ('APPDATA','LOCALAPPDATA','USERPROFILE','TEMP','TMP'):
    p=owned/key.lower();p.mkdir();env[key]=str(p)
legacy_root,legacy=snapshot_legacy_profile()
u=c.windll.user32;u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
u.WindowFromPoint.argtypes=(w.POINT,);u.WindowFromPoint.restype=w.HWND
u.MoveWindow.argtypes=(w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.BOOL)
u.PostMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
u.GetDpiForWindow.argtypes=(w.HWND,);u.GetDpiForWindow.restype=w.UINT
exe=ROOT/'out'/'winui'/'Release'/'flyExplorer.exe'
app=subprocess.Popen([str(exe),str(fixture)],cwd=exe.parent,env=env)
hwnd=None;complete=False;images=[]
result={'phase':args.phase,'theme':args.theme,'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'states':[]}
def wait(fn,label,seconds=20):return wait_until(fn,label,seconds=seconds,interval=.15)
def pid(h):
    n=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(n));return n.value
def rect(node):
    r=node.rectangle();return [r.left,r.top,r.right,r.bottom]
def owned_mouse(point):
    assert pid(u.GetForegroundWindow())==app.pid
    assert pid(u.WindowFromPoint(w.POINT(point[0],point[1])))==app.pid,'foreign pointer pixel'
    mouse.move(coords=point)
def capture(label):
    assert pid(u.GetForegroundWindow())==app.pid
    box=rect(win);assert 0<=box[0]<box[2]<=u.GetSystemMetrics(0) and 0<=box[1]<box[3]<=u.GetSystemMetrics(1)
    tips=[]
    for top in Desktop(backend='uia').windows(process=app.pid):
        for node in top.descendants(control_type='ToolTip'):
            tips.append({'name':node.window_text(),'rect':rect(node)})
    p=BASE/(args.phase+'-'+args.theme+'-'+label+'.png');ImageGrab.grab(bbox=tuple(box),include_layered_windows=True).save(p);images.append((label,p))
    nodes={n.element_info.automation_id:n for n in win.descendants()}
    result['states'].append({'label':label,'window':box,'dpi':u.GetDpiForWindow(hwnd),'tooltips':tips,'reveal':rect(nodes['TextPreviewRevealButton']) if 'TextPreviewRevealButton' in nodes else None,'toggle':rect(nodes['TextPreviewToggleButton']) if 'TextPreviewToggleButton' in nodes else None,'toggle_has_focus':bool(nodes['TextPreviewToggleButton'].element_info.element.CurrentHasKeyboardFocus) if 'TextPreviewToggleButton' in nodes else None,'toggle_offscreen':bool(nodes['TextPreviewToggleButton'].element_info.element.CurrentIsOffscreen) if 'TextPreviewToggleButton' in nodes else None})
try:
    def view():
        global hwnd
        assert app.poll() is None
        assert Path(psutil.Process(app.pid).exe()).resolve()==exe.resolve()
        wins=[v for v in Desktop(backend='uia').windows(process=app.pid) if 'flyExplorer' in v.window_text()]
        if len(wins)!=1:return None
        hwnd=wins[0].handle;assert pid(hwnd)==app.pid
        return Desktop(backend='uia').window(handle=hwnd)
    win=wait(view,'owned window absent');el=lambda name:win.child_window(auto_id=name,visible_only=False)
    wait(lambda:el('LeftFiles').descendants(control_type='ListItem'),'owned file absent')
    win.set_focus();assert u.MoveWindow(hwnd,20,20,1220,700,True)
    el('ThemePicker').select(1 if args.theme=='light' else 2)
    wait(lambda:('라이트' if args.theme=='light' else '다크') in el('ThemeStateText').window_text(),'theme missing')
    el('FileInfoToggleButton').invoke()
    reveal=wait(lambda:el('TextPreviewRevealButton').wrapper_object(),'reveal absent')
    reveal.set_focus();box=reveal.rectangle();point=(box.mid_point().x,box.mid_point().y)
    owned_mouse(point);time.sleep(1.8);capture('hover')
    assert pid(u.GetForegroundWindow())==app.pid
    keyboard.send_keys('{ENTER}')
    wait(lambda:el('TextPreviewToggleButton').is_visible(),'keyboard reveal failed')
    time.sleep(.3);capture('keyboard-reveal')
    assert u.MoveWindow(hwnd,20,20,960,519,True)
    time.sleep(.4);capture('compact')
    owned_mouse((420,35));time.sleep(1.2);capture('pointer-away')
    if args.phase=='after':
        for state in result['states'][-2:]:
            assert state['toggle_has_focus'] and not state['toggle_offscreen'],state
            box=state['toggle'];pane=el('FileInfoPane').rectangle()
            assert pane.left<=box[0]<box[2]<=pane.right and pane.top<=box[1]<box[3]<=pane.bottom,state
        assert '켜기' in el('TextPreviewToggleButton').window_text(),'resize opted in'
        assert not any(n.element_info.automation_id=='TextPreviewBody' and n.window_text() for n in win.descendants()),'resize exposed content'
    complete=True
finally:
    if app.poll() is None:
        if hwnd:u.PostMessageW(hwnd,0x10,0,0)
        try:app.wait(timeout=15)
        except subprocess.TimeoutExpired:app.terminate();app.wait(timeout=6)
    result['normal_exit']=app.returncode==0
    assert_legacy_profile_unchanged(legacy_root,legacy);result['legacy_profile_unchanged']=True
    assert hashlib.sha256(file.read_bytes()).hexdigest()==sentinel;result['owned_bytes_unchanged']=True
    if complete and result['normal_exit']:
        assert owned.parent==BASE and not owned.is_symlink();shutil.rmtree(owned);result['fixture_profiles_removed']=True
    print('PREVIEW_TOOLTIP_DIAGNOSTIC='+json.dumps(result),flush=True)
    for label,p in images:print('OWNED_PNG_'+args.phase+'-'+args.theme+'-'+label+'='+base64.b64encode(p.read_bytes()).decode(),flush=True)
assert complete and result['normal_exit']
