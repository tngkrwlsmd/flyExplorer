"""R07-1: record only a successful Rename's original path, never undo files."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]


def src(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")


class R07RenameReceiptContract(unittest.TestCase):
    def test_completion_adds_value_only_to_existing_file_command_result(self):
        header=src("app/winui/file_operation_controller.h")
        struct=header.split("struct FileCommandCompletion final {",1)[1].split("\n    };",1)[0]
        for marker in ("ticket=0", "Context context{}", "Kind kind=", "Result result{}",
                       "std::wstring originalRenameSource{}"):
            self.assertIn(marker,struct)
        self.assertNotIn("std::filesystem",struct)
        self.assertNotIn("HANDLE ",struct)

    def test_source_is_frozen_before_native_execution_only_for_rename(self):
        cpp=src("app/winui/file_operation_controller.cpp")
        body=cpp.split("FileOperationController::StartStatus FileOperationController::startFileCommand(",1)[1].split(
            "FileOperationController::CommandDisposition",1)[0]
        for marker in ("value.ticket=ticket","value.context=std::move(context)",
                       "request.kind==fxfile::filecommand::Kind::RenameSelected",
                       "originalRenameSource=request.source",
                       "value.result=fxfile::filecommand::execute(request)",
                       "value.result.error==ERROR_SUCCESS",
                       "value.originalRenameSource=std::move(originalRenameSource)"):
            self.assertIn(marker,body)
        self.assertLess(body.index("originalRenameSource=request.source"),
                        body.index("value.result=fxfile::filecommand::execute(request)"))
        self.assertLess(body.index("value.result=fxfile::filecommand::execute(request)"),
                        body.index("value.originalRenameSource=std::move(originalRenameSource)"))

    def test_no_undo_mutation_or_os_history_flag_was_added(self):
        header=src("app/winui/file_operation_controller.h")
        cpp=src("app/winui/file_operation_controller.cpp")
        command=src("src/base/file_command_core.cpp")
        transfer=src("src/base/shell_transfer_core.cpp")
        menu=src("app/winui/m22_transfers.cpp")
        for forbidden in ("UndoFile(", "RedoFile(", "MoveFileExW(", "SetOperationFlags("):
            self.assertNotIn(forbidden,cpp)
        self.assertNotIn("FOFX_ADDUNDORECORD",transfer)
        self.assertIn("if(task.kind==Kind::Recycle)flags|=FOF_ALLOWUNDO|FOFX_RECYCLEONDELETE;",transfer)
        self.assertIn("::MoveFileW(src.c_str(),target.c_str())",command)
        self.assertNotIn('L"실행 취소"',menu)
        self.assertIn("originalRenameSource",header)

    def test_design_requires_verified_identity_and_no_overwrite(self):
        design=src("docs/development/R07_UNDO_RECEIPT_POLICY_20261103.md")
        for marker in ("R07-1", "볼륨 식별자", "파일 ID", "외부 변경", "차단",
                       "Redo", "NOT TESTED", "실행 취소 가능 판정이나 파일 쓰기 허가가 아니다"):
            self.assertIn(marker,design)


if __name__=="__main__":
    unittest.main()
