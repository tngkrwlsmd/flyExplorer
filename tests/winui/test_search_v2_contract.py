"""Search v2 bounded regex/filter source contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class SearchV2Contracts(unittest.TestCase):
    def test_query_model_keeps_existing_bounds(self):
        header=read("app/winui/m19_search.h")
        body=read("app/winui/m19_search.cpp")
        for token in (
            "SearchEntryKind", "SearchQueryValidation", "InvalidRegex",
            "kMaxWalk=2500", "kMaxDepth=5", "kMaxResults=100",
            "kMaxExtension=32", "std::regex_search",
            "FILE_ATTRIBUTE_REPARSE_POINT",
        ):
            self.assertIn(token,header+body)
        self.assertIn("SearchEntryKind::Files",header)

    def test_controller_rejects_bad_pattern_before_worker_start(self):
        controller=read("app/winui/search_controller.cpp")
        start=controller.index("SearchController::StartStatus SearchController::start")
        worker=controller.index("std::thread",start)
        validate=controller.index("validateRequest(request)",start)
        self.assertLess(validate,worker)
        self.assertIn("InvalidPattern",controller)
        self.assertIn("InvalidExtension",controller)

    def test_live_context_includes_every_search_option(self):
        features=read("app/winui/m19_features.cpp")
        controller=read("app/winui/search_controller.cpp")
        for token in (
            "SearchExtensionBox", "SearchRegexBox", "SearchCaseBox",
            "SearchTargetBox", "sameSearchQuery(a.query,b.query)",
        ):
            self.assertIn(token,features+controller)

    def test_winui_exposes_bounded_advanced_search_controls(self):
        xaml=read("app/winui/MainWindow.xaml")
        for key in (
            "SearchRegexBox","SearchCaseBox","SearchTargetBox",
            "SearchExtensionBox",
        ):
            self.assertIn('x:Name="'+key+'"',xaml)
        self.assertIn("깊이 5",xaml)
        self.assertIn("2,500개",xaml)
        self.assertIn("결과 100개",xaml)

    def test_existing_owned_m19_gui_covers_new_options(self):
        gui=read("tests/winui/test_m19_winui_features.py")
        for marker in (
            "REAL_SEARCH_V2_DEFAULT_FILE_LITERAL_3_PASS",
            "REAL_SEARCH_V2_REGEX_CASE_SENSITIVE_PASS",
            "REAL_SEARCH_V2_UNICODE_EXTENSION_PASS",
            "REAL_SEARCH_V2_FOLDER_ONLY_PASS",
            "REAL_SEARCH_V2_INVALID_REGEX_PRESTART_REJECT_PASS",
        ):
            self.assertIn(marker,gui)

if __name__=="__main__":
    unittest.main()
