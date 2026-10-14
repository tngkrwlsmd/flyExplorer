"""F03 safe-open source contract for bounded worker-only candidate opening."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
SOURCE=(ROOT/"src/base/file_preview_safe_open.cpp").read_text(encoding="utf-8")
HEADER=(ROOT/"src/base/file_preview_safe_open.h").read_text(encoding="utf-8")
NATIVE=(ROOT/"tests/winui/native_preview_reader.cpp").read_text(encoding="utf-8")


class F03SafeOpenContract(unittest.TestCase):
    def test_guards_and_volume_checks(self):
        for token in (
            "kMaxAncestors=64", "UniqueHandle file;",
            "std::vector<UniqueHandle> lockedAncestors",
            "openLocalRegular(",
        ):
            self.assertIn(token,HEADER)
        for token in (
            "previewpolicy::screen(candidate)",
            "GetDriveTypeW(rootText)!=DRIVE_FIXED",
            "FILE_FLAG_OPEN_REPARSE_POINT",
            "FILE_FLAG_BACKUP_SEMANTICS",
            "FILE_SHARE_READ",
            "GetFinalPathNameByHandleW(",
            "FileAttributeTagInfo", "FileIdInfo",
            "FileStandardInfo", "FILE_ATTRIBUTE_REPARSE_POINT",
            "rootIdentity.VolumeSerialNumber",
            "Status::Changed",
            "opened.lockedAncestors.push_back(std::move(part))",
        ):
            self.assertIn(token,SOURCE)

    def test_template_and_owned_native(self):
        project=ET.parse(ROOT/"app/winui/flyExplorer.project-template.xml")
        compile_paths=[
            c.get("Include","").replace(chr(92),"/")
            for c in project.iter()
            if c.tag.endswith("ClCompile")
        ]
        self.assertIn("../../src/base/file_preview_safe_open.cpp",compile_paths)
        self.assertIn("const std::wstring path(candidate.absolutePath)",SOURCE)
        self.assertIn("stable.absolutePath=path",SOURCE)
        self.assertIn("previewpolicy::screen(stable)",SOURCE)
        self.assertLess(
            SOURCE.index("const std::wstring path(candidate.absolutePath)"),
            SOURCE.index("previewpolicy::screen(stable)"))
        self.assertIn("UniqueHandle openPath(std::wstring const& path,bool directory) {",SOURCE)
        self.assertNotIn("UniqueHandle openPath(std::wstring const& path,bool directory) noexcept",SOURCE)
        self.assertIn("F03_NATIVE_SAFE_OPEN_AND_GUARDED_READ=PASS",NATIVE)
        self.assertIn("std::wstring&&,std::uint64_t)=delete;",NATIVE)
        self.assertIn("F03_NATIVE_ANCESTOR_SYMLINK_REJECT=NOT_TESTED",NATIVE)


if __name__=="__main__":
    unittest.main()
