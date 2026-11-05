import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]

def read(name):
    return (ROOT/name).read_text(encoding="utf-8-sig")

class R07RestoreUiOwnerContract(unittest.TestCase):
    def test_callback_uses_weak_window_and_exact_owner_gate(self):
        header=read("app/winui/MainWindow.xaml.h")
        source=read("app/winui/m21_commands.cpp")
        self.assertIn("FileOperationRestoreCallback();",header)
        self.assertIn("RestoreCompletionContextCurrent(",header)
        callback=source.split("MainWindow::FileOperationRestoreCallback()",1)[1].split(
            "bool MainWindow::RestoreCompletionContextCurrent(",1)[0]
        self.assertIn("auto weak=get_weak();",callback)
        self.assertIn("if(auto ui=weak.get())",callback)
        self.assertNotIn("get_strong",callback)
        owner=source.split("bool MainWindow::RestoreCompletionContextCurrent(",1)[1].split(
            "void MainWindow::OnRenameRestoreCompleted(",1)[0]
        for token in ("mClosing", "origin.windowTabIdentity", "origin.side",
                      "pane.active!=origin.tab", "pane.pending[origin.tab]",
                      "pane.routeIds[origin.tab]!=origin.route",
                      "pane.filesystemPaths[origin.tab]!=origin.visibleFolder",
                      "snapshot().parsingName==", "origin.visibleShellFolder"):
            self.assertIn(token,owner)

    def test_result_is_written_only_to_origin_without_false_success(self):
        source=read("app/winui/m21_commands.cpp")
        body=source.split("void MainWindow::OnRenameRestoreCompleted(",1)[1].split(
            "void MainWindow::OnCreateFolder(",1)[0]
        self.assertIn("if(!RestoreCompletionContextCurrent(completion.context))return;",body)
        self.assertIn("Outcome::VerifiedCommitted",body)
        self.assertIn("Outcome::UncertainAfterAttempt",body)
        self.assertIn("state.identity==completion.context.windowTabIdentity",body)
        self.assertIn("state.fileOperationNotice=notice;",body)
        self.assertIn("ActiveWindowTab().identity==completion.context.windowTabIdentity",body)
        self.assertNotIn("startTakenRenameRestoreAsync",body)
        self.assertNotIn("Ctrl+Z",body)

    def test_user_undo_stays_disconnected(self):
        source=read("app/winui/m21_commands.cpp")
        wrapper=source.split(
            "MainWindow::StartPendingRenameRestoreForCurrentOwner(",1
        )[1].split("bool MainWindow::RestoreCompletionContextCurrent(",1)[0]
        self.assertIn("startTakenRenameRestoreAsync(",wrapper)
        self.assertIn("RestoreCompletionContextCurrent(liveContext)",wrapper)
        self.assertNotIn("Ctrl+Z",wrapper)
        self.assertNotIn("OnKey",wrapper)

if __name__=="__main__":
    unittest.main()
