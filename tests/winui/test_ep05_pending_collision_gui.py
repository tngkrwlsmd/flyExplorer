"""Owned collision-pending command-state check; cancel only, never copy/overwrite."""
from pathlib import Path
import argparse,base64,ctypes as c,hashlib,json,os,shutil,subprocess,tempfile,time
from ctypes import wintypes as w
from paths import ROOT
from profile_guard import snapshot_legacy_profile,assert_legacy_profile_unchanged
from uia_polling import wait_until
from pywinauto import Desktop,keyboard
from PIL import ImageGrab
import psutil

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--phase',choices=('before','after'),required=True)
    parser.add_argument('--theme',choices=('light','dark'),default='light')
    args=parser.parse_args();exe=args.exe.resolve()
    probe=c.windll.user32
    probe.GetCursorPos.argtypes=(c.POINTER(w.POINT),);probe.GetCursorPos.restype=w.BOOL
    point=w.POINT()
    if not probe.GetCursorPos(c.byref(point)):
        print('EP05_INPUT_DESKTOP_UNAVAILABLE: no app launched',flush=True)
        raise SystemExit(2)
    allowed=ROOT/'logs'/'five-goals-20261029'
    assert exe==ROOT/'out'/'winui'/'Release'/'flyExplorer.exe' or exe==allowed/'baseline-runtime'/'flyExplorer.exe'
    base=allowed/'collision';base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix=args.phase+'-'+args.theme+'-',dir=base)).resolve()
    left=owned/'Left';right=owned/'Right';left.mkdir();right.mkdir()
    name='OwnedCollision.txt';(left/name).write_bytes(b'owned source unchanged');(right/name).write_bytes(b'owned destination unchanged')
    env={k:v for k,v in os.environ.items() if not k.startswith('FLY')}
    for key in ('APPDATA','LOCALAPPDATA','USERPROFILE','TEMP','TMP'):
        p=owned/key.lower();p.mkdir();env[key]=str(p)
    legacy_root,legacy=snapshot_legacy_profile()
    u=c.windll.user32;u.GetForegroundWindow.restype=w.HWND
    u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
    u.MoveWindow.argtypes=(w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.BOOL)
    u.PostMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
    u.GetDpiForWindow.argtypes=(w.HWND,);u.GetDpiForWindow.restype=w.UINT
    app=subprocess.Popen([str(exe),str(left)],cwd=exe.parent,env=env)
    hwnd=None;passed=False;images=[]
    result={'phase':args.phase,'theme':args.theme,'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
    def wait(fn,label,seconds=22):return wait_until(fn,label,seconds=seconds,interval=.1)
    def pid(h):
        n=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(n));return n.value
    try:
        def view():
            nonlocal hwnd
            assert app.poll() is None
            assert Path(psutil.Process(app.pid).exe()).resolve()==exe
            wins=[x for x in Desktop(backend='uia').windows(process=app.pid) if 'flyExplorer' in x.window_text()]
            if len(wins)!=1:return None
            hwnd=wins[0].handle;assert pid(hwnd)==app.pid
            return Desktop(backend='uia').window(handle=hwnd)
        win=wait(view,'owned app absent');el=lambda key:win.child_window(auto_id=key,visible_only=False)
        def rows(side):return el(side+'Files').descendants(control_type='ListItem')
        def row(side):return next((x for x in rows(side) if name in x.window_text()),None)
        win.set_focus()
        assert pid(u.GetForegroundWindow())==app.pid
        assert u.MoveWindow(hwnd,20,20,1160,640,True)
        try:wait(lambda:row('Left'),'source absent')
        except AssertionError:
            print('EP05_STARTUP_STATE='+json.dumps({'address':el('AddressBox').get_value(),'status':el('StatusText').window_text(),'left_rows':len(rows('Left')),'right_rows':len(rows('Right'))}),flush=True)
            raise
        el('ThemePicker').select(1 if args.theme=='light' else 2)
        wait(lambda:('라이트' if args.theme=='light' else '다크') in el('ThemeStateText').window_text(),'theme absent')
        el('RightFiles').click_input();keyboard.send_keys('^l',pause=0)
        el('AddressBox').set_edit_text(str(right));el('AddressBox').set_focus();keyboard.send_keys('{ENTER}',pause=0)
        wait(lambda:el('AddressBox').get_value().casefold()==str(right).casefold() and row('Right'),'target absent')
        row('Left').click_input();row('Left').select()
        wait(lambda:el('CopyButton').is_enabled(),'app copy unavailable')
        keys=('CreateFolderButton','RenameButton','WindowsCutButton','WindowsCopyButton','WindowsPasteButton','RecycleButton','CopyButton','MoveButton')
        result['ready']={key:el(key).is_enabled() for key in keys}
        el('CopyButton').invoke()
        def cancel():
            return next((x for x in win.descendants(control_type='Button') if x.window_text()=='취소' and x.is_visible()),None)
        close=wait(cancel,'collision confirmation absent')
        assert any('동일한 이름이 이미 존재합니다' in x.window_text() for x in win.descendants(control_type='Text'))
        result['pending']={key:el(key).is_enabled() for key in keys}
        def capture(label):
            assert pid(u.GetForegroundWindow())==app.pid
            r=win.rectangle();assert 0<=r.left<r.right<=u.GetSystemMetrics(0) and 0<=r.top<r.bottom<=u.GetSystemMetrics(1)
            p=base/(args.phase+'-'+args.theme+'-'+label+'.png')
            ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom),include_layered_windows=True).save(p);images.append((label,p))
            result['window']=[r.left,r.top,r.right,r.bottom];result['dpi']=u.GetDpiForWindow(hwnd)
        capture('pending')
        assert (left/name).read_bytes()==b'owned source unchanged' and (right/name).read_bytes()==b'owned destination unchanged'
        # A background context-menu gesture must not bypass the active modal.
        keyboard.send_keys('+{F10}',pause=0);time.sleep(.2)
        result['pending_menu']=[{'name':x.window_text(),'enabled':x.is_enabled()} for x in win.descendants(control_type='MenuItem') if x.is_visible()]
        mutating={'새 폴더','새 텍스트 파일','잘라내기','복사','붙여넣기','이름 바꾸기','삭제','이동','반대쪽 패널로 보내기'}
        result['pending_mutating_menu']=[x for x in result['pending_menu'] if x['name'] in mutating]
        result['mutating_menu_observed']=bool(result['pending_mutating_menu'])
        result['menu_mutation_blocked']=not any(x['enabled'] for x in result['pending_mutating_menu'])
        assert cancel() is not None
        if args.phase=='after':
            assert not any(result['pending'].values()),result
            assert result['menu_mutation_blocked'],result['pending_menu']
        cancel().invoke()
        wait(lambda:el('CopyButton').is_enabled(),'command did not recover after cancel')
        result['recovered']={key:el(key).is_enabled() for key in keys}
        assert result['recovered']['CreateFolderButton'] and result['recovered']['CopyButton']
        assert el('AddressBox').get_value().casefold()==str(left).casefold()
        assert len(rows('Left'))==1 and len(rows('Right'))==1
        capture('recovered');passed=True
    finally:
        if app.poll() is None:
            if hwnd:u.PostMessageW(hwnd,0x10,0,0)
            try:app.wait(timeout=15)
            except subprocess.TimeoutExpired:app.terminate();app.wait(timeout=6)
        result['normal_exit']=app.returncode==0
        assert_legacy_profile_unchanged(legacy_root,legacy);result['original_settings_unchanged']=True
        assert (left/name).read_bytes()==b'owned source unchanged' and (right/name).read_bytes()==b'owned destination unchanged'
        assert [p.name for p in left.iterdir()]==[name] and [p.name for p in right.iterdir()]==[name]
        result['owned_bytes_unchanged']=True
        if passed and result['normal_exit']:
            assert owned.parent==base.resolve() and not owned.is_symlink();shutil.rmtree(owned);result['fixture_profiles_removed']=True
        print('EP05_PENDING_RESULT='+json.dumps(result),flush=True)
        for label,p in images:print('OWNED_PNG_'+args.phase+'-'+args.theme+'-'+label+'='+base64.b64encode(p.read_bytes()).decode(),flush=True)
    assert passed and result['normal_exit']

if __name__=='__main__':main()
