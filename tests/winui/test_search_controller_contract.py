"""Current search ownership, query validation, content and preset contracts."""
from pathlib import Path
import unittest

R = Path(__file__).resolve().parents[2]


def src(path):
    return (R / path).read_text(encoding="utf-8-sig")


class SearchControllerContracts(unittest.TestCase):
    def test_f11_search_result_location_is_scoped_and_nonmutating(self):
        xaml=src("app/winui/MainWindow.xaml")
        header=src("app/winui/MainWindow.xaml.h")
        feature=src("app/winui/m19_features.cpp")
        controller=src("app/winui/search_controller.h")
        for token in ('SelectionChanged="OnSearchMatchSelectionChanged"',
                      'Click="OnLocateSearchMatch"', 'IsEnabled="False"',
                      '선택한 결과의 폴더로 이동'):
            self.assertIn(token,xaml)
        for token in ("mSearchResultContext", "mSearchResultPaths",
                      "mSearchResultValid", "SelectedSearchMatchPath()"):
            self.assertIn(token,header)
        self.assertIn("static bool sameContext(Context const&,Context const&) noexcept;",controller)
        selection=feature.split("std::wstring MainWindow::SelectedSearchMatchPath()",1)[1].split(
            "void MainWindow::OnSelectSearchRecent(",1)[0]
        for token in ("SearchController::sameContext(",
                      "mSearchResultContext,SearchContext()", "SelectedIndex()",
                      "SelectedItem().try_as<TextBlock>()",
                      "mSearchResultPaths[static_cast<std::size_t>(index)]",
                      "selected.is_absolute()", "selected.parent_path()",
                      "selected.lexically_normal()!=selected",
                      "QueuePath(mSearchResultContext.side,",
                      "SearchPanel().Visibility(Visibility::Collapsed)"):
            self.assertIn(token,selection)
        self.assertNotIn("ShellExecute",selection)
        self.assertNotIn("CreateProcess",selection)
        self.assertIn("mSearchResultPaths=completion.result.matches;",feature)
        self.assertIn("mSearchResultContext=completion.context;",feature)
        self.assertIn("mSearchResultValid=false;",feature)
        self.assertIn("mSearchController.invalidate();",feature)

    def test_controller_owns_lifecycle_and_close_invalidation(self):
        project = src("app/winui/flyExplorer.project-template.xml")
        header = src("app/winui/MainWindow.xaml.h")
        controller = src("app/winui/search_controller.cpp")
        controller_h = src("app/winui/search_controller.h")
        main = src("app/winui/MainWindow.xaml.cpp")
        self.assertIn("search_controller.cpp", project)
        self.assertIn("SearchController mSearchController", header)
        for old in ("mSearchCancel", "mSearchEpoch", "mRecentScopes", "mRecentEdited"):
            self.assertNotIn(old, header)
        for token in (
            "state_->epoch",
            "state_->cancel",
            "ticket=++state_->epoch",
            "completion.ticket!=state_->epoch",
            "state_->closing=true",
            "prepareForClose",
        ):
            self.assertIn(token, controller + controller_h)
        self.assertIn("mSearchController.prepareForClose()", main)

    def test_context_and_recent_state_reject_stale_results(self):
        controller = src("app/winui/search_controller.cpp")
        features = src("app/winui/m19_features.cpp")
        main = src("app/winui/MainWindow.xaml.cpp")
        for field in ("windowIdentity", "side", "tab", "route", "paneFolder", "scope"):
            self.assertIn("a." + field + "==b." + field, controller)
        for token in (
            "sameSearchQuery(a.query,b.query)",
            "readRecentScopes(loaded)",
            "rememberScope(",
            "writeRecentScopes(persist)",
            "recentRevision",
        ):
            self.assertIn(token, controller)
        self.assertIn("mSearchController.accept(", features)
        self.assertIn("Disposition::StaleContext", features)
        self.assertIn("mSearchController.invalidate()", main)

    def test_query_options_keep_bounded_prethread_validation(self):
        header = src("app/winui/m19_search.h")
        search = src("app/winui/m19_search.cpp")
        controller = src("app/winui/search_controller.cpp")
        for token in (
            "SearchEntryKind",
            "InvalidRegex",
            "kMaxWalk=20000",
            "kMaxDepth=32",
            "kMaxResults=1000",
            "resultLimited",
            "traversalLimited",
            "visited",
            "kMaxExtension=32",
            "std::regex_search",
            "FILE_ATTRIBUTE_REPARSE_POINT",
            "minSizeKb",
            "maxSizeKb",
            "modifiedAfter",
            "modifiedBefore",
            "InvalidSizeRange",
            "InvalidDateRange",
        ):
            self.assertIn(token, header + search + controller)
        start = controller.index("SearchController::StartStatus SearchController::start")
        self.assertLess(
            controller.index("validateRequest(request)", start),
            controller.index("std::thread", start),
        )

    def test_search_scale_separates_traversal_and_display_limits(self):
        header = src("app/winui/m19_search.h")
        search = src("app/winui/m19_search.cpp")
        features = src("app/winui/m19_features.cpp")
        native = src("tests/winui/m19/m19_native_fixture.cpp")
        for token in (
            "kMaxWalk=20000",
            "kMaxDepth=32",
            "kMaxResults=1000",
            "out.visited=walked",
            "out.resultLimited=true",
            "out.traversalLimited=true",
            "SEARCH_SCALE_BEYOND_2500_WALK_AND_100_RESULTS",
            "SEARCH_SCALE_DEPTH_BEYOND_FIVE",
        ):
            self.assertIn(token, header + search + native)
        self.assertIn("처음 ", features)
        self.assertIn("탐색 한도 도달(", features)
        self.assertNotIn("개(제한된 일부 결과)", features)

    def test_content_search_is_bounded_regex_encoding_and_cancellable(self):
        header = src("app/winui/m19_search.h")
        search = src("app/winui/m19_search.cpp")
        bounded = src("src/base/bounded_regex.cpp")
        for token in (
            "contentTerm",
            "contentRegex",
            "InvalidContentTerm",
            "InvalidContentRegex",
            "contentLimited",
            "contentRegexLimited",
            "kMaxContentFileBytes=1024ull*1024ull",
            "kMaxContentSearchBytes=16ull*1024ull*1024ull",
            "kContentChunkBytes=64*1024",
            "enum class SearchContentEncoding",
            "AutoUtf",
            "Korean949",
            "Windows1252",
            "MB_ERR_INVALID_CHARS",
            "FILE_FLAG_OPEN_REPARSE_POINT",
            "if(cancel&&cancel->load())",
            "fxfile::boundedregex::Pattern",
            "kMaxMatchSteps=4ull*1024ull*1024ull",
            "StateKind::Split",
            "CompileResult::Unsupported",
        ):
            self.assertIn(token, header + search + bounded)
        self.assertNotIn("std::wregex", bounded)
        self.assertNotIn("std::regex", bounded)
        self.assertEqual(0, bounded.count("std::thread"))

    def test_content_encoding_prefers_bom_before_explicit_fallback(self):
        search = src("app/winui/m19_search.cpp")
        self.assertIn("return decodeCodePage(949", search)
        self.assertIn("return decodeCodePage(1252", search)
        self.assertLess(
            search.index("bytes[0]==0xff&&bytes[1]==0xfe"),
            search.index("switch(encoding)"),
        )

    def test_search_presets_are_bounded_atomic_and_backward_compatible(self):
        header = src("src/base/search_preset_store.h")
        store = src("src/base/search_preset_store.cpp")
        for token in (
            "kMaxItems=20",
            "search-presets-v1.txt",
            "MOVEFILE_REPLACE_EXISTING",
            "MOVEFILE_WRITE_THROUGH",
            "FILE_ATTRIBUTE_REPARSE_POINT",
            "std::wstring contentTerm",
            "int contentEncoding=0",
            'line==L"schema=1"',
            'line==L"schema=2"',
            'line==L"schema=3"',
            'line==L"schema=4"',
            "bool contentRegex=false",
            'std::wstring text=L"schema=4\\r\\n"',
        ):
            self.assertIn(token, header + store)
        self.assertNotIn("APPDATA\\fxfile", store)
        self.assertNotIn("scope", header)

    def test_native_and_owned_gui_cover_compound_content_and_encoding_behavior(self):
        native = src("tests/winui/m19/m19_native_fixture.cpp")
        gui = src("tests/winui/test_m19_winui_features.py")
        for marker in (
            "INVALID_SIZE_RANGE_REJECTED",
            "INVALID_DATE_SYNTAX_REJECTED",
            "CONTENT_TOTAL_IO_BUDGET_16MIB",
            "EXPLICIT_CP949_CONTENT_MATCH",
            "EXPLICIT_WINDOWS1252_CONTENT_MATCH",
            "BOM_OVERRIDES_EXPLICIT_FALLBACK_ENCODING",
            "CONTENT_REGEX_GROUP_ALTERNATION_MATCH",
            "CONTENT_REGEX_UNSUPPORTED_LOOKAROUND_REJECTED",
            "CONTENT_REGEX_ADVERSARIAL_STEP_BUDGET",
            "SEARCH_PRESET_SCHEMA1_BACKWARD_COMPAT",
            "SEARCH_PRESET_SCHEMA2_BACKWARD_COMPAT",
            "SEARCH_PRESET_SCHEMA3_BACKWARD_COMPAT",
        ):
            self.assertIn(marker, native)
        for marker in (
            "REAL_SEARCH_V2_INVALID_REGEX_PRESTART_REJECT_PASS",
            "REAL_CONTENT_SEARCH_PRESET_RESTART_PASS",
            "REAL_CONTENT_REGEX_GROUP_ALTERNATION_PASS",
            "REAL_CONTENT_REGEX_INVALID_PRESTART_REJECT_PASS",
            "REAL_CONTENT_REGEX_PRESET_RESTART_PASS",
            "REAL_CONTENT_ENCODING_CP949_PASS",
            "REAL_CONTENT_ENCODING_WINDOWS1252_PASS",
        ):
            self.assertIn(marker, gui)


if __name__ == "__main__":
    unittest.main()
