"""F5/F6 shortcut semantics must be non-mutating and Explorer-aligned."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WINDOW = ROOT / "app" / "winui" / "MainWindow.xaml.cpp"
TRANSFERS = ROOT / "app" / "winui" / "m22_transfers.cpp"


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class ShortcutSemanticsContract(unittest.TestCase):
    def test_number_shortcuts_use_existing_window_tabs_with_editor_and_bounds_guards(self):
        source = compact(WINDOW.read_text(encoding="utf-8"))
        root = source.split("RootShell().PreviewKeyDown(", 1)[1]
        self.assertIn("if(control&&!shift&&!alt&& key>=Windows::System::VirtualKey::Number1&& key<=Windows::System::VirtualKey::Number9)", root)
        self.assertLess(root.index("pendingConfirmationToken()"),
                        root.index("int windowTabShortcut="))
        guarded = root.split("if(addressAlias||", 1)[1].split(
            "// Closed set of Ctrl-only", 1)[0]
        self.assertIn("windowAlias||windowTabShortcut>=0||", guarded)
        command = guarded.split("if(windowTabShortcut>=0){", 1)[1].split(
            "if(windowAlias){", 1)[0]
        for token in ("index<ui->mWorkspace.count()",
                      "index!=ui->mWorkspace.activeIndex()",
                      "ui->ActivateWindowTab(index)", "ui->RefreshWindowTabs()",
                      "args.Handled(true)"):
            self.assertIn(token, command)
        for forbidden in ("CreateWindowTab(", "OpenFolder(", "QueuePidl(",
                          "PersistPreferences(", "Current()."):
            self.assertNotIn(forbidden, command)

    def test_backspace_is_file_list_local_history_without_new_navigation_logic(self):
        source = compact(TRANSFERS.read_text(encoding="utf-8"))
        handler = source.split("void MainWindow::HandleFileShortcut(", 1)[1]
        branch = handler.split(
            "if(!ctrl&&!shift&&!alt&&vk==Windows::System::VirtualKey::Back){", 1
        )[1].split("// Keyboard equivalent", 1)[0]
        self.assertIn("mClosing||mFileOperations.pendingConfirmationToken()", branch)
        self.assertLess(branch.index("pendingConfirmationToken()"),
                        branch.index("OnBackClicked(nullptr,nullptr)"))
        self.assertIn("args.Handled(true);return;", branch)
        for forbidden in ("QueuePidl(", "OpenFolder(", "RunTransfer(", "HistoryAction::Up"):
            self.assertNotIn(forbidden, branch)
        window = compact(WINDOW.read_text(encoding="utf-8"))
        root = window.split("RootShell().PreviewKeyDown(", 1)[1].split(
            "})); RefreshWindowTabs();", 1
        )[0]
        self.assertNotIn("VirtualKey::Back", root)

    def test_ctrl_d_recycles_only_from_file_list_with_existing_confirmation(self):
        source = compact(TRANSFERS.read_text(encoding="utf-8"))
        handler = source.split("void MainWindow::HandleFileShortcut(", 1)[1]
        alias = handler.split(
            "if(ctrl&&!shift&&!alt&&vk==Windows::System::VirtualKey::D){", 1
        )[1].split("if(vk==Windows::System::VirtualKey::F2)", 1)[0]
        self.assertIn("RunTransfer(fxfile::shelltransfer::Kind::Recycle)", alias)
        self.assertIn("args.Handled(true);return;", alias)
        self.assertNotIn("CreateFileW(", alias)
        self.assertNotIn("CopySelectedToWindowsClipboard(", alias)
        self.assertLess(handler.index("VirtualKey::D){"),
                        handler.index("VirtualKey::F2)"))
        self.assertIn("if(vk==Windows::System::VirtualKey::Delete){", handler)
        self.assertIn(
            "if(mFileOperations.pendingConfirmationToken()){",
            source.split("void MainWindow::RunTransfer(", 1)[1].split(
                "void MainWindow::", 1
            )[0],
        )
        root = compact(WINDOW.read_text(encoding="utf-8")).split(
            "RootShell().PreviewKeyDown(", 1
        )[1].split("})); RefreshWindowTabs();", 1)[0]
        self.assertNotIn("control&&!shift&&!alt&&key==Windows::System::VirtualKey::D", root)

    def test_alt_p_settles_changed_layout_before_focus_without_deferred_input(self):
        source = compact(WINDOW.read_text(encoding="utf-8"))
        command = source.split("if(previewAlias){", 1)[1].split("args.Handled(true);", 1)[0]
        self.assertLess(command.index("OnToggleFileInfoPane(nullptr,nullptr)"),
                        command.index("RootShell().UpdateLayout()"))
        self.assertLess(command.index("RootShell().UpdateLayout()"),
                        command.index("OnRevealTextPreview(nullptr,nullptr)"))
        self.assertEqual(command.count("UpdateLayout()"), 1)
        for token in ("TryEnqueue(", "std::thread", "QueueTextPreview(",
                      "mTextPreviewEnabled=", "Sleep("):
            self.assertNotIn(token, command)

    def test_f11_uses_window_state_and_ignores_held_key_repeats(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        self.assertIn('#include <winrt/Windows.UI.Core.h>', window)
        root = window.split("RootShell().PreviewKeyDown(", 1)[1]
        self.assertIn("windowAlias=!control&&!shift&&!alt&& key==Windows::System::VirtualKey::F11", root)
        self.assertLess(root.index("pendingConfirmationToken()"),
                        root.index("const bool windowAlias="))
        aliases = root.split("if(addressAlias||", 1)[1].split(
            "// Closed set of Ctrl-only", 1
        )[0]
        self.assertIn("previewAlias||windowAlias||", aliases)
        self.assertLess(aliases.index("GetParent(node)"),
                        aliases.index("if(windowAlias){"))
        command = aliases.split("if(windowAlias){", 1)[1].split(
            "if(previewAlias){", 1
        )[0]
        for token in ("ui->AppWindow().Presenter(). try_as<OverlappedPresenter>()",
                      "if(!presenter)return;", "if(!args.KeyStatus().WasKeyDown)",
                      "OverlappedPresenterState::Maximized", "presenter.Restore()",
                      "OverlappedPresenterState::Restored&& presenter.IsMaximizable()",
                      "presenter.Maximize()", "catch(winrt::hresult_error const&)",
                      "args.Handled(true)"):
            self.assertIn(token, command)
        self.assertLess(command.index("if(!args.KeyStatus().WasKeyDown)"),
                        command.index("presenter.Restore()"))
        for forbidden in ("SetPresenter(", "MoveAndResize(", "QueuePidl(",
                          "PersistPreferences(", "ActivateWindowTab(", "Focus("):
            self.assertNotIn(forbidden, command)

    def test_alt_p_reuses_preview_pane_without_bypassing_optin(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        root = window.split("RootShell().PreviewKeyDown(", 1)[1]
        self.assertIn("previewAlias=alt&&!control&&!shift&& key==Windows::System::VirtualKey::P", root)
        aliases = root.split("if(addressAlias||", 1)[1].split(
            "// Closed set of Ctrl-only", 1
        )[0]
        self.assertIn("refreshAlias||viewShortcut>=0||previewAlias||", aliases)
        self.assertLess(root.index("pendingConfirmationToken()"),
                        root.index("const bool previewAlias="))
        self.assertLess(aliases.index("GetParent(node)"),
                        aliases.index("if(previewAlias){"))
        handler = aliases.split("if(previewAlias){", 1)[1]
        for token in ("OnToggleFileInfoPane(nullptr,nullptr)",
                      "ActiveWindowTab().fileInfoPaneVisible",
                      "OnRevealTextPreview(nullptr,nullptr)",
                      "ActiveWindowTab().model.activePane",
                      "side==0?ui->LeftFiles():ui->RightFiles()",
                      "view.Focus(Microsoft::UI::Xaml::FocusState::Keyboard)",
                      "args.Handled(true)"):
            self.assertIn(token, handler)
        for forbidden in ("OnToggleTextPreview(", "mTextPreviewEnabled=",
                          "QueueTextPreview(", "ReadFile(", "PersistPreferences("):
            self.assertNotIn(forbidden, handler)
        close = window.split("void MainWindow::OnToggleFileInfoPane(", 1)[1].split(
            "void MainWindow::ApplyFileInfoPaneLayout()", 1
        )[0]
        self.assertIn("if(!state.fileInfoPaneVisible){ mTextPreviewEnabled=false; CancelTextPreview();", close)

    def test_ctrl_wheel_steps_existing_hovered_pane_view_owner(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        wheel = window.split(
            "using Microsoft::UI::Xaml::Input::PointerEventHandler;", 1
        )[1].split("RootShell().AddHandler(", 1)[0]
        for token in (
            "for(int side=0;side<2;++side)",
            "(::GetKeyState(VK_CONTROL)&0x8000)==0",
            "(::GetKeyState(VK_SHIFT)&0x8000)!=0",
            "(::GetKeyState(VK_MENU)&0x8000)!=0",
            "mFileOperations.pendingConfirmationToken()",
            "args.GetCurrentPoint(view). Properties().MouseWheelDelta()",
            "if(side!=ui->ActiveWindowTab().model.activePane) ui->ActivatePane(side)",
            "current+(delta>0?1:-1)",
            "(std::max)(0,(std::min)(4,",
            "if(next!=current)ui->UpdateView(next)",
            "args.Handled(true)",
        ):
            self.assertIn(token, wheel)
        for forbidden in (
            "PersistPreferences(", "pane.active=", "fileLists[side].viewMode=",
            "RunTransfer(", "OpenFolder(", "QueuePidl(", "std::thread",
        ):
            self.assertNotIn(forbidden, wheel)

    def test_view_shortcuts_match_supported_explorer_modes(self):
        window = WINDOW.read_text(encoding="utf-8")
        block = window.split("int viewShortcut=-1;", 1)[1].split(
            "if(addressAlias||", 1
        )[0]
        self.assertIn("if(control&&shift&&!alt)", block)
        bindings = dict(re.findall(
            r"case Windows::System::VirtualKey::Number(\d):\s*"
            r"viewShortcut=static_cast<int>\(FileViewMode::(\w+)\);break;",
            block,
        ))
        self.assertEqual(bindings, {
            "2": "LargeIcons", "3": "MediumIcons", "4": "SmallIcons",
            "5": "List", "6": "Details",
        })
        self.assertNotIn("NumberPad", block)
        self.assertNotIn("UpdateView(", block)

    def test_view_shortcuts_use_existing_owner_after_input_guards(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        root = window.split("RootShell().PreviewKeyDown(", 1)[1]
        aliases = root.split("if(addressAlias||", 1)[1].split(
            "// Closed set of Ctrl-only", 1
        )[0]
        self.assertIn("refreshAlias||viewShortcut>=0||", aliases)
        self.assertIn("node.try_as<TextBox>()", aliases)
        for control in ("PasswordBox", "RichEditBox", "ComboBox",
                        "AutoSuggestBox", "MenuFlyoutPresenter", "ContentDialog"):
            self.assertIn(f"node.try_as<{control}>()", aliases)
        self.assertLess(root.index("pendingConfirmationToken()"),
                        root.index("int viewShortcut=-1;"))
        self.assertLess(aliases.index("GetParent(node)"),
                        aliases.index("ui->UpdateView(viewShortcut)"))
        command = aliases.split("if(viewShortcut>=0){", 1)[1]
        self.assertTrue(command.startswith(
            " ui->UpdateView(viewShortcut); args.Handled(true); return;"
        ))
        self.assertNotIn("PersistPreferences(", aliases)
        self.assertNotIn("pane.active=", aliases)
        owner = compact((ROOT / "app/winui/m20_shell.cpp").read_text(encoding="utf-8"))
        owner = owner.split("void MainWindow::UpdateView(int selection)", 1)[1]
        self.assertIn("const int side=ActiveWindowTab().model.activePane", owner)
        self.assertIn("ActiveWindowTab().fileLists[side].viewMode=", owner)
        self.assertIn("fileBar()->SetViewIndex(selection)", owner)

    def test_explorer_aliases_preserve_editor_modal_and_file_boundaries(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        aliases = window.split("const bool addressAlias=", 1)[1].split(
            "// Closed set of Ctrl-only", 1
        )[0]
        guard = aliases.split("if(addressAlias){", 1)[0]
        # New focus aliases may leave address/search fields, but not steal an
        # inline rename, password, combo or modal/menu interaction.
        for control in ("PasswordBox", "RichEditBox", "ComboBox",
                        "AutoSuggestBox", "MenuFlyoutPresenter", "ContentDialog"):
            self.assertIn(f"node.try_as<{control}>()", guard)
        self.assertIn("box!=ui->AddressBox()&&box!=ui->QuickSearchBox()", guard)
        self.assertIn("(refreshAlias||", guard)
        for forbidden in ("RunTransfer(", "OpenFolder(", "StartSearch(",
                          "PersistPreferences("):
            self.assertNotIn(forbidden, aliases)
        self.assertIn("OnAddressDisplayClicked(nullptr,nullptr)", aliases)
        self.assertIn("search.SelectAll()", aliases)
        root = window.split("RootShell().PreviewKeyDown(", 1)[1]
        self.assertLess(root.index("pendingConfirmationToken()"),
                        root.index("const bool addressAlias="))

    def test_explorer_alias_bindings_do_not_replace_configurable_shortcuts(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        aliases = window.split("const bool addressAlias=", 1)[1].split(
            "// Closed set of Ctrl-only", 1
        )[0]
        for binding in (
            "!control&&!shift&& ((!alt&&key==Windows::System::VirtualKey::F4)|| (alt&&key==Windows::System::VirtualKey::D))",
            "searchAlias=!control&&!shift&&!alt&& key==Windows::System::VirtualKey::F3",
            "refreshAlias=control&&!shift&&!alt&& key==Windows::System::VirtualKey::R",
        ):
            self.assertIn(binding, aliases)
        # Ctrl+R joins the same active-pane refresh branch, rather than
        # creating another navigation request implementation.
        refresh = window.split("key==Windows::System::VirtualKey::F5", 1)[1].split(
            "key==Windows::System::VirtualKey::F6", 1
        )[0]
        self.assertIn(")||refreshAlias)", refresh)
        self.assertIn("QueuePidl(side", refresh)
        self.assertIn("NavigationAction::Refresh", refresh)

    def test_f5_is_window_preview_refresh_not_file_transfer(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        preview = window.split("RootShell().PreviewKeyDown(", 1)[1].split(
            "})); RefreshWindowTabs();", 1
        )[0]
        self.assertIn(
            "key==Windows::System::VirtualKey::F5", preview
        )
        f5 = preview.split(
            "key==Windows::System::VirtualKey::F5", 1
        )[1].split(
            "key==Windows::System::VirtualKey::F6", 1
        )[0]
        self.assertIn("NavigationAction::Refresh", f5)
        self.assertIn("QueuePidl(side", f5)
        self.assertNotIn("RunTransfer(", f5)

    def test_f6_is_window_preview_split_pane_focus(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        preview = window.split("RootShell().PreviewKeyDown(", 1)[1].split(
            "})); RefreshWindowTabs();", 1
        )[0]
        f6 = preview.split(
            "key==Windows::System::VirtualKey::F6", 1
        )[1].split(
            "const bool createFolderShortcut", 1
        )[0]
        self.assertIn("model.split", f6)
        self.assertIn("const int other=1-model.activePane", f6)
        self.assertIn("ActivatePane(other)", f6)
        self.assertIn("Focus( Microsoft::UI::Xaml::FocusState::Keyboard)", f6)
        self.assertIn("const bool focused=otherView.Focus(", f6)
        self.assertIn("focused?", f6)
        self.assertIn("포커스를 이동할 수 없습니다.", f6)
        self.assertNotIn("RunTransfer(", f6)

    def test_configurable_ctrl_focus_shortcuts_do_not_mutate_files(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        preview = window.split("RootShell().PreviewKeyDown(", 1)[1].split(
            "})); RefreshWindowTabs();", 1
        )[0]
        for token in (
            "VirtualKey::L", "VirtualKey::E",
            "VirtualKey::F", "VirtualKey::K",
            "VirtualKey::G", "VirtualKey::J",
            "pref.addressShortcut", "pref.searchShortcut",
            "OnAddressDisplayClicked(nullptr,nullptr)",
            "QuickSearchBox()", "SelectAll()", "args.Handled(true)",
        ):
            self.assertIn(token, preview)
        self.assertNotIn("RunTransfer(", preview)
        bindings = (ROOT / "src" / "base" / "ui_preferences.h").read_text(
            encoding="utf-8"
        )
        self.assertIn("validFocusShortcuts(", bindings)
        self.assertIn("kFocusShortcutCount=6", bindings)
        self.assertIn("address!=search", bindings)
        self.assertIn("std::size(choices)==", window)
        self.assertIn("fxfile::uisettings::kFocusShortcutCount", window)
        store = (ROOT / "src" / "base" / "ui_preferences.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("address<kFocusShortcutCount", store)
        self.assertIn("search<kFocusShortcutCount", store)
        self.assertIn("addressShortcut=0", bindings)
        self.assertIn("searchShortcut=2", bindings)

    def test_shortcut_editor_supports_save_reset_and_persistence(self):
        ui = (ROOT / "app" / "winui" / "MainWindow.xaml").read_text(
            encoding="utf-8"
        )
        header = (ROOT / "app" / "winui" / "MainWindow.xaml.h").read_text(
            encoding="utf-8"
        )
        window = WINDOW.read_text(encoding="utf-8")
        for token in (
            'x:Name="AddressShortcutBox"', 'x:Name="SearchShortcutBox"',
            'Click="OnApplyShortcuts"', 'Click="OnResetShortcuts"',
        ):
            self.assertIn(token, ui)
        for name in ('AddressShortcutBox', 'SearchShortcutBox'):
            choices = ui.split('x:Name="'+name+'"', 1)[1].split(
                '</ComboBox>', 1
            )[0]
            items = re.findall(r'<ComboBoxItem Content="([^"]+)"/>', choices)
            self.assertEqual(
                ['Ctrl+L', 'Ctrl+E', 'Ctrl+F', 'Ctrl+K', 'Ctrl+G', 'Ctrl+J'],
                items,
            )
        for name in ("OnApplyShortcuts", "OnResetShortcuts"):
            self.assertIn(name, header)
            self.assertIn("void MainWindow::"+name+"(", window)
        self.assertIn("PersistPreferences()", window)

    def test_full_gui_profile_covers_real_shortcut_keyboard(self):
        orchestrator = compact(
            (ROOT / "tools" / "winui" / "run_checks.py").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn('if area == "all":', orchestrator)
        self.assertIn('for focused in ("window-tabs", "shortcuts", "filter-preset"):', orchestrator)
        self.assertIn('gui_command( focused, configuration, env )', orchestrator)
        self.assertIn('"test_shortcut_gui.py"', orchestrator)

    def test_file_operation_shortcuts_do_not_own_f5_or_f6(self):
        transfers = compact(TRANSFERS.read_text(encoding="utf-8"))
        handler = transfers[
            transfers.index("void MainWindow::HandleFileShortcut"):
        ]
        self.assertNotIn("VirtualKey::F5", handler)
        self.assertNotIn("VirtualKey::F6", handler)
        self.assertNotIn(
            "RunTransfer(fxfile::shelltransfer::Kind::Copy);args.Handled(true);return;",
            handler,
        )
        self.assertNotIn(
            "RunTransfer(fxfile::shelltransfer::Kind::Move);args.Handled(true);return;",
            handler,
        )


if __name__ == "__main__":
    unittest.main()

