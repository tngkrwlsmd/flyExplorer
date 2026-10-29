"""Search-result reveal owns one exact navigation and reuses row identity."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def src(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class SearchRevealContracts(unittest.TestCase):
    def test_only_accepted_explicit_locate_arms_target(self):
        feature = src("app/winui/m19_features.cpp")
        command = feature.split("void MainWindow::OnLocateSearchMatch(", 1)[1].split("void MainWindow::OnSelectSearchRecent(", 1)[0]
        self.assertLess(command.index("pendingConfirmationToken()"), command.index("QueuePath("))
        self.assertLess(command.index("SelectedSearchMatchPath()"), command.index("QueuePath("))
        self.assertLess(command.index("if(!request)return;"), command.index("reveal.target=match;"))
        for token in ("reveal.route=mSearchResultContext.route;", "reveal.tab=mSearchResultContext.tab;", "reveal.navigationRequest=request;"):
            self.assertIn(token, command)
        self.assertNotIn("SelectedItems().Append", command)
        self.assertNotIn("ShellExecute", command)
        self.assertNotIn("GetFileAttributes", command)

    def test_completion_and_same_folder_open_are_explicit(self):
        ui = src("app/winui/MainWindow.xaml.cpp")
        complete = ui.split("void MainWindow::OnNativeResult(", 1)[1].split("void MainWindow::OnNativeChange(", 1)[0]
        self.assertIn("reveal.completeNavigation(completed.request,", complete)
        self.assertIn("validTab?pane.routeIds[pane.active]:0,pane.active,", complete)
        self.assertIn("completed.kind==Kind::NoChange)&&", complete)
        self.assertIn("completed.action==Action::Open", complete)
        self.assertIn("CompareStringOrdinal(reveal.folder.c_str(),-1,", complete)
        no_change = complete.split("if(completed.kind==Kind::NoChange){", 1)[1].split("if(completed.kind==Kind::Failed){", 1)[0]
        self.assertIn(".fileCommandReveal.afterRefresh", no_change)
        self.assertIn("FillFiles(completed.side);", no_change)
        # Metadata invalidation happens between readiness and presentation;
        # it must not discard the new one-shot selection.
        state = src("app/winui/file_list_state.h")
        invalidate = state.split("void invalidate() noexcept {", 1)[1].split("}", 1)[0]
        self.assertNotIn("fileCommandReveal.clear()", invalidate)

    def test_render_reuses_exact_paths_and_clears_on_context_changes(self):
        ui = src("app/winui/MainWindow.xaml.cpp")
        fill = ui.split("void MainWindow::FillFiles(int side)", 1)[1].split("std::wstring MainWindow::WindowTabLabel(", 1)[0]
        for token in ("state.fileCommandReveal.route!=nextRoute", "state.fileCommandReveal.tab!=pane.active", "state.fileCommandReveal.folder==snapshot.parsingName", "CompareStringOrdinal(itemParsing.c_str(),-1,", "state.fileCommandReveal.target.c_str()", "if(revealAfterRefresh)state.fileCommandReveal.clear();", "if(revealAfterRefresh)view.ScrollIntoView(focusRow);"):
            self.assertIn(token, fill)
        suspend = ui.split("void MainWindow::SuspendActiveWindowTab()", 1)[1].split("void MainWindow::ApplyActiveWindowTab(", 1)[0]
        self.assertIn("state.fileLists[side].fileCommandReveal.clear();", suspend)
        commands = src("app/winui/m21_commands.cpp")
        arm = commands.split("auto& reveal=ActiveWindowTab().fileLists[side].fileCommandReveal;", 1)[1]
        self.assertLess(arm.index("reveal.clear();"), arm.index("reveal.target=completion.result.target;"))

    def test_actual_one_shot_state_compiles_and_rejects_stale_results(self):
        compiler = shutil.which("g++")
        if not compiler:
            self.skipTest("host C++ compiler unavailable")
        state = src("app/winui/file_list_state.h")
        value = "struct FileCommandReveal final {" + state.split("struct FileCommandReveal final {", 1)[1].split("} fileCommandReveal{};", 1)[0] + "};"
        code = "#include <string>\n#include <cstdint>\n#include <cstddef>\n#include <cassert>\n" + value + r'''
int main(){
 auto armed=[](){
  FileCommandReveal r{};
  r.target=L"C:\\Owned\\한글.txt";r.folder=L"C:\\Owned";
  r.route=7;r.tab=2;r.navigationRequest=91;
  return r;
 };
 auto r=armed();
 r.completeNavigation(91,7,2,true,true);
 assert(r.afterRefresh&&r.navigationRequest==0&&!r.target.empty());
 r.clear();
 assert(!r.afterRefresh&&r.target.empty()&&r.folder.empty()&&r.route==0&&r.tab==0);
 for(int failure=0;failure<7;++failure){
  r=armed();
  if(failure==5)r.target.clear();
  if(failure==6)r.navigationRequest=0;
  r.completeNavigation(failure==0?92:91,failure==1?8:7,
      failure==2?3:2,failure!=3,failure!=4);
  assert(!r.afterRefresh&&r.navigationRequest==0&&r.target.empty());
 }
 // A later create/rename must not inherit an old navigation ticket.
 r=armed();r.clear();r.target=L"new.txt";r.afterRefresh=true;
 assert(r.navigationRequest==0&&r.afterRefresh);
}
'''
        with tempfile.TemporaryDirectory(prefix="fly-search-reveal-") as directory:
            source = Path(directory) / "reveal.cpp"
            binary = Path(directory) / "reveal"
            source.write_text(code, encoding="utf-8")
            built = subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic", str(source), "-o", str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(built.returncode, 0, built.stderr)
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=5)
            self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main()
