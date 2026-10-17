"""F04-A source guard: filesystem tree path policy without UI/OS I/O."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HEADER = (ROOT / "app/winui/folder_tree_path.h").read_text(encoding="utf-8")
NATIVE = (ROOT / "tests/winui/native_f04_tree_path.cpp").read_text(encoding="utf-8")


class FolderTreePathContract(unittest.TestCase):
    def test_boundaries_and_stale_result_rejection(self):
        for required in (
            "kMaxPathUnits = 1024", "kMaxTreeDepth = 12",
            "kMaxChildrenPerNode = 128", "normalizedDrivePath(",
            "safeLeaf(", "childPath(", "RequestIdentity", "accepts(",
            "current.side == received.side", "current.tab == received.tab",
            "current.route == received.route",
            "current.generation == received.generation",
        ):
            self.assertIn(required, HEADER)

    def test_no_unreviewed_io_in_ui_thread_helper(self):
        for forbidden in (
            "GetFileAttributes", "FindFirstFile", "CreateFile", "DeleteFile",
            "ShellExecute", "CoCreateInstance", "DispatcherQueue", "std::thread",
            "std::filesystem", "GetDriveType", "RegSetValue", "SetFileInformation",
        ):
            self.assertNotIn(forbidden, HEADER)

    def test_native_scenarios_exist(self):
        for case in ("C:relative", "server", "한글 폴더", "NUL.txt", "lPt9.txt",
                     "folder\\\\..", "overflow", "RequestIdentity{1,3,42,9}",
                     "F04_TREE_PATH_NATIVE_PASS"):
            self.assertIn(case, NATIVE)


if __name__ == "__main__":
    unittest.main()
