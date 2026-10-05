"""Contract tests for the zero-run remote request validator."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "winui" / "validate_remote_request.py"

spec = importlib.util.spec_from_file_location("validate_remote_request", MODULE_PATH)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def request(**overrides):
    sha = "1" * 40
    data = {
        "request_id": "preflight-contract",
        "expected_main_sha": sha,
        "candidate_sha": sha,
        "logical_unit": "preflight-contract",
        "configuration": "none",
        "validation_kind": ["none"],
        "invalidated_evidence": {},
        "working_directory": "",
        "command": "Write-Output 'inspection only'",
    }
    data.update(overrides)
    return data


class RemoteRequestPreflightContract(unittest.TestCase):
    def test_non_validation_shape_passes(self):
        validator.validate_request(request())

    def test_validation_cannot_use_none_configuration(self):
        data = request(
            validation_kind=["source"],
            invalidated_evidence={"source": "contract changed"},
            command="cmd /c test.bat source",
        )
        with self.assertRaisesRegex(
            validator.RequestError,
            "Debug or Release",
        ):
            validator.validate_request(data)

    def test_incidental_gui_filename_does_not_declare_gui_stage(self):
        command = (
            "$largePath=('tests\\winui\\test_large_owned_folder_' + 'gui.py'); "
            "Write-Output $largePath"
        )
        self.assertEqual(set(), validator.detect_stages(command))
        validator.validate_request(request(command=command))

    def test_static_py_compile_of_gui_harness_is_not_gui_stage(self):
        command = (
            "python -X utf8 -m py_compile "
            "tests\\winui\\test_high_contrast_gui.py"
        )
        self.assertEqual(set(), validator.detect_stages(command))
        validator.validate_request(request(command=command))

    def test_static_compileall_of_gui_harness_is_not_gui_stage(self):
        command = (
            "python -m compileall -q "
            "tests\\winui\\test_large_owned_folder_gui.py"
        )
        self.assertEqual(set(), validator.detect_stages(command))
        validator.validate_request(request(command=command))

    def test_actual_gui_python_invocation_is_detected(self):
        command = (
            "python -X utf8 tests\\winui\\test_large_owned_folder_gui.py "
            "--items 2300 --configuration Release"
        )
        self.assertEqual({"gui"}, validator.detect_stages(command))
        data = request(
            configuration="Release",
            validation_kind=["gui"],
            invalidated_evidence={"gui": "GUI harness changed"},
            command=command,
        )
        validator.validate_request(data)

    def test_undeclared_actual_gui_invocation_is_rejected(self):
        data = request(
            command=(
                "python -X utf8 tests\\winui\\test_large_owned_folder_gui.py "
                "--items 2300 --configuration Release"
            )
        )
        with self.assertRaisesRegex(
            validator.RequestError,
            "undeclared validation stage",
        ):
            validator.validate_request(data)


if __name__ == "__main__":
    unittest.main()
