"""Preferences coordinator ownership and async persistence contracts."""
from pathlib import Path
import unittest

R=Path(__file__).resolve().parents[2]
A=R/"app/winui"

def text(name):
    return (A/name).read_text(encoding="utf-8-sig")

class PreferencesCoordinatorContract(unittest.TestCase):
    def test_coordinator_owns_preferences_revision_and_write_serialization(self):
        header=text("preferences_coordinator.h")
        impl=text("preferences_coordinator.cpp")
        window=text("MainWindow.xaml.h")
        main=text("MainWindow.xaml.cpp")
        surface=text("m20_shell.cpp")
        for token in ("Preferences preferences_","writeMutex_","revision_",
                      "setTheme(","setDefaultViewMode(","persist("):
            self.assertIn(token,header)
        self.assertNotIn("Microsoft::UI::Xaml",header)
        self.assertNotIn("DispatcherQueue",header)
        for token in ("std::thread(","std::lock_guard<std::mutex>",
                      "ticket!=revision->load()","fxfile::uisettings::save(snapshot)"):
            self.assertIn(token,impl)
        for forbidden in ("mPreferencesWriteMutex","mPreferencesRevision",
                          "fxfile::uisettings::Preferences mPreferences"):
            self.assertNotIn(forbidden,window)
        self.assertIn("mPreferencesCoordinator.load()",main)
        self.assertIn("mPreferencesCoordinator.current()",main)
        self.assertIn("mPreferencesCoordinator.persist(",surface)
        self.assertIn("mPreferencesCoordinator.setTheme(chosen)",surface)
        self.assertIn("mPreferencesCoordinator.setDefaultViewMode(selection)",surface)
        self.assertNotIn("std::thread(",surface)

    def test_project_registers_coordinator(self):
        project=text("flyExplorer.project-template.xml")
        self.assertIn('ClInclude Include="preferences_coordinator.h"',project)
        self.assertIn('ClCompile Include="preferences_coordinator.cpp"',project)

    def test_private_preferences_store_is_korean_default_atomic_and_legacy_isolated(self):
        body=(R/"src/base/ui_preferences.cpp").read_text(encoding="utf-8-sig")
        header=(R/"src/base/ui_preferences.h").read_text(encoding="utf-8-sig")
        for token in ("flyExplorer","ui-preferences-v1.txt","ko-KR",
                      "GetTempFileNameW","MOVEFILE_WRITE_THROUGH",
                      "MOVEFILE_REPLACE_EXISTING"):
            self.assertIn(token,body+header)
        self.assertNotIn("fxfile\\\\conf",body+header)
        self.assertIn("schema=3", body)
        self.assertIn("schema=2", body)
        self.assertIn("validFocusShortcuts(pref.addressShortcut,pref.searchShortcut)", body)

if __name__=="__main__":
    unittest.main()
