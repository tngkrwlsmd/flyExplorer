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

    def test_post_failure_releases_only_its_own_busy_ticket(self):
        """큐 등록 실패가 UI 완료 콜백 없이도 해당 작업의 busy를 해제한다."""
        controller = read("app/winui/file_operation_controller.cpp")
        worker = controller.split(
            "FileOperationController::StartStatus FileOperationController::startFileCommand(", 1
        )[1].split("FileOperationController::CommandDisposition", 1)[0]
        self.assertIn("posted=post([", worker)
        self.assertIn("if(!posted){", worker)
        failure = worker.split("if(!posted){", 1)[1].split("}).detach();", 1)[0]
        self.assertIn("std::lock_guard<std::mutex> lock(shared->mutex)", failure)
        self.assertIn("if(shared->epoch==ticket){", failure)
        self.assertIn("shared->busy=false;", failure)
        self.assertNotIn("completion(std::move(value))", failure)

    def test_delivery_trace_separates_enqueue_from_ui_execution(self):
        """테스트 빌드에서만 등록 결과·UI 진입·실제 전달을 구별한다."""
        source = read("app/winui/m21_commands.cpp")
        post = source.split(
            "FileOperationController::Post MainWindow::FileOperationUiPost(){", 1
        )[1].split(
            "FileOperationController::RestoreCallback MainWindow::FileOperationRestoreCallback(){", 1
        )[0]
        owned, normal = post.split("#else", 1)
        for marker in (
            '"POST_CALLED\\n"', '"POST_REJECTED\\n"',
            '"POST_ACCEPTED\\n"', '"POST_EXCEPTION\\n"',
            '"UI_TASK_ENTERED\\n"', '"UI_TASK_DISPATCH\\n"',
        ):
            self.assertIn(marker, owned)
            self.assertNotIn(marker, normal)
        self.assertLess(owned.index('"UI_TASK_ENTERED\\n"'),
                        owned.index('"UI_TASK_DISPATCH\\n"'))
        self.assertLess(owned.index("if(auto ui=weak.get())"),
                        owned.index('"UI_TASK_DISPATCH\\n"'))
        self.assertIn("if(!ui->mClosing)", owned)
        self.assertIn("return queued;", owned)

    def test_test_only_worker_result_and_busy_release_trace(self):
        """Worker Post return and ticket busy release are independent of UI."""
        header = read("app/winui/file_operation_controller.h")
        controller = read("app/winui/file_operation_controller.cpp")
        commands = read("app/winui/m21_commands.cpp")
        gui = read("tests/winui/test_owned_r07_restore_runtime_gui.py")
        self.assertIn("using FileCommandWorkerTrace=", header)
        self.assertIn("FLYEXPLORER_R07_OWNED_WORKER_TRACE", commands)
        self.assertIn("ownedR07PathUnderTemp(*candidate)", commands)
        self.assertIn("ownedR07PathEqual(*expectedOriginal,request.source)", commands)
        self.assertIn("std::move(workerTrace)", commands)
        for stage in (
            "WORKER_POST_PENDING", "WORKER_POST_TRUE", "WORKER_POST_FALSE",
            "WORKER_BUSY_RELEASED", "WORKER_BUSY_NOT_RELEASED",
            "WORKER_POST_EXCEPTION",
        ):
            self.assertIn(stage, controller)
        self.assertIn("if(shared->epoch==ticket)", controller)
        self.assertIn("released=true;", controller)
        self.assertIn('b"WORKER_POST_PENDING" in exe.read_bytes()', gui)
        self.assertIn(
            'worker_lines == ["WORKER_POST_PENDING", "WORKER_POST_TRUE"]', gui
        )

    def test_restore_start_rejection_is_only_test_owned_trace(self):
        source = read("app/winui/m21_commands.cpp")
        start = source.split(
            "MainWindow::StartPendingRenameRestoreForCurrentOwner(", 1
        )[1].split("bool MainWindow::RestoreCompletionContextCurrent(", 1)[0]
        self.assertIn(
            "#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)", start
        )
        for stage in (
            "START_CONTEXT_NOT_CURRENT",
            "START_CANDIDATE_UNAVAILABLE",
            "START_ASYNC_BUSY",
            "START_ASYNC_STALE",
            "START_ASYNC_THREAD_FAILURE",
        ):
            self.assertIn(stage, start)
        self.assertIn("if(!RestoreCompletionContextCurrent(liveContext))", start)
        self.assertIn("if(!taken){", start)
        self.assertIn("startTakenRenameRestoreAsync(", start)
        self.assertIn("traceStartReject", start)
        self.assertNotIn("restoreRenameNoReplace(", start)

    def test_owned_restore_context_rejection_reports_exact_guard(self):
        """실기 소유권 거부를 테스트 빌드에서만 분류하고 실제 차단은 보존한다."""
        source = read("app/winui/m21_commands.cpp")
        start = source.split(
            "MainWindow::StartPendingRenameRestoreForCurrentOwner(", 1
        )[1].split("bool MainWindow::RestoreCompletionContextCurrent(", 1)[0]
        self.assertIn("if(!RestoreCompletionContextCurrent(liveContext)){", start)
        diagnostic = start.split("START_CONTEXT_NOT_CURRENT", 1)[1].split(
            "#endif", 1
        )[0]
        for stage in (
            "START_CONTEXT_CLOSING",
            "START_CONTEXT_INVALID_ORIGIN",
            "START_CONTEXT_INACTIVE_PANE",
            "START_CONTEXT_OTHER_TAB",
            "START_CONTEXT_MISSING_TAB",
            "START_CONTEXT_MISSING_PENDING",
            "START_CONTEXT_NAV_PENDING",
            "START_CONTEXT_MISSING_ROUTE",
            "START_CONTEXT_ROUTE_CHANGED",
            "START_CONTEXT_MISSING_PATH",
            "START_CONTEXT_FOLDER_CHANGED",
            "START_CONTEXT_SHELL_CHANGED",
            "START_CONTEXT_WINDOW_TAB_MISSING",
        ):
            self.assertIn(stage, diagnostic)
        self.assertIn("traceStartReject(reason)", diagnostic)
        self.assertIn(
            "return FileOperationController::StartStatus::StaleConfirmation;",
            start.split("traceStartReject(reason)", 1)[1],
        )
        guard = source.split(
            "bool MainWindow::RestoreCompletionContextCurrent(", 1
        )[1].split("void MainWindow::OnRenameRestoreCompleted(", 1)[0]
        for safety in (
            "if(mClosing||origin.side<0||origin.side>1||",
            "!origin.windowTabIdentity||!origin.route",
            "state.model.activePane!=origin.side",
            "pane.pending[origin.tab]",
            "pane.routeIds[origin.tab]!=origin.route",
            "pane.filesystemPaths[origin.tab]!=origin.visibleFolder",
            "origin.visibleShellFolder",
        ):
            self.assertIn(safety, guard)

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
