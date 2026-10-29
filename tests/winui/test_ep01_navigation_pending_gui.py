"""Observe real navigation transitions without injected product delays."""
from pathlib import Path
import argparse,ctypes as c,json,os,shutil,tempfile,threading,time,traceback
from ctypes import wintypes as w
from PIL import ImageGrab
from pywinauto import keyboard,mouse
import benchmark_filtered_folder_gui as helper

class Events:
    """One live property per observation; the product fix supplies the transition."""
    def __init__(self,app,label,target):
        self.app=app;self.label=label;self.target=target
        self.ready=threading.Event();self.stop=threading.Event();self.sent=threading.Event()
        self.mode=None;self.acted=False;self.events=[];self.actions=[];self.errors=[];self.states={}
        r=app.win.rectangle();self.bounds=(r.left,r.top,r.right,r.bottom)
        assert 0<=r.left<r.right<=helper.u.GetSystemMetrics(0) and 0<=r.top<r.bottom<=helper.u.GetSystemMetrics(1)
        self.thread=threading.Thread(target=self.run,daemon=True)
    def arm(self,mode):
        self.mode=mode;self.acted=False;self.sent.clear()
    def run(self):
        import comtypes
        from comtypes.client import CreateObject
        from comtypes.gen import UIAutomationClient as U
        comtypes.CoInitializeEx(0)
        try:
            automation=CreateObject(U.CUIAutomation,interface=U.IUIAutomation)
            element=automation.ElementFromHandle(self.app.hwnd)
            assert element.CurrentProcessId==self.app.app.pid
            nodes={key:element.FindFirst(4,automation.CreatePropertyCondition(30011,key)) for key in ('BackButton','ForwardButton','UpButton','StatusText','AddressBox')}
            self.states={key:bool(nodes[key].CurrentIsEnabled) for key in ('BackButton','ForwardButton','UpButton')}
            self.ready.set()
            while not self.stop.wait(.003):
                if not self.mode or not self.sent.is_set() or self.acted:continue
                started=time.perf_counter()
                if self.label=='before':
                    self.acted=True
                    assert helper.owner(helper.u.GetForegroundWindow())==self.app.app.pid
                    for index in range(6):
                        path=helper.BASE/(self.label+'-history-frame-'+str(index)+'.png')
                        ImageGrab.grab(bbox=self.bounds,include_layered_windows=True).save(path)
                        self.app.images.append(('history-frame-'+str(index),path))
                        time.sleep(.04)
                    self.actions.append({'phase':self.mode,'frames':6,'t':time.perf_counter()})
                    continue
                pending=not bool(nodes['UpButton'].CurrentIsEnabled)
                if not pending:continue
                self.acted=True
                assert helper.owner(helper.u.GetForegroundWindow())==self.app.app.pid
                path=helper.BASE/(self.label+'-'+self.mode+'-loading.png')
                ImageGrab.grab(bbox=self.bounds,include_layered_windows=True).save(path)
                self.app.images.append((self.mode+'-loading',path))
                self.states={key:bool(nodes[key].CurrentIsEnabled) for key in ('BackButton','ForwardButton','UpButton')}
                self.events.extend({'t':time.perf_counter(),'phase':self.mode,'key':key,'value':value} for key,value in self.states.items())
                record={'phase':self.mode,'observed_pending_t':started,'t':time.perf_counter(),'states':dict(self.states)}
                self.actions.append(record)
                if self.mode=='history' and self.label=='after':
                    keyboard.send_keys('%{LEFT}',pause=0)
                    record['guard_feedback']='현재 폴더 이동이 끝난 뒤' in nodes['StatusText'].CurrentName
                elif self.mode=='replace':
                    assert not any(ch in str(self.target) for ch in '+^%{}()')
                    keyboard.send_keys('^l',pause=0)
                    deadline=time.monotonic()+1
                    while not nodes['AddressBox'].CurrentHasKeyboardFocus and time.monotonic()<deadline:time.sleep(.01)
                    assert nodes['AddressBox'].CurrentHasKeyboardFocus,'owned address editor did not take focus'
                    keyboard.send_keys('^a'+str(self.target),pause=0)
                    record['enter_while_pending']=not bool(nodes['UpButton'].CurrentIsEnabled)
                    assert record['enter_while_pending'],'address typing missed pending interval'
                    keyboard.send_keys('{ENTER}',pause=0)
                record['input_finished']=time.perf_counter()
        except BaseException:self.errors.append(traceback.format_exc());self.ready.set()
        finally:comtypes.CoUninitialize()
    def close(self):
        self.mode=None;self.stop.set();self.thread.join(timeout=5)
        assert not self.thread.is_alive() and not self.errors,self.errors

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--phase',choices=('before','after'),required=True)
    parser.add_argument('--fixture',type=Path)
    parser.add_argument('--scope',choices=('all','replace','before-sort'),default='all')
    args=parser.parse_args();exe=args.exe.resolve()
    base=helper.ROOT/'logs'/'navigation-events-20261029'
    assert exe in (helper.ROOT/'out'/'winui'/'Release'/'flyExplorer.exe',base/'before-runtime'/'flyExplorer.exe')
    point=w.POINT();assert helper.u.GetCursorPos(c.byref(point)),'INPUT_DESKTOP_UNAVAILABLE; no fixture/app launched'
    base.mkdir(parents=True,exist_ok=True);helper.BASE=base
    data=args.fixture.resolve() if args.fixture else Path(tempfile.mkdtemp(prefix='fixture-',dir=base)).resolve()
    if args.fixture:assert data==base/'paired-fixture' and data.is_dir() and not data.is_symlink()
    a=data/'A';b=data/'B';big=data/'Big'
    if not args.fixture:
        for p in (a,b,big):p.mkdir()
        (a/'owned-a.txt').write_bytes(b'owned-a');(b/'owned-b.txt').write_bytes(b'owned-b')
        for i in range(8000):(big/f'entry-{i:05d}.txt').write_bytes(f'owned-{i}'.encode())
    passed=False
    try:
        with helper.App(exe,a,args.phase+'-navigation') as app:
            app.el('RightFiles').click_input();app.keys('^l')
            app.el('AddressBox').set_edit_text(str(b));app.el('AddressBox').set_focus();app.keys('{ENTER}')
            helper.wait(lambda:app.el('AddressBox').get_value().casefold()==str(b).casefold() and 'owned-b.txt' in app.first('Right') and app.el('UpButton').is_enabled(),'explicit right B did not settle')
            app.el('LeftFiles').set_focus()
            if args.scope=='all':app.navigate(b,'owned-b.txt')
            app.navigate(big,'entry-00000.txt')
            if args.scope=='all':
                app.el('BackButton').invoke()
                helper.wait(lambda:'owned-b.txt' in app.first() and app.el('BackButton').is_enabled() and app.el('ForwardButton').is_enabled(),'B history not ready')
            app.el('LeftFiles').set_focus();app.capture('ready')
            events=Events(app,args.phase,a);events.thread.start()
            try:
                assert events.ready.wait(8) and not events.errors,events.errors
                if args.scope=='all':
                    assert all(events.states.values()),events.states
                    events.arm('history')
                    if args.phase=='before':
                        rect=app.el('ForwardButton').rectangle();events.sent.set()
                        mouse.click(coords=((rect.left+rect.right)//2,(rect.top+rect.bottom)//2))
                    else:app.keys('%{RIGHT}');events.sent.set()
                    helper.wait(lambda:app.el('AddressBox').get_value().casefold()==str(big).casefold() and app.el('BackButton').is_enabled() and app.el('UpButton').is_enabled() and 'entry-00000.txt' in app.first(),'history request did not settle')
                    helper.wait(lambda:bool(events.actions),'loading event/action absent',8)
                    guard=any(a.get('guard_feedback',False) for a in events.actions)
                    app.report['history_shortcut_attempted']=args.phase=='after'
                    app.report['history_shortcut_rejected']=guard
                    if args.phase=='after':
                        time.sleep(.3)
                        assert app.el('AddressBox').get_value().casefold()==str(big).casefold(),'history shortcut displaced pending target'
                        app.report['history_target_preserved']=True
                        for key in ('BackButton','ForwardButton','UpButton'):
                            assert any(e['phase']=='history' and e['key']==key and e['value'] is False for e in events.events),(key,events.events)
                        # The same real key route must work after completion.
                        events.mode=None;app.el('LeftFiles').set_focus();app.keys('%{LEFT}')
                        helper.wait(lambda:app.el('AddressBox').get_value().casefold()==str(b).casefold() and app.el('UpButton').is_enabled(),'settled Alt+Left positive control failed')
                        app.keys('%{RIGHT}')
                        helper.wait(lambda:app.el('AddressBox').get_value().casefold()==str(big).casefold() and app.el('UpButton').is_enabled(),'history restoration failed')
                        app.report['settled_history_shortcut_works']=True
                if args.scope=='before-sort':
                    events.arm('history');app.el('SortPicker').select(1);app.keys('{ESC}');events.sent.set()
                    helper.wait(lambda:app.count()==8000 and 'entry-07999.txt' in app.first(),'baseline full sort did not settle',40)
                    helper.wait(lambda:bool(events.actions),'baseline frames absent',8)
                    app.report['baseline_sorted_items']=8000
                if args.phase=='after':
                    events.arm('replace');app.el('SortPicker').select(1)
                    app.keys('{ESC}');app.el('LeftFiles').set_focus();events.sent.set()
                    helper.wait(lambda:app.el('AddressBox').get_value().casefold()==str(a).casefold() and app.el('UpButton').is_enabled() and 'owned-a.txt' in app.first(),'explicit address replacement did not settle',40)
                    helper.wait(lambda:any(x['phase']=='replace' for x in events.actions),'replacement was not event-triggered')
                    action=next(x for x in events.actions if x['phase']=='replace')
                    assert not action['states']['BackButton'] and not action['states']['UpButton'],action
                    time.sleep(.4)
                    assert app.el('AddressBox').get_value().casefold()==str(a).casefold() and 'owned-a.txt' in app.first()
                    app.report['explicit_address_replaced_pending']=True
                assert 'owned-b.txt' in app.first('Right')
                app.capture('settled')
            finally:
                events.close();app.report['events']=events.events;app.report['actions']=events.actions
        passed=True
    finally:
        assert (a/'owned-a.txt').read_bytes()==b'owned-a' and (b/'owned-b.txt').read_bytes()==b'owned-b'
        assert len(list(big.iterdir()))==8000
        for i in range(8000):assert (big/f'entry-{i:05d}.txt').read_bytes()==f'owned-{i}'.encode()
        if passed and not args.fixture:
            assert data.parent==base.resolve() and not data.is_symlink();shutil.rmtree(data)
        print('NAV_EVENT_FIXTURE='+json.dumps({'completed':passed,'owned_bytes_unchanged':True,'fixture_removed':passed and not args.fixture,'shared_fixture':bool(args.fixture)}),flush=True)

if __name__=='__main__':main()
