"""R07-23E-A 소유 WinUI 런타임 진입의 컴파일·경로 안전 계약.

일반 제품 빌드에는 진입점이 없고, 명시적 테스트 빌드에서도 %TEMP% 아래
정확한 Rename 원본/대상/추적 경로가 모두 일치할 때만 private 복원을 시작한다.
이 검사는 소스 경계를 확인하며 실제 WinUI 실행 결과는 별도 Windows 증거다.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


class OwnedRestoreRuntimeBoundaryContract(unittest.TestCase):
    def test_compile_symbol_requires_explicit_msbuild_property(self):
        project = read("app/winui/flyExplorer.project-template.xml")
        self.assertIn(
            """Condition="'$(FlyExplorerR07OwnedRuntimeTest)'=='true'">""",
            project,
        )
        self.assertIn("FLYEXPLORER_R07_OWNED_RUNTIME_TEST", project)
        release = project.split(
            """<ItemDefinitionGroup Condition="'$(Configuration)'=='Release'">""",
            1,
        )[1].split("</ItemDefinitionGroup>", 1)[0]
        self.assertNotIn("FLYEXPLORER_R07_OWNED_RUNTIME_TEST", release)
        build = read("app/winui/build.cmd")
        self.assertIn(
            'if "%FLYEXPLORER_R07_OWNED_RUNTIME_BUILD%"=="1"',
            build,
        )
        self.assertEqual(build.count("%R07_OWNED_RUNTIME_PROPERTY%"), 2)

    def test_runtime_entry_requires_exact_owned_temp_paths(self):
        source = read("app/winui/m21_commands.cpp")
        for token in (
            "FLYEXPLORER_R07_OWNED_ORIGINAL",
            "FLYEXPLORER_R07_OWNED_TARGET",
            "FLYEXPLORER_R07_OWNED_TRACE",
            "FLYEXPLORER_R07_OWNED_DELIVERY_TRACE",
            "POST_CALLED\\n",
            "POST_ACCEPTED\\n",
            "UI_TASK_ENTERED\\n",
            "UI_TASK_DISPATCH\\n",
            "ON_FILE_COMPLETION\\n",
            "ownedR07PathUnderTemp(*expectedOriginal)",
            "ownedR07PathUnderTemp(*expectedTarget)",
            "ownedR07PathUnderTemp(*trace)",
            "ownedR07PathEqual(*expectedOriginal,completion.originalRenameSource)",
            "ownedR07PathEqual(*expectedTarget,completion.result.target)",
            'writeOwnedR07Trace(*trace,"BEGIN\\n",true)',
        ):
            self.assertIn(token, source)
        self.assertIn("CREATE_NEW:OPEN_EXISTING", source)
        self.assertIn("FILE_FLAG_OPEN_REPARSE_POINT", source)
        self.assertIn("FILE_ATTRIBUTE_REPARSE_POINT", source)
        self.assertIn("FILE_SHARE_READ|FILE_SHARE_WRITE", source)

    def test_owned_gui_temp_environment_matches_win32_temp_path(self):
        source = read("tests/winui/test_owned_r07_restore_runtime_gui.py")
        self.assertIn(
            'for key in ("APPDATA", "LOCALAPPDATA", "TEMP"):', source
        )
        self.assertIn('profile["TMP"] = profile["TEMP"]', source)
        self.assertIn('assert profile["TMP"] == profile["TEMP"]', source)
        self.assertIn('fixture = Path(tempfile.mkdtemp(', source)
        self.assertIn('prefix="fixture-", dir=profile["TEMP"]', source)

    def test_only_guarded_accepted_rename_calls_private_restore(self):
        source = read("app/winui/m21_commands.cpp")
        call = source.rindex("StartPendingRenameRestoreForCurrentOwner(")
        guard = source.rfind(
            "#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)", 0, call
        )
        end = source.find("#endif", call)
        self.assertGreater(guard, 0)
        self.assertGreater(end, call)
        guarded = source[guard:end]
        self.assertIn("Disposition::Succeeded", source[:guard])
        self.assertIn("Kind::RenameSelected", guarded)
        self.assertIn("renameEvidence.verified", guarded)
        self.assertIn("StartStatus::Started", guarded)
        self.assertNotIn("OnUndo", source)
        self.assertNotIn("OnRedo", source)

    def test_runtime_completion_is_traced_once_before_owned_refresh(self):
        source = read("app/winui/m21_commands.cpp")
        callback = source.split(
            "void MainWindow::OnRenameRestoreCompleted(", 1
        )[1].split("void MainWindow::OnCreateFolder(", 1)[0]
        self.assertIn("mOwnedR07RestoreRuntimeActive=false", callback)
        self.assertEqual(callback.count("writeOwnedR07Trace("), 1)
        self.assertIn('"COMPLETE_VERIFIED\\n"', callback)
        self.assertLess(
            callback.index("writeOwnedR07Trace("),
            callback.index("QueuePidl("),
        )


if __name__ == "__main__":
    unittest.main()
