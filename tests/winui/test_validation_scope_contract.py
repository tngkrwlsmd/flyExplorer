from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/winui/resolve_validation_scope.py"
SPEC = spec_from_file_location("resolve_validation_scope", MODULE_PATH)
assert SPEC and SPEC.loader
SCOPE = module_from_spec(SPEC)
SPEC.loader.exec_module(SCOPE)


class ValidationScopeContractTests(unittest.TestCase):
    def classify(self, paths, message="fix: change behavior"):
        return SCOPE.classify(paths, message)[0]

    def test_metadata_and_source_contracts_use_source(self):
        self.assertEqual(
            self.classify([
                "AGENTS.md",
                "docs/development/AGENT_EFFICIENCY.md",
                "tests/winui/test_arch_contract.py",
                "tools/policy/run_policy_checks.py",
            ]),
            "source",
        )

    def test_ui_independent_and_build_paths_use_release(self):
        self.assertEqual(self.classify(["src/base/model.cpp"]), "release")
        self.assertEqual(self.classify(["packaging/setup.iss"]), "release")
        self.assertEqual(self.classify(["build.bat"]), "release")
        self.assertEqual(
            self.classify(["tests/winui/m20/m20_native_fixture.cpp"]),
            "release",
        )

    def test_nonvisual_winui_refactor_uses_release(self):
        self.assertEqual(
            self.classify(
                [
                    "app/winui/workspace_restore_coordinator.cpp",
                    "app/winui/workspace_restore_coordinator.h",
                    "tests/winui/test_workspace_restore_coordinator_contract.py",
                ],
                "refactor: isolate restore lifecycle",
            ),
            "release",
        )

    def test_explicit_release_trailer_can_mark_nonvisual_behavior_preserving_work(self):
        self.assertEqual(
            self.classify(
                ["app/winui/MainWindow.xaml.cpp"],
                "chore: reorganize event plumbing\n\nCI-Scope: release",
            ),
            "release",
        )

    def test_regular_winui_behavior_change_uses_build_focused_release(self):
        self.assertEqual(
            self.classify(["app/winui/MainWindow.xaml.cpp"], "fix: update navigation"),
            "release",
        )

    def test_xaml_uses_release_automatic_scope(self):
        for message in (
            "refactor: reorganize view",
            "refactor: reorganize view\n\nCI-Scope: release",
            "ui: reorganize view\n\nCI-Scope: release-gui",
        ):
            self.assertEqual(
                self.classify(["app/winui/MainWindow.xaml"], message),
                "release",
            )

    def test_gui_harness_uses_release_automatic_scope(self):
        self.assertEqual(
            self.classify(
                ["tests/winui/test_shell_gui.py"],
                "refactor: simplify GUI harness",
            ),
            "release",
        )

    def test_release_gui_trailer_does_not_enable_automatic_gui(self):
        self.assertEqual(
            self.classify(
                ["src/base/model.cpp"],
                "fix: model behavior\n\nCI-Scope: release-gui",
            ),
            "release",
        )

    def test_source_trailer_cannot_downgrade_product_change(self):
        self.assertEqual(
            self.classify(
                ["app/winui/search_controller.cpp"],
                "fix: search behavior\n\nCI-Scope: source",
            ),
            "release",
        )

    def test_remote_shell_workflow_is_source_only_but_ci_workflow_is_release(self):
        self.assertEqual(
            self.classify([".github/workflows/remote-windows-task.yml"]),
            "source",
        )
        self.assertEqual(
            self.classify([".github/workflows/windows-build.yml"]),
            "release",
        )


if __name__ == "__main__":
    unittest.main()
