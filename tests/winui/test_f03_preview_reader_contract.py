"""F03 read-only handle reader must keep strict separations and fail closed."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
HEADER=(ROOT/"src/base/file_preview_reader.h").read_text(encoding="utf-8")
SOURCE=(ROOT/"src/base/file_preview_reader.cpp").read_text(encoding="utf-8")
NATIVE=(ROOT/"tests/winui/native_preview_reader.cpp").read_text(encoding="utf-8")
NS={"b":"http://schemas.microsoft.com/developer/msbuild/2003"}


class F03HandleReaderContract(unittest.TestCase):
    def test_no_path_open_or_ui_thread_io_owner(self):
        self.assertIn("readVerifiedHandle(", HEADER)
        self.assertIn("HANDLE file", HEADER)
        self.assertIn("std::atomic_bool const& cancelled", HEADER)
        self.assertIn("deadline", HEADER)
        for forbidden in (
            "CreateFileW(", "ShellExecute", "CoCreateInstance",
            "std::thread", "std::async", "DispatcherQueue", "FindFirstFile",
        ):
            self.assertNotIn(forbidden, SOURCE)
        self.assertIn("Call ONLY inside a supervised, cancellable worker process", HEADER)
        self.assertIn("DOES NOT authorize opening a path", HEADER)

    def test_handle_identity_bounds_and_failure_isolation(self):
        for token in (
            "GetFileInformationByHandleEx(",
            "FileStandardInfo", "FileBasicInfo", "FileAttributeTagInfo",
            "FILE_ATTRIBUTE_REPARSE_POINT", "FILE_ATTRIBUTE_OFFLINE",
            "GetFinalPathNameByHandleW(",
            "CompareStringOrdinal(",
            "GetDriveTypeW(volume)==DRIVE_FIXED",
            "previewpolicy::kMaxTextBytes",
            "previewpolicy::kMaxImageBytes",
            "GetFileType(handle)!=FILE_TYPE_DISK",
            "SetFilePointerEx(", "ReadFile(",
            "afterBasic.LastWriteTime.QuadPart!=beforeBasic.LastWriteTime.QuadPart",
            "Status::ChangedFile", "Status::Cancelled",
            "Status::Deadline", "Status::ShortRead", "Status::InvalidText",
            "catch(...)",
        ):
            self.assertIn(token, SOURCE)
        self.assertIn("return reject(Status::IoError)", SOURCE)
        self.assertIn("std::vector<std::uint8_t> payload;", SOURCE)
        self.assertIn("if(kind==previewpolicy::Kind::Text && !inertUtf8(payload))", SOURCE)

    def test_native_runner_serializes_complete_batch_lines(self):
        runner=(ROOT/"tools/winui/run_f03_reader_native.ps1").read_text(
            encoding="utf-8")
        for marker in (
            "('call \"'+$vcvars+",
            "('cd /d \"'+$FixtureRoot+",
            "('cl.exe /nologo /std:c++20",
            "('\"'+$exe+",
            "$body.Count -ne 9",
            "F03_NATIVE_BATCH_SERIALIZATION_INVALID",
        ):
            self.assertIn(marker, runner)

    def test_registered_native_translation_unit(self):
        project=ET.parse(ROOT/"app/winui/flyExplorer.project-template.xml")
        compiles=[
            e.attrib["Include"].replace("\\", "/")
            for e in project.findall(".//b:ClCompile", NS)
            if "Include" in e.attrib
        ]
        headers=[
            e.attrib["Include"].replace("\\", "/")
            for e in project.findall(".//b:ClInclude", NS)
            if "Include" in e.attrib
        ]
        self.assertIn("../../src/base/file_preview_reader.cpp", compiles)
        self.assertIn("../../src/base/file_preview_reader.h", headers)
        self.assertIn("../../src/base/file_preview_policy.h", headers)
        self.assertIn("F03_NATIVE_HANDLE_READ_AND_FAILURE_CONTRACT=PASS", NATIVE)


if __name__=="__main__":
    unittest.main()
