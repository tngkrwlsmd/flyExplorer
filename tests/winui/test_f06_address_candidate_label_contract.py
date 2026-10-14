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


if __name__=="__main__":
    unittest.main()
