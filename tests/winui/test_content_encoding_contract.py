"""Explicit legacy content-encoding contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class ContentEncodingContracts(unittest.TestCase):
    def test_query_has_bounded_explicit_encoding_enum(self):
        h=read("app/winui/m19_search.h")
        cpp=read("app/winui/m19_search.cpp")
        for token in (
            "enum class SearchContentEncoding",
            "AutoUtf","Korean949","Windows1252",
            "InvalidContentEncoding",
            "contentEncoding=SearchContentEncoding::AutoUtf",
        ):
            self.assertIn(token,h+cpp)

    def test_bom_is_checked_before_explicit_fallback_codepage(self):
        cpp=read("app/winui/m19_search.cpp")
        self.assertIn("decodeCodePage(",cpp)
        self.assertIn("case SearchContentEncoding::Korean949",cpp)
        self.assertIn("return decodeCodePage(949",cpp)
        self.assertIn("return decodeCodePage(1252",cpp)
        bom=cpp.index("bytes[0]==0xff&&bytes[1]==0xfe")
        switch=cpp.index("switch(encoding)")
        self.assertLess(bom,switch)

    def test_ui_and_controller_map_only_three_known_encoding_choices(self):
        xaml=read("app/winui/MainWindow.xaml")
        features=read("app/winui/m19_features.cpp")
        controller_h=read("app/winui/search_controller.h")
        controller_cpp=read("app/winui/search_controller.cpp")
        self.assertIn('x:Name="SearchContentEncodingBox"',xaml)
        for label in ("자동 UTF","한국어 CP949","서유럽 Windows-1252"):
            self.assertIn(label,xaml)
        self.assertIn("SearchContentEncoding::Korean949",features)
        self.assertIn("SearchContentEncoding::Windows1252",features)
        self.assertIn("SearchContentEncoding::AutoUtf",features)
        self.assertIn("InvalidContentEncoding",controller_h+controller_cpp)

    def test_saved_presets_write_schema3_and_read_schema1_2_3(self):
        h=read("src/base/search_preset_store.h")
        cpp=read("src/base/search_preset_store.cpp")
        self.assertIn("int contentEncoding=0",h)
        for token in ('line==L"schema=1"','line==L"schema=2"',
                      'line==L"schema=3"',
                      'std::wstring text=L"schema=3\\r\\n"'):
            self.assertIn(token,cpp)
        self.assertIn("p.contentEncoding<0||p.contentEncoding>2",cpp)

    def test_native_fixture_covers_explicit_codepages_and_compatibility(self):
        native=read("tests/winui/m19/m19_native_fixture.cpp")
        for marker in (
            "AUTO_UTF_REJECTS_CP949",
            "EXPLICIT_CP949_CONTENT_MATCH",
            "AUTO_UTF_REJECTS_WINDOWS1252",
            "EXPLICIT_WINDOWS1252_CONTENT_MATCH",
            "BOM_OVERRIDES_EXPLICIT_FALLBACK_ENCODING",
            "INVALID_CONTENT_ENCODING_REJECTED",
            "SEARCH_PRESET_CONTENT_ENCODING_SCHEMA3_RESTART",
            "SEARCH_PRESET_SCHEMA2_BACKWARD_COMPAT",
        ):
            self.assertIn(marker,native)

    def test_owned_gui_executes_both_legacy_codepages_and_restart(self):
        gui=read("tests/winui/test_m19_winui_features.py")
        shell=read("tests/winui/test_shell_gui.py")
        for marker in (
            "REAL_CONTENT_ENCODING_AUTO_UTF_REJECTS_CP949_PASS",
            "REAL_CONTENT_ENCODING_CP949_PASS",
            "REAL_CONTENT_ENCODING_WINDOWS1252_PASS",
            "REAL_CONTENT_ENCODING_AUTO_UTF_RESTORE_PASS",
            "REAL_CONTENT_ENCODING_PRESET_RESTART_PASS",
        ):
            self.assertIn(marker,gui)
        self.assertIn("FLY_M19_OWNED_FEATURES_ONLY",shell)
        self.assertIn("M19_FOCUSED_GUI_PASS",shell)

if __name__=="__main__":
    unittest.main()
