"""Accepted async requests must publish pending state to navigation chrome."""
from pathlib import Path
import unittest
CODE=(Path(__file__).resolve().parents[2]/'app/winui/MainWindow.xaml.cpp').read_text(encoding='utf-8-sig')

class NavigationSubmitChrome(unittest.TestCase):
    def test_every_live_submission_updates_chrome_before_loading_feedback(self):
        for name,end,submissions in (
            ('QueuePath','QueuePidl',('submitParsing(',)),
            ('QueuePidl','QueueNextFolderPage',('submitActive(',)),
            ('QueueNextFolderPage','UpdateWatch',('submitPreviousPage(','submitNextPage(')),
            ('OnLoadPreviousFiles','DetailLayoutProfile',('submitPreviousPage(',)),
        ):
            body=CODE.split('MainWindow::'+name+'(',1)[1].split('MainWindow::'+end+'(',1)[0]
            for submit in submissions:
                with self.subTest(method=name,submit=submit):
                    tail=body.split(submit,1)[1]
                    self.assertLess(tail.index('UpdateNavigationChrome();'),tail.index('StatusText().Text('))
                    self.assertIn('side==ActiveWindowTab().model.activePane',tail[:tail.index('StatusText().Text(')])

    def test_continuation_completion_refreshes_before_terminal_and_early_return_paths(self):
        result=CODE.split('void MainWindow::OnNativeResult(',1)[1].split('void MainWindow::OnNativeChange(',1)[0]
        before=result.split('if(completed.kind==Kind::NoChange)',1)[0]
        self.assertIn('if(completed.active&&continuation)UpdateNavigationChrome();',before)

if __name__=='__main__':unittest.main()
