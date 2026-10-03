"""File detail worker lifecycle ownership after the MainWindow V8 audit."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

class FileDetailControllerContract(unittest.TestCase):
    def test_controller_owns_detail_worker_lifecycle_without_xaml(self):
        header=read("app/winui/file_detail_controller.h")
        main_h=read("app/winui/MainWindow.xaml.h")
        main_cpp=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn("class FileDetailController final",header)
        self.assertIn("void cancel(int side) noexcept",header)
        self.assertIn("void prepareForClose() noexcept",header)
        self.assertNotIn("Microsoft::UI::Xaml",header)
        self.assertNotIn("DispatcherQueue",header)
        self.assertIn("FileDetailController mFileDetails",main_h)
        self.assertNotIn("mDetailCancel",main_h)
        self.assertNotIn("mDetailCancel",main_cpp)
        self.assertIn("mFileDetails.prepareForClose()",main_cpp)
        self.assertIn("mFileDetails.cancel(side)",main_cpp)

    def test_worker_preserves_bounded_shell_visual_and_cancel_guards(self):
        impl=read("app/winui/file_detail_controller.cpp")
        for token in (
            "extensions.size()<24",
            "recover.size()>=2",
            "thumbnailBudget<4",
            "request.paths.size()>1200",
            "fxfile::filetype::queryVisuals(",
            "fxfile::thumbnail::query(",
            "if(cancelToken->load())return; // prevent stale metadata child launch",
            "if(cancelToken->load())return;",
        ):
            self.assertIn(token,impl)

    def test_mainwindow_keeps_live_state_acceptance_and_project_compiles_owner(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        project=read("app/winui/flyExplorer.project-template.xml")
        self.assertIn("mFileDetails.start(",main)
        self.assertIn("ActiveWindowTab().fileLists[side].accepts(",main)
        self.assertIn("pane.routeIds[tab]!=route",main)
        self.assertIn("pane.tabs[tab].snapshot().children.size()!=count",main)
        self.assertIn('<ClInclude Include="file_detail_controller.h" />',project)
        self.assertIn('<ClCompile Include="file_detail_controller.cpp">',project)

if __name__=="__main__":
    unittest.main()
