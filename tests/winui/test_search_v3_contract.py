"""Search v3 bounded compound-criteria and saved-preset contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class SearchV3Contracts(unittest.TestCase):
    def test_query_adds_bounded_size_and_local_date_ranges(self):
        h=read("app/winui/m19_search.h")
        cpp=read("app/winui/m19_search.cpp")
        for token in (
            "minSizeKb","maxSizeKb","modifiedAfter","modifiedBefore",
            "InvalidSizeRange","InvalidDateRange","parseOptionalSizeKb",
            "parseDate","localDateKey","criteriaMatch",
            "kMaxWalk=2500","kMaxDepth=5","kMaxResults=100",
        ):
            self.assertIn(token,h+cpp)
        self.assertIn("if((hasMin||hasMax)&&folderEntry)return false",cpp)

    def test_controller_rejects_invalid_ranges_before_worker_start(self):
        cpp=read("app/winui/search_controller.cpp")
        h=read("app/winui/search_controller.h")
        for token in ("InvalidSizeRange","InvalidDateRange"):
            self.assertIn(token,h+cpp)
        start=cpp.index("SearchController::StartStatus SearchController::start")
        self.assertLess(cpp.index("validateRequest(request)",start),
                        cpp.index("std::thread",start))

    def test_private_saved_query_store_is_bounded_and_atomic(self):
        h=read("src/base/search_preset_store.h")
        cpp=read("src/base/search_preset_store.cpp")
        for token in (
            "kMaxItems=20","search-presets-v1.txt","LOCALAPPDATA",
            "MOVEFILE_REPLACE_EXISTING","MOVEFILE_WRITE_THROUGH",
            "FILE_ATTRIBUTE_REPARSE_POINT",
        ):
            self.assertIn(token,h+cpp)
        self.assertNotIn("APPDATA\\fxfile",cpp)

    def test_saved_preset_does_not_include_scope(self):
        h=read("src/base/search_preset_store.h")
        self.assertNotIn("scope",h)
        self.assertIn("std::wstring term",h)
        self.assertIn("std::wstring minSizeKb",h)
        self.assertIn("std::wstring modifiedAfter",h)

    def test_winui_exposes_compound_criteria_and_saved_sets(self):
        xaml=read("app/winui/MainWindow.xaml")
        features=read("app/winui/search_preset_features.cpp")
        for key in (
            "SearchMinSizeBox","SearchMaxSizeBox",
            "SearchModifiedAfterBox","SearchModifiedBeforeBox",
            "SearchPresetBox","SearchPresetNameBox","SearchPresetSaveButton",
            "SearchPresetApplyButton","SearchPresetDeleteButton",
        ):
            self.assertIn('x:Name="'+key+'"',xaml)
        for token in (
            "InitializeSearchPresets","OnSaveSearchPreset",
            "OnApplySearchPreset","OnDeleteSearchPreset",
            "validateSearchQuery",
        ):
            self.assertIn(token,features)

    def test_native_fixture_covers_compound_and_persistence(self):
        native=read("tests/winui/m19/m19_native_fixture.cpp")
        for marker in (
            "SIZE_ONLY_QUERY_WITH_EMPTY_TERM",
            "LOCAL_MODIFIED_DATE_RANGE",
            "NAME_EXTENSION_SIZE_DATE_AND_QUERY",
            "INVALID_SIZE_RANGE_REJECTED",
            "INVALID_DATE_SYNTAX_REJECTED",
            "SEARCH_PRESET_ATOMIC_RESTART_PERSISTENCE",
        ):
            self.assertIn(marker,native)

if __name__=="__main__":
    unittest.main()
