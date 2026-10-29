"""Owned F6 modal-boundary diagnostic; never clipboard, recycle or a confirmed copy."""
from pathlib import Path
import argparse,json,shutil,tempfile,time
import benchmark_filtered_folder_gui as helper

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--label',choices=('before','after'),default='before')
    parser.add_argument('--expect-blocked',action='store_true')
    args=parser.parse_args();exe=args.exe.resolve()
    assert exe==helper.ROOT/'out'/'winui'/'Release'/'flyExplorer.exe'
    base=helper.ROOT/'logs'/'modal-shortcuts-20261029';base.mkdir(parents=True,exist_ok=True)
    helper.BASE=base
    data=Path(tempfile.mkdtemp(prefix='fixture-',dir=base)).resolve()
    left=data/'Left';right=data/'Right';left.mkdir();right.mkdir()
    name='OwnedModal.txt'
    (left/name).write_bytes(b'owned modal source');(right/name).write_bytes(b'owned modal destination')
    passed=False
    try:
        with helper.App(exe,left,args.label+'-f6') as app:
            app.el('RightFiles').click_input();app.navigate(right,name)
            row=helper.wait(lambda:next((r for r in app.rows('Left') if name in r.window_text()),None),'owned source absent')
            row.click_input();row.select()
            helper.wait(lambda:app.el('CopyButton').is_enabled(),'copy not ready')
            app.el('CopyButton').invoke()
            def cancel():return next((r for r in app.win.descendants(control_type='Button') if r.window_text()=='취소' and r.is_visible()),None)
            helper.wait(cancel,'owned collision dialog absent')
            before=app.el('AddressBox').get_value()
            app.capture('modal-before-f6')
            app.keys('{F6}');time.sleep(.25)
            after=app.el('AddressBox').get_value()
            assert cancel() is not None,'F6 dismissed the collision dialog'
            app.report.update(before_address=before,after_address=after,modal_f6_switched_pane=after.casefold()!=before.casefold())
            app.capture('modal-after-f6')
            if args.expect_blocked:assert after==before,'F6 changed the active pane during confirmation'
            app.keys('{ESC}')
            helper.wait(lambda:cancel() is None and app.el('UpButton').is_enabled(),'cancel did not settle')
            app.report['escape_closed_dialog']=True
            # Verify the same real keyboard path works when the modal is closed.
            app.el('LeftFiles').set_focus()
            helper.wait(lambda:app.el('AddressBox').get_value().casefold()==str(left).casefold(),'left pane did not regain focus')
            current=app.el('AddressBox').get_value()
            app.keys('{F6}')
            helper.wait(lambda:app.el('AddressBox').get_value().casefold()!=current.casefold(),'non-modal F6 positive control failed')
            app.report['nonmodal_f6_switches_pane']=True
        passed=True
    finally:
        assert (left/name).read_bytes()==b'owned modal source' and (right/name).read_bytes()==b'owned modal destination'
        assert [p.name for p in left.iterdir()]==[name] and [p.name for p in right.iterdir()]==[name]
        if passed:
            assert data.parent==base.resolve() and not data.is_symlink();shutil.rmtree(data)
        print('MODAL_F6_RESULT='+json.dumps({'diagnostic_completed':passed,'fixture_removed':passed,'owned_bytes_unchanged':True}),flush=True)

if __name__=='__main__':main()
