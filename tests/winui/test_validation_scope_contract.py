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
    def classify(self, paths):
        return SCOPE.classify(paths, "fix: change behavior")[0]

    def areas(self, paths):
        return SCOPE.affected_areas(paths)

    def test_metadata_and_contracts_remain_source_only(self):
        self.assertEqual(
            "source",
            self.classify([
                "AGENTS.md",
                "docs/development/AGENT_EFFICIENCY.md",
                "tests/winui/test_arch_contract.py",
                "docs/operations/windows-runner-retirement.md",
            ]),
        )

    def test_product_and_build_paths_require_one_release_build_scope(self):
        for path in (
            "src/base/model.cpp",
            "packaging/package.py",
            "build.bat",
            "app/winui/MainWindow.xaml.cpp",
            "app/winui/MainWindow.xaml",
        ):
            self.assertEqual("release", self.classify([path]), path)

    def test_search_session_shell_and_file_operation_changes_are_narrow(self):
        self.assertEqual(
            {"search"},
            self.areas(["app/winui/search_controller.cpp"]),
        )
        self.assertEqual(
            {"session"},
            self.areas(["app/winui/session_coordinator.cpp"]),
        )
        self.assertEqual(
            {"shell"},
            self.areas(["app/winui/shell_navigation_controller.cpp"]),
        )
        self.assertEqual(
            {"file-operations"},
            self.areas(["src/base/shell_transfer_core.cpp"]),
        )

    def test_packaging_accessibility_large_folder_and_settings_are_narrow(self):
        self.assertEqual({"packaging"}, self.areas(["packaging/package.py"]))
        self.assertEqual(
            {"accessibility"},
            self.areas(["tests/winui/test_high_contrast_contract.py"]),
        )
        self.assertEqual(
            {"large-folder"},
            self.areas(["tests/winui/test_large_folder_streaming_contract.py"]),
        )
        self.assertEqual(
            {"identity-settings"},
            self.areas(["src/base/ui_preferences.cpp"]),
        )

    def test_unknown_base_source_fails_conservatively_to_all_product_areas(self):
        self.assertEqual(
            set(SCOPE.PRODUCT_AREAS),
            self.areas(["src/base/new_cross_cutting_model.cpp"]),
        )

    def test_infra_only_change_does_not_expand_to_product_contracts(self):
        paths = [
            "tools/winui/resolve_validation_scope.py",
            "tools/winui/validate_remote_request.py",
        ]
        self.assertEqual(set(), self.areas(paths))
        self.assertEqual({"infra"}, SCOPE.change_families(paths))

    def test_gui_harness_is_harness_family_without_product_expansion(self):
        paths = ["tests/winui/test_shell_gui.py"]
        self.assertEqual(set(), self.areas(paths))
        self.assertEqual({"harness"}, SCOPE.change_families(paths))


if __name__ == "__main__":
    unittest.main()
