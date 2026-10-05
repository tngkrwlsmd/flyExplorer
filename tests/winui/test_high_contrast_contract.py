"""Static contract for High Contrast-adaptive WinUI opacity resources."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui"

EXPECTED_DEFAULTS = {
    "FlyExplorerCaptionOpacity": "0.82",
    "FlyExplorerSecondaryCommandOpacity": "0.76",
    "FlyExplorerSecondaryTextOpacity": "0.75",
    "FlyExplorerSelectionTextOpacity": "0.72",
    "FlyExplorerStatusTextOpacity": "0.68",
    "FlyExplorerSubtleTextOpacity": "0.65",
    "FlyExplorerSidebarHeadingOpacity": "0.62",
    "FlyExplorerColumnSeparatorOpacity": "0.55",
    "FlyExplorerPaneDividerOpacity": "0.42",
    "FlyExplorerToolbarSeparatorOpacity": "0.32",
    "FlyExplorerHeaderSeparatorOpacity": "0.20",
}

X = "{http://schemas.microsoft.com/winfx/2006/xaml}"
P = "{http://schemas.microsoft.com/winfx/2006/xaml/presentation}"


class HighContrastContract(unittest.TestCase):
    def test_theme_dictionary_promotes_muted_opacity_to_full_contrast(self):
        root = ET.parse(APP / "App.xaml").getroot()
        dictionaries = root.findall(
            ".//" + P + "ResourceDictionary.ThemeDictionaries/" + P + "ResourceDictionary"
        )
        by_key = {d.attrib.get(X + "Key"): d for d in dictionaries}
        self.assertIn("Default", by_key)
        self.assertIn("HighContrast", by_key)

        def values(dictionary):
            return {
                child.attrib[X + "Key"]: (child.text or "").strip()
                for child in dictionary
                if X + "Key" in child.attrib
            }

        default = values(by_key["Default"])
        high = values(by_key["HighContrast"])
        self.assertEqual(EXPECTED_DEFAULTS, default)
        self.assertEqual(set(EXPECTED_DEFAULTS), set(high))
        self.assertTrue(all(value == "1.0" for value in high.values()))

    def test_user_visible_fractional_opacity_uses_theme_resources(self):
        literal_attribute = re.compile(r'Opacity="(0\.[0-9]+)"')
        literal_setter = re.compile(
            r'<Setter\s+Property="Opacity"\s+Value="(0\.[0-9]+)"'
        )
        failures = []
        for path in sorted(APP.glob("*.xaml")):
            text = path.read_text(encoding="utf-8")
            for regex in (literal_attribute, literal_setter):
                for match in regex.finditer(text):
                    value = float(match.group(1))
                    # 0 / 0.01 are hidden automation-compat controls, not
                    # visible muted content. Everything visible must adapt.
                    if value > 0.01:
                        line = text.count("\n", 0, match.start()) + 1
                        failures.append(f"{path.name}:{line}: {match.group(0)}")
        self.assertEqual([], failures, "\n".join(failures))

    def test_owned_high_contrast_gui_never_mutates_global_accessibility_state(self):
        body=(APP.parent.parent/"tests"/"winui"/"test_high_contrast_gui.py").read_text(
            encoding="utf-8"
        )
        for token in (
            "HIGH_CONTRAST_ON_REQUIRED",
            "SystemParametersInfoW(0x0042",
            "OWNED_HIGH_CONTRAST_UIA_AND_SELECTION_PASS",
            "OWNED_HIGH_CONTRAST_SEARCH_SURFACE_PASS",
            "ORIGINAL_SIX_USER_SETTINGS_IDENTICAL",
            "ImageGrab.grab",
        ):
            self.assertIn(token,body)
        for forbidden in (
            "SPI_SETHIGHCONTRAST",
            "SystemParametersInfoW(0x0043",
            "ChangeDisplaySettingsEx",
            "winreg.SetValue",
        ):
            self.assertNotIn(forbidden,body)

    def test_high_contrast_search_acceptance_uses_exposed_control(self):
        body=(APP.parent.parent/"tests"/"winui"/"test_high_contrast_gui.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('auto_id="SearchScopeBox"', body)
        self.assertNotIn('auto_id="SearchPanel").exists', body)

    def test_expected_ui_surfaces_consume_high_contrast_resources(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(APP.glob("*.xaml"))
        )
        for key in EXPECTED_DEFAULTS:
            self.assertGreaterEqual(
                combined.count("{ThemeResource " + key + "}"),
                1,
                key,
            )
        for brush in (
            "SystemControlForegroundBaseLowBrush",
            "SystemControlHighlightAccentBrush",
        ):
            source = combined + (APP / "NavigationSidebar.xaml.cpp").read_text(
                encoding="utf-8"
            )
            self.assertIn(brush, source)


if __name__ == "__main__":
    unittest.main()
