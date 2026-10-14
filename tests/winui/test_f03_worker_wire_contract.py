"""F03 one-shot child wire is bounded, private and not yet a UI supervisor."""
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
WIRE=(ROOT/"src/base/file_preview_worker_wire.h").read_text(encoding="utf-8")
HEADER=(ROOT/"src/base/file_preview_worker.h").read_text(encoding="utf-8")
WORKER=(ROOT/"src/base/file_preview_worker.cpp").read_text(encoding="utf-8")
HELPER=(ROOT/"app/winui/helper/FlyShellIsolationHelper.cpp").read_text(encoding="utf-8")
NATIVE=(ROOT/"tests/winui/native_preview_worker.cpp").read_text(encoding="utf-8")
RUNNER=(ROOT/"tools/winui/run_f03_reader_native.ps1").read_text(encoding="utf-8")


class F03WorkerWireContract(unittest.TestCase):
    def test_private_versioned_bounded_wire(self):
        for token in (
            "kRequestMagic", "kReplyMagic", "kVersion=1",
            "kDeadlineMs=3000", "pathUnits>=4u",
            "pathUnits<=kMaxPathUnits",
            "knownBytes<=", "static_assert(sizeof(Request)==28",
            "static_assert(sizeof(Reply)==24",
            "r.status==0u || (!r.byteCount&&!r.checksum&&r.kind==0u)",
        ):
            self.assertIn(token,WIRE)

    def test_child_performs_validation_without_logging_or_ui_calls(self):
        for token in (
            "FILE_TYPE_PIPE", "exactRead(input,&head,sizeof(head))",
            "previewwire::validHeader(head)", "validUtf16(path)",
            "head.pathChecksum", "previewpolicy::canonicalLocalPath(path)",
            "screen(candidate)", "screened.kind!=kind",
            "previewsafe::openLocalRegular(candidate,cancel,deadline)",
            "previewread::readVerifiedHandle(",
            "std::chrono::milliseconds(previewwire::kDeadlineMs)",
            "bytes.size()>previewwire::kMaxReplyBytes",
            "Status::InvalidRequest", "Status::UnsafePath",
            "Status::ReadRejected", "Status::Deadline",
        ):
            self.assertIn(token,WORKER)
        for prohibited in ("CreateProcessW(", "ShellExecute", "CoCreateInstance",
                           "DispatcherQueue", "OutputDebugStringW(", "std::ofstream"):
            self.assertNotIn(prohibited,WORKER)
        self.assertIn("runOne(HANDLE input,HANDLE output) noexcept",WORKER)
        self.assertIn("int runOne(HANDLE input,HANDLE output) noexcept;",HEADER)
        self.assertIn('L"--preview-read"',HELPER)

    def test_helper_build_and_owned_native_negative_cases(self):
        p=ET.parse(ROOT/"app/winui/helper/FlyShellIsolationHelper.project-template.xml")
        compiles=[x.get("Include","").replace("\\","/")
                  for x in p.iter() if x.tag.endswith("ClCompile")]
        for unit in ("file_preview_worker.cpp","file_preview_safe_open.cpp",
                     "file_preview_reader.cpp"):
            self.assertIn("../../../src/base/"+unit,compiles)
        for token in ("native_preview_worker.cpp", "$workerCpp",
                      "$workerTestCpp", "$body[5].Contains($workerCpp)"):
            self.assertIn(token,RUNNER)
        for token in ("F03_NATIVE_WORKER_WIRE_BOUNDS=PASS",
                      "badChecksum", "badKind", "badSize",
                      "absent", "unc"):
            self.assertIn(token,NATIVE)
        self.assertIn('path+L".missing.txt"',NATIVE)


if __name__=="__main__":
    unittest.main()
