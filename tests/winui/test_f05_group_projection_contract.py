"""F05 static acceptance: no implicit incomplete-model or OS side effects."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROJECTION = (ROOT / "app/winui/file_group_projection.h").read_text(encoding="utf-8")
PRESENTATION = (ROOT / "app/winui/file_group_presentation.h").read_text(encoding="utf-8")


class F05GroupProjectionContract(unittest.TestCase):
    def test_full_model_gate_and_identity(self):
        for name in ("indexComplete", "modelLimitReached", "expectedCount",
                     "visibleRoute", "visibleTab", "metadataReady",
                     "DuplicateIdentity", "UnsupportedItem",
                     "kMaximumIndexedItems=25000", "logicalItems",
                     "sourceCount=request.expectedCount", "result.side=request.side"):
            self.assertIn(name, PROJECTION)

    def test_collapse_scope_and_file_row_identity(self):
        for name in ("resetFor(", "route_==route", "tab_==tab",
                     "EntryKind::Heading", "EntryKind::File", "visibleFileRows",
                     "totalFileRows", "state.matches(request.route,request.tab,request.side)"):
            self.assertIn(name, PRESENTATION)
        self.assertIn("if(!projection.ready())", PRESENTATION)

    def test_no_os_io_or_mutation(self):
        for code in (PROJECTION, PRESENTATION):
            for forbidden in ("CreateFile", "DeleteFile", "ReadFile(",
                              "ShellExecute", "CoCreateInstance", "GetFileAttributes",
                              "DispatcherQueue", "std::thread", "std::filesystem"):
                self.assertNotIn(forbidden, code)

    def test_runner_scoped_to_ignored_output(self):
        runner = (ROOT / "tools/winui/run_f05_group_native.py").read_text(encoding="utf-8")
        self.assertIn('ROOT / "out/f05-native"', runner)
        self.assertIn('"/std:c++17"', runner)
        self.assertIn('"-std=c++17"', runner)
        self.assertIn("source.stem", runner)


if __name__ == "__main__":
    unittest.main()
