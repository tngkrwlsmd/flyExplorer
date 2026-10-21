"""F08 bounded single-file raw Deflate ZIP writer source contracts; NOT EXECUTED."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[2]
def get(path):
    return (R/path).read_text(encoding="utf-8-sig")
class ZipDeflateWriterContracts(unittest.TestCase):
    def test_vendor_codec_and_project_template(self):
        d="src/base/third_party/miniz_3_1_2/"
        for p in ("LICENSE","miniz_tdef.h","miniz_tdef.c",
                  "miniz_tdef_compat.h","UPSTREAM.md"):
            self.assertTrue((R/(d+p)).is_file())
        self.assertIn('#include "miniz_tdef_compat.h"',get(d+"miniz_tdef.c"))
        self.assertIn("3.1.2",get(d+"UPSTREAM.md"))
        c=get("src/base/zip_raw_deflate_compress.cpp")
        for token in ("TDEFL_DEFAULT_MAX_PROBES","TDEFL_FINISH",
                      "tdefl_init(","tdefl_compress(","TDEFL_STATUS_DONE",
                      "consumed!=source.size()","MINIZ_NO_MALLOC",
                      "MINIZ_NO_STDIO","MINIZ_NO_TIME"):
            self.assertIn(token,c)
        self.assertNotIn("TDEFL_WRITE_ZLIB_HEADER;",c)
        proj=get("app/winui/flyExplorer.project-template.xml")
        self.assertIn("zip_raw_deflate_compress.cpp",proj)
        self.assertIn("miniz_tdef.c",proj)
        self.assertIn("<CompileAs>CompileAsC</CompileAs>",proj)

    def test_bounded_safe_onefile_creation(self):
        w=get("src/base/zip_deflate_writer.h")
        for token in ('L".deflate.zip"', "zipstore::detail::safeSource(",
                      "GENERIC_READ,FILE_SHARE_READ",
                      "FILE_FLAG_OPEN_REPARSE_POINT",
                      "kMaxCompressionInput","ftLastWriteTime",
                      "ziprawdeflate::compressBounded(content,compressed)",
                      "ziprawdeflate::inflateExact(","verified!=content",
                      "kMaxRatio","useDeflate?8u:0u",
                      "0x04034b50u","0x02014b50u","0x06054b50u",
                      "GetTempFileNameW(parent.c_str()",
                      "staging.owned=true;","state.nNumberOfLinks==1",
                      "zipstore::detail::writeAll(output.h,zip)",
                      "MoveFileExW(staging.path,target.c_str(),MOVEFILE_WRITE_THROUGH)",
                      "staging.owned=false;"):
            self.assertIn(token,w)
        self.assertLess(w.index("ziprawdeflate::inflateExact("),
                        w.index("GetTempFileNameW(parent.c_str()"))
        for bad in ("MOVEFILE_REPLACE_EXISTING","CREATE_ALWAYS",
                    "FILE_SHARE_WRITE","ShellExecuteW("):
            self.assertNotIn(bad,w)

if __name__=="__main__":
    unittest.main()
