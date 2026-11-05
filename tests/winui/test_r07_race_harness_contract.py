"""R07-17 source guard for one isolated native race executable."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class R07RaceHarnessContract(unittest.TestCase):
    def test_native_project_links_product_function_and_only_test_hook(self):
        project=read("tests/winui/r07_race_native/FlyR07RaceNative.project-template.xml")
        core=read("src/base/file_command_core.cpp")
        self.assertIn(r"src\base\file_command_core.cpp",project)
        self.assertIn("FLY_R07_RESTORE_RACE_NATIVE_TEST",project)
        self.assertIn('#if defined(FLY_R07_RESTORE_RACE_NATIVE_TEST)',core)
        self.assertIn('extern "C" void FlyR07RestoreRaceHook(unsigned stage) noexcept;',core)
        self.assertEqual(3,core.count("FlyR07RestoreRaceHook("))

    def test_recheck_before_native_call_no_overwrite_or_ui(self):
        core=read("src/base/file_command_core.cpp")
        restore=core.split("RenameRestoreWriteResult restoreRenameNoReplace(",1)[1]
        first=restore.index("FlyR07RestoreRaceHook(1u);")
        parent=restore.index("if(!parentStillVisible()",first)
        vacancy=restore.index("const DWORD finalAttrs=",parent)
        late=restore.index("FlyR07RestoreRaceHook(2u);",vacancy)
        syscall=restore.index("status=native(item.h,&io,info,",late)
        self.assertTrue(first<parent<vacancy<late<syscall)
        self.assertIn("info->ReplaceIfExists=FALSE",restore)
        self.assertIn("info->RootDirectory=parent.h;",restore)
        self.assertEqual(1,restore.count("status=native(item.h,&io,info,"))
        for path in ("app/winui/m22_transfers.cpp",
                     "app/winui/file_operation_controller.cpp",
                     "app/winui/m21_commands.cpp"):
            self.assertNotIn("restoreRenameNoReplace(",read(path))
        self.assertNotIn("FLY_R07_RESTORE_RACE_NATIVE_TEST",
                         read("app/winui/flyExplorer.project-template.xml"))

    def test_owned_file_sentinels_and_exact_wrapper_count(self):
        fixture=read("tests/winui/r07_race_native/race_native_fixture.cpp")
        wrapper=read("tests/winui/r07_race_native/test_native.py")
        self.assertIn("R07_RACE_NATIVE_SUMMARY",fixture)
        self.assertIn("native_atomic_no_replace_after_last_check",fixture)
        self.assertIn("parent_move_before_final_guard_handled_or_blocked",fixture)
        self.assertIn("R07_RACE_NATIVE_SUMMARY 8 passed, 0 failed.",wrapper)
        self.assertIn("assert_legacy_profile_unchanged(real,original)",wrapper)
        self.assertIn("shutil.rmtree(own)",wrapper)

if __name__=="__main__":
    unittest.main()
