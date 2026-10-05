"""Behavior contracts for the zero-run remote request validator."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "winui" / "validate_remote_request.py"

spec = importlib.util.spec_from_file_location(
    "validate_remote_request", MODULE_PATH
)
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
        "request_mode": "diagnostic",
        "configuration": "none",
        "validation_plan": [],
        "working_directory": "",
        "command": "Write-Output 'inspection only'",
    }
    data.update(overrides)
    return data


class RemoteRequestPreflightContract(unittest.TestCase):
    def test_diagnostic_shape_passes_without_validation_metadata_duplication(self):
        normalized = validator.validate_request(request())
        self.assertEqual(normalized["request_mode"], "diagnostic")
        self.assertEqual(normalized["validation_plan"], [])

    def test_validation_requires_configuration_and_plan(self):
        with self.assertRaisesRegex(
            validator.RequestError, "Debug or Release"
        ):
            validator.validate_request(
                request(
                    request_mode="validation",
                    validation_plan=["source"],
                )
            )
        with self.assertRaisesRegex(
            validator.RequestError, "validation_plan"
        ):
            validator.validate_request(
                request(
                    request_mode="validation",
                    configuration="Release",
                    validation_plan=[],
                )
            )

    def test_new_schema_rejects_legacy_double_declaration(self):
        with self.assertRaisesRegex(
            validator.RequestError, "must not also declare"
        ):
            validator.validate_request(
                request(validation_kind=["source"])
            )

    def test_legacy_request_is_readable_during_migration(self):
        data = request()
        data.pop("request_mode")
        data.pop("validation_plan")
        data["validation_kind"] = ["source", "gui"]
        data["configuration"] = "Release"
        normalized = validator.validate_request(data)
        self.assertEqual(normalized["request_mode"], "validation")
        self.assertEqual(normalized["validation_plan"], ["source", "gui"])

    def test_free_form_command_is_not_reparsed_as_a_second_stage_declaration(self):
        normalized = validator.validate_request(
            request(
                command=(
                    "python -X utf8 tests\\winui\\test_large_owned_folder_gui.py "
                    "--items 2300 --configuration Release"
                )
            )
        )
        self.assertEqual(normalized["request_mode"], "diagnostic")

    def test_validation_accepts_logical_targets_beyond_fixed_stage_enum(self):
        normalized = validator.validate_request(
            request(
                request_mode="validation",
                configuration="Release",
                validation_plan=["source", "high-contrast-gui"],
                command=(
                    "python tools\\winui\\high_contrast_acceptance.py"
                ),
                harness_revision="hc-harness-v2",
            )
        )
        self.assertEqual(
            normalized["validation_plan"],
            ["source", "high-contrast-gui"],
        )

    def test_multiline_retry_reason_is_rejected(self):
        with self.assertRaisesRegex(
            validator.RequestError, "single line"
        ):
            validator.validate_request(
                request(retry_reason="first\nsecond")
            )


if __name__ == "__main__":
    unittest.main()
