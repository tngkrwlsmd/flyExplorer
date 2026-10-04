"""Bounded literal text content-search contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class ContentSearchContracts(unittest.TestCase):
    def test_query_and_results_expose_bounded_content_state(self):
        h=read("app/winui/m19_search.h")
        cpp=read("app/winui/m19_search.cpp")
        for token in (
            "contentTerm","InvalidContentTerm","contentLimited",
            "contentFilesScanned","contentFilesSkipped","contentBytesRead",
            "kMaxContentFileBytes=1024ull*1024ull",
            "kMaxContentSearchBytes=16ull*1024ull*1024ull",
            "kContentChunkBytes=64*1024",
        ):
            self.assertIn(token,h+cpp)

    def test_content_reader_is_literal_text_only_and_encoding_bounded(self):
        cpp=read("app/winui/m19_search.cpp")
        for token in (
            "MB_ERR_INVALID_CHARS","0xff&&bytes[1]==0xfe",
            "0xfe&&bytes[1]==0xff","0xef&&bytes[1]==0xbb&&bytes[2]==0xbf",
            "FILE_FLAG_OPEN_REPARSE_POINT","FILE_ATTRIBUTE_REPARSE_POINT",
            "literalMatches(text,term,caseSensitive)",
        ):
            self.assertIn(token,cpp)
        self.assertNotIn("std::wregex content",cpp)

    def test_cancellation_and_total_io_budget_are_inside_existing_worker(self):
        cpp=read("app/winui/m19_search.cpp")
        self.assertIn("if(cancel&&cancel->load())",cpp)
        self.assertIn("ContentMatch::BudgetExceeded",cpp)
        self.assertIn("out.contentLimited=true",cpp)
        self.assertIn("out.truncated=true",cpp)
        self.assertEqual(cpp.count("std::thread"),0)

    def test_controller_rejects_folder_only_content_before_thread_start(self):
        h=read("app/winui/search_controller.h")
        cpp=read("app/winui/search_controller.cpp")
        core=read("app/winui/m19_search.cpp")
        self.assertIn("InvalidContentTerm",h+cpp+core)
        start=cpp.index("SearchController::StartStatus SearchController::start")
        self.assertLess(cpp.index("validateRequest(request)",start),
                        cpp.index("std::thread",start))

    def test_search_presets_migrate_schema1_and_persist_content_schema2(self):
        h=read("src/base/search_preset_store.h")
        cpp=read("src/base/search_preset_store.cpp")
        self.assertIn("std::wstring contentTerm",h)
        self.assertIn('line==L"schema=1"',cpp)
        self.assertIn('line==L"schema=2"',cpp)
        self.assertIn('std::wstring text=L"schema=2\\r\\n"',cpp)

    def test_winui_and_owned_gui_include_content_criterion(self):
        xaml=read("app/winui/MainWindow.xaml")
        features=read("app/winui/m19_features.cpp")
        presets=read("app/winui/search_preset_features.cpp")
        gui=read("tests/winui/test_m19_winui_features.py")
        self.assertIn('x:Name="SearchContentBox"',xaml)
        self.assertIn("contentTerm=std::wstring(SearchContentBox().Text().c_str())",features)
        self.assertIn("p.contentTerm=std::wstring(SearchContentBox().Text().c_str())",presets)
        for marker in (
            "REAL_CONTENT_SEARCH_UTF8_LITERAL_PASS",
            "REAL_CONTENT_SEARCH_UTF16_PASS",
            "REAL_CONTENT_SEARCH_PRESET_RESTART_PASS",
        ):
            self.assertIn(marker,gui)

    def test_native_fixture_covers_encoding_binary_budget_and_migration(self):
        native=read("tests/winui/m19/m19_native_fixture.cpp")
        for marker in (
            "UTF8_CONTENT_CASE_INSENSITIVE_MATCH",
            "CONTENT_CASE_SENSITIVE_MATCH",
            "UTF16LE_BOM_CONTENT_MATCH",
            "UTF16BE_BOM_CONTENT_MATCH",
            "BINARY_NUL_CONTENT_SKIPPED",
            "CONTENT_FILE_OVER_1MIB_SKIPPED",
            "NAME_EXTENSION_CONTENT_AND_QUERY",
            "CONTENT_FOLDER_ONLY_REJECTED_BEFORE_SEARCH",
            "CONTENT_TOTAL_IO_BUDGET_16MIB",
            "SEARCH_PRESET_CONTENT_SCHEMA2_RESTART",
            "SEARCH_PRESET_SCHEMA1_BACKWARD_COMPAT",
        ):
            self.assertIn(marker,native)

if __name__=="__main__":
    unittest.main()
