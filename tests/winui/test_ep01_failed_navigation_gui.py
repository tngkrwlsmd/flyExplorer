"""Owned failed-address preservation only; pending history is not accepted here."""
from pathlib import Path
import argparse,json,shutil,tempfile
from benchmark_filtered_folder_gui import App,BASE,ROOT,wait

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    args=parser.parse_args();exe=args.exe.resolve()
    assert exe==ROOT/'out'/'winui'/'Release'/'flyExplorer.exe'
    BASE.mkdir(parents=True,exist_ok=True)
    data=Path(tempfile.mkdtemp(prefix='failure-owned-',dir=BASE)).resolve()
    a=data/'A';b=data/'B';a.mkdir();b.mkdir()
    (a/'owned-a.txt').write_bytes(b'owned-a');(b/'owned-b.txt').write_bytes(b'owned-b')
    passed=False
    try:
        with App(exe,a,'after-failure') as app:
            wait(lambda:'owned-a.txt' in app.first('Right'),'opposite startup absent')
            app.navigate(b,'owned-b.txt')
            committed=app.el('AddressBox').get_value()
            app.capture('committed')
            missing=data/'owned-missing-never-created'
            app.keys('^l');app.el('AddressBox').set_edit_text(str(missing))
            app.el('AddressBox').set_focus();app.keys('{ENTER}')
            wait(lambda:'Shell 폴더를 열지 못했습니다' in app.el('StatusText').window_text() and app.el('UpButton').is_enabled(),'failure feedback absent')
            assert app.el('AddressBox').get_value()==committed
            # Type/size/date metadata can complete independently; compare identity.
            assert 'owned-b.txt' in app.first() and 'owned-a.txt' in app.first('Right')
            app.report.update(address_preserved=True,left_name_preserved=True,right_name_preserved=True,pending_history_acceptance='NOT_TESTED')
            app.capture('failed-navigation')
        passed=True
    finally:
        assert (a/'owned-a.txt').read_bytes()==b'owned-a' and (b/'owned-b.txt').read_bytes()==b'owned-b'
        assert sorted(p.relative_to(data).as_posix() for p in data.rglob('*') if p.is_file())==['A/owned-a.txt','B/owned-b.txt']
        if passed:
            assert data.parent==BASE.resolve() and not data.is_symlink();shutil.rmtree(data)
        print('EP01_FAILED_ADDRESS='+json.dumps({'passed':passed,'owned_bytes_unchanged':True,'fixture_removed':passed}),flush=True)

if __name__=='__main__':main()
