"""R18 Explorer-compatible Alt+Shift+P Details shortcut; source-only scope."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class R18DetailsShortcut(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "app/winui/MainWindow.xaml.cpp").read_text(
            encoding="utf-8-sig"
        )
        cls.keys = cls.source.split("RootShell().PreviewKeyDown(", 1)[1].split(
            "// Closed set of Ctrl-only non-mutating focus shortcuts.", 1
        )[0]

    def test_details_alias_is_explorer_alt_shift_p_not_preview(self):
        keys = self.keys
        self.assertIn(
            "const bool detailsAlias=alt&&!control&&shift&&\n"
            "                    key==Windows::System::VirtualKey::P;",
            keys,
        )
        self.assertIn(
            "const bool previewAlias=alt&&!control&&!shift&&\n"
            "                    key==Windows::System::VirtualKey::P;",
            keys,
        )
        self.assertIn("||previewAlias||detailsAlias||windowAlias", keys)
        self.assertIn(
            "refreshAlias||viewShortcut>=0||previewAlias||detailsAlias", keys
        )

    def test_details_toggles_once_without_implicit_preview(self):
        detail = self.keys.split("if(detailsAlias){", 1)[1].split(
            "if(previewAlias){", 1
        )[0]
        self.assertIn("if(!args.KeyStatus().WasKeyDown)", detail)
        self.assertIn("ui->OnToggleFileInfoPane(nullptr,nullptr);", detail)
        self.assertIn("args.Handled(true);", detail)
        self.assertIn("return;", detail)
        self.assertNotIn("OnRevealTextPreview", detail)
        self.assertNotIn("UpdateLayout", detail)
        self.assertNotIn(".Focus(", detail)
        self.assertNotIn("QueueTextPreview", detail)
        self.assertIn("ui->mFileOperations.pendingConfirmationToken()", self.keys)
        self.assertIn("node.try_as<MenuFlyoutPresenter>()", self.keys)
        self.assertIn("node.try_as<ContentDialog>()", self.keys)

    def test_existing_alt_p_preview_keeps_explicit_focus_policy(self):
        preview = self.keys.split("if(previewAlias){", 1)[1]
        self.assertIn("ui->OnToggleFileInfoPane(nullptr,nullptr);", preview)
        self.assertIn("ui->OnRevealTextPreview(nullptr,nullptr);", preview)
        self.assertIn("view.Focus(Microsoft::UI::Xaml::FocusState::Keyboard);", preview)


if __name__ == "__main__":
    unittest.main()
