"""F08 raw ZIP Deflate source-only contracts. NOT EXECUTED."""
from pathlib import Path
import unittest

R=Path(__file__).resolve().parents[2]
def get(path):
    return (R/path).read_text(encoding="utf-8-sig")

class ZipRawDeflateContracts(unittest.TestCase):
    def test_pinned_vendor_and_no_file_api(self):
        p="src/base/third_party/miniz_3_1_2/"
        for name in ("LICENSE","miniz_common.h","miniz_export.h",
                     "miniz_tinfl.h","miniz_tinfl.c","UPSTREAM.md"):
            self.assertTrue((R/(p+name)).is_file())
        self.assertIn("miniz_tinfl.h",get(p+"miniz_tinfl.c"))
        self.assertIn("3.1.2",get(p+"UPSTREAM.md"))
        self.assertIn("Permission is hereby granted",get(p+"LICENSE"))

    def test_raw_only_bounded_codec(self):
        code=get("src/base/zip_raw_deflate.cpp")
        for v in ("MINIZ_NO_MALLOC","MINIZ_NO_STDIO","MINIZ_NO_TIME",
                  "tinfl_decompressor decompressor{}",
                  "TINFL_FLAG_USING_NON_WRAPPING_OUTPUT_BUF",
                  "TINFL_STATUS_DONE", "consumed!=packed",
                  "decoded(expected+1u)",
                  "produced!=expected","kMaxOutputBytes",
                  "kMaxPackedBytes", "kMaxRatio",
                  "cancellation->load(std::memory_order_relaxed)"):
            self.assertIn(v,code)
        self.assertNotIn("TINFL_FLAG_PARSE_ZLIB_HEADER",code)
        self.assertNotIn("CREATE_ALWAYS",code)
        project=get("app/winui/flyExplorer.project-template.xml")
        self.assertIn('src\\base\\zip_raw_deflate.cpp',project)
        self.assertIn("<PrecompiledHeader>NotUsing</PrecompiledHeader>",project)
        self.assertIn('src\\base\\third_party\\miniz_3_1_2\\miniz_tinfl.c',project)
        self.assertIn("<CompileAs>CompileAsC</CompileAs>",project)
        self.assertIn("MINIZ_NO_TIME;%(PreprocessorDefinitions)",project)

    def test_one_member_integration_and_crc_before_publication(self):
        ex=get("src/base/zip_store_extractor.h")
        for token in ('#include "zip_raw_deflate.h"',
                      "(method!=0&&method!=8)",
                      "(method==8&&versionNeeded!=20)",
                      "ziprawdeflate::inflateExact(",
                      "zipstore::detail::crc32(payload)!=checksum",
                      "GetTempFileNameW(parent.c_str()"):
            self.assertIn(token,ex)
        self.assertLess(ex.index("ziprawdeflate::inflateExact("),
                        ex.index("GetTempFileNameW(parent.c_str()"))
        self.assertLess(ex.index("zipstore::detail::crc32(payload)!=checksum"),
                        ex.index("GetTempFileNameW(parent.c_str()"))
        ui=get("app/winui/m22_transfers.cpp")
        self.assertIn('make(L"ZIP 해제 (Store/Deflate, 한 파일)"',ui)

if __name__=="__main__":
    unittest.main()
