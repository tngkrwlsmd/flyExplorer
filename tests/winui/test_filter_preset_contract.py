"""Persistent pane filter preset source contracts."""
from pathlib import Path
import unittest
import re

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

    def test_visual_style_persistence_and_row_classification(self):
        h=read("src/base/filter_rule_store.h")
        cpp=read("src/base/filter_rule_store.cpp")
        xaml=read("app/winui/MainWindow.xaml")
        app=read("app/winui/MainWindow.xaml.cpp")
        features=read("app/winui/filter_rule_features.cpp")
        for token in ('kMaxColor = 4','kMaxIcon = 4','schema=2',
                      'schema=1','item.color,item.icon','colorText.size()!=1'):
            self.assertIn(token,h+cpp)
        for name in ("FilterRuleColorBox","FilterRuleIconBox"):
            self.assertIn('x:Name="'+name+'"',xaml)
            self.assertIn(name+"().SelectedIndex(",features)
        self.assertIn("fxfile::filterrules::Store::matches(itemLabel,rule.masks)",app)
        self.assertIn("필터 분류 아이콘",app)
        self.assertIn("FillFiles(0);FillFiles(1)",features)

    def test_light_theme_filename_accent_contrast(self):
        app=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn("RootShell().ActualTheme()==ElementTheme::Light",app)
        matches=re.findall(
            r"case ([1-4]):value=light\?Windows::UI::Color\{255,(\d+),(\d+),(\d+)\}",
            app)
        self.assertEqual(len(matches),4,"expected four real light-theme colors")
        self.assertEqual({int(x[0]) for x in matches},{1,2,3,4})
        def channel(x):
            c=int(x)/255
            return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
        for style,r,g,b in matches:
            lum=.2126*channel(r)+.7152*channel(g)+.0722*channel(b)
            self.assertGreaterEqual((1.05)/(lum+.05),4.5,
                                    "light-theme style "+style)

    def test_screen_reader_ui_a_rule_color_icon_semantics(self):
        app=read("app/winui/MainWindow.xaml.cpp")
        xaml=read("app/winui/MainWindow.xaml")
        self.assertIn("kFilterColors",app)
        self.assertIn("kFilterIcons",app)
        for token in ("필터 프리셋: ", "분류 색상: ", "분류 아이콘: ",
                      "필터 분류 아이콘: "):
            self.assertIn(token,app)
        self.assertIn("SetName(\\n                row,hstring(label))".replace("\\n","\\n"),app)
        self.assertIn('AutomationProperties.Name="필터 규칙 분류 색상"',xaml)
        self.assertIn('AutomationProperties.Name="필터 규칙 분류 아이콘"',xaml)

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
