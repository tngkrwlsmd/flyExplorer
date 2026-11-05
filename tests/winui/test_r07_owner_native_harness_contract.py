"""R07-15: fixture links real controller, never the GUI/restore action."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")

class R07OwnerNativeContract(unittest.TestCase):
    def test_actual_controller_compilation(self):
        template=read("tests/winui/r07_owner_native/FlyR07OwnerNative.project-template.xml")
        self.assertIn(r"app\winui\file_operation_controller.cpp",template)
        self.assertIn(r"src\base\file_command_core.cpp",template)
        self.assertIn("FLY_R07_OWNER_NATIVE_CONTRACT",template)
        cpp=read("app/winui/file_operation_controller.cpp")
        self.assertTrue(cpp.startswith('#if !defined(FLY_R07_OWNER_NATIVE_CONTRACT)\n#include "pch.h"\n#endif'))
        self.assertIn("recheckAndRetireRenameRestoreCandidate(",cpp)
    def test_test_fixture_never_calls_real_restore(self):
        fixture=read("tests/winui/r07_owner_native/owner_gate_native_fixture.cpp")
        self.assertIn('request.name=L"invalid\\\\leaf";',fixture)
        self.assertIn("R07_OWNER_NATIVE_SUMMARY",fixture)
        self.assertIn("std::abort();",fixture)
        self.assertNotIn("restoreRenameNoReplace(",fixture)
        for forbidden in ("CreateFileW(","DeleteFileW(","MoveFileW(","SetFileInformationByHandle("):
            self.assertNotIn(forbidden,fixture)
        self.assertNotIn("recheckAndRetireRenameRestoreCandidate(",read("app/winui/m22_transfers.cpp"))
    def test_wrapper_exact_result_and_user_guard(self):
        wrapper=read("tests/winui/r07_owner_native/test_native.py")
        self.assertIn("R07_OWNER_NATIVE_SUMMARY 23 passed, 0 failed.",wrapper)
        self.assertIn("snapshot_legacy_profile()",wrapper)
        self.assertIn("assert_legacy_profile_unchanged(real, original)",wrapper)
        self.assertIn("shutil.rmtree(own)",wrapper)

if __name__=="__main__":
    unittest.main()
