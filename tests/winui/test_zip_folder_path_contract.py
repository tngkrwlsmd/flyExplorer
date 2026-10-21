"""F08 one-root ZIP path containment source contracts. NOT EXECUTED."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def source(p):
    return (R/p).read_text(encoding="utf-8-sig")
class SingleRootZipContracts(unittest.TestCase):
    def test_only_one_root_and_one_leaf(self):
        c=source("src/base/zip_store_batch_extractor.h")
        for token in (
            "value.find(L'/',slash+1)",
            "flatName(root)&&flatName(leaf)",
            "rootMode!=!entryRoot.empty()",
            "archiveRoot,entryRoot",
            "zipinspect::detail::same(previous.name,entryLeaf)",
            "staging.nestedRoot",
            "staging.nestedOwned=true;",
            "if(!nestedOwned)return;",
            "CreateDirectoryW(staging.nestedRoot.c_str(),nullptr)",
            "if(!nestedRoot.empty())::RemoveDirectoryW(nestedRoot.c_str())",
            "!(child&FILE_ATTRIBUTE_DIRECTORY)",
            "(child&FILE_ATTRIBUTE_REPARSE_POINT)",
            "CreateDirectoryW(staging.path.c_str(),nullptr)",
            "MoveFileExW(staging.path.c_str(),target.c_str()",
        ):
            self.assertIn(token,c)
        self.assertLess(c.index("detail::memberPath(name,entryRoot,entryLeaf)"),
                        c.index("GetTempFileNameW(parent.c_str()"))
        self.assertLess(c.index("crc32(member.content)!=checksum"),
                        c.index("GetTempFileNameW(parent.c_str()"))
        self.assertNotIn("std::filesystem::remove_all(",c)
if __name__=="__main__":
    unittest.main()
