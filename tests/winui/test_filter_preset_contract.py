"""Persistent pane filter preset source contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class FilterPresetContracts(unittest.TestCase):
    def test_private_bounded_atomic_store(self):
        h=read("src/base/filter_rule_store.h")
        cpp=read("src/base/filter_rule_store.cpp")
        for token in (
            "kMaxItems = 20","kMaxName = 56","kMaxMasks = 260",
            "filter-rules-v1.txt","MOVEFILE_REPLACE_EXISTING",
            "MOVEFILE_WRITE_THROUGH","FILE_ATTRIBUTE_REPARSE_POINT",
        ):
            self.assertIn(token,h+cpp)
        self.assertNotIn("FileFilter.item",cpp)
        self.assertIn('GetEnvironmentVariableW(\n        L"LOCALAPPDATA"',cpp)

    def test_filter_keeps_substring_and_adds_bounded_masks(self):
        cpp=read("src/base/filter_rule_store.cpp")
        app=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn('expression.find_first_of(L"*?;")',cpp)
        self.assertIn("wildcardMatch",cpp)
        self.assertIn("std::search(filename.begin()",cpp)
        self.assertIn("fxfile::filterrules::Store::matches(",app)
        self.assertNotIn("std::search(label.begin()",app)

    def test_manager_is_user_visible_and_panel_exclusive(self):
        xaml=read("app/winui/MainWindow.xaml")
        features=read("app/winui/filter_rule_features.cpp")
        m19=read("app/winui/m19_features.cpp")
        bookmarks=read("app/winui/bookmark_features.cpp")
        for key in (
            "FilterRulePanelButton","FilterRulePanel","FilterRuleManagerBox",
            "FilterRuleNameEdit","FilterRuleMasksEdit","FilterRuleSaveButton",
            "FilterRuleApplyButton","FilterRuleDeleteButton",
        ):
            self.assertIn('x:Name="'+key+'"',xaml)
        self.assertIn("OnToggleFilterRules",features)
        self.assertIn("FilterRulePanel().Visibility(Visibility::Collapsed)",m19)
        self.assertIn("FilterRulePanel().Visibility(Visibility::Collapsed)",bookmarks)

    def test_project_and_native_fixture_include_store(self):
        project=read("app/winui/flyExplorer.project-template.xml")
        native=read("tests/winui/m20/m20_native_fixture.cpp")
        m20=read("tests/winui/m20/FlyM20StateContracts.project-template.xml")
        for token in ("filter_rule_store.h","filter_rule_store.cpp"):
            self.assertIn(token,project)
            self.assertIn(token,m20)
        for marker in (
            "filter_rule_literal_substring_compat",
            "filter_rule_wildcard_set_case_insensitive",
            "filter_rule_atomic_save_reload",
            "filter_rule_bounded_20_items",
        ):
            self.assertIn(marker,native)

if __name__=="__main__":
    unittest.main()
