"""F06: compact visible suggestion labels must not change the full target."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")


class F06AddressCandidateLabelContract(unittest.TestCase):
    def test_candidate_tail_visible_and_full_path_preserved(self):
        source=SOURCE.split("void MainWindow::UpdateAddressSuggestions()",1)[1].split(
            "void MainWindow::OnAddressTextChanged(",1)[0]
        for token in (
            "std::filesystem::path(path)",
            "candidatePath.filename().native()",
            "candidatePath.parent_path().filename().native()",
            "candidateLabel.Text(hstring(display));",
            "candidateLabel.TextTrimming(TextTrimming::CharacterEllipsis);",
            "button.Content(candidateLabel);",
            "ToolTipService::SetToolTip(",
            "button,box_value(hstring(path))",
            "button.Tag(box_value(hstring(path)));",
            'button,L"주소 후보: "+hstring(path)',
        ):
            self.assertIn(token,source)
        self.assertIn("const auto limit=(std::min)(known.size(),static_cast<size_t>(2048));",source)
        self.assertIn("if(choices.size()>=8",source)


    def test_px12_keyboard_up_down_never_leaves_bounded_candidates(self):
        source=SOURCE.split("void MainWindow::UpdateAddressSuggestions()",1)[1].split(
            "void MainWindow::OnAddressTextChanged(",1)[0]
        for fragment in (
            "for(std::size_t candidateIndex=0;candidateIndex<choices.size();++candidateIndex)",
            "button.KeyDown([weak,candidateIndex]",
            "key!=Windows::System::VirtualKey::Escape",
            "key!=Windows::System::VirtualKey::Up",
            "key!=Windows::System::VirtualKey::Down",
            "if(ui->mClosing)return;",
            "if(candidateIndex>=siblings.Size())return;",
            "key==Windows::System::VirtualKey::Up&&candidateIndex==0",
            "ui->AddressBox().Focus(FocusState::Keyboard);",
            "candidateIndex+1:candidateIndex-1",
            "if(target<siblings.Size())",
            "siblings.GetAt(static_cast<std::uint32_t>(target))",
            "ui->mAddressSuggestionKeyboardFocus=true;",
            "next.Focus(FocusState::Keyboard);",
            "args.Handled(true);",
        ):
            self.assertIn(fragment,source)
        # Arrow focus must never execute navigation or introduce a new Shell,
        # network, disk enumeration, or unbounded suggestion query.
        handler=source.split("button.KeyDown([weak,candidateIndex]",1)[1].split(
            "rows.Children().Append(button);",1)[0]
        for forbidden in ("OpenFolder(", "QueuePidl(", "FindFirstFile",
                          "SHParseDisplayName(", "std::filesystem::exists("):
            self.assertNotIn(forbidden,handler)
        self.assertLess(handler.index("if(candidateIndex>=siblings.Size())return;"),
                        handler.index("siblings.GetAt(static_cast<std::uint32_t>(target))"))
        self.assertIn("button.Click({this,&MainWindow::OnAddressSuggestionClicked});",
                      source)



if __name__=="__main__":
    unittest.main()
