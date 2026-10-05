"""Behavior contracts for the zero-run remote request validator."""
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
        "request_mode": "diagnostic",
        "configuration": "none",
        "validation_plan": [],
        "working_directory": "",
        "command": "Write-Output 'inspection only'",
    }
    data.update(overrides)
    return data


class RemoteRequestPreflightContract(unittest.TestCase):
    def test_diagnostic_shape_is_small_and_valid(self):
        normalized = validator.validate_request(request())
        self.assertEqual("diagnostic", normalized["request_mode"])
        self.assertEqual([], normalized["validation_plan"])

    def test_validation_requires_one_configuration_and_a_plan(self):
        with self.assertRaisesRegex(validator.RequestError, "Debug or Release"):
            validator.validate_request(
                request(request_mode="validation", validation_plan=["search"])
            )
        normalized = validator.validate_request(
            request(
                request_mode="validation",
                configuration="Release",
                validation_plan=["search", "build"],
            )
        )
        self.assertEqual(["search", "build"], normalized["validation_plan"])

    def test_duplicate_or_invalid_targets_are_rejected(self):
        with self.assertRaisesRegex(validator.RequestError, "duplicate"):
            validator.validate_request(
                request(
                    request_mode="validation",
                    configuration="Release",
                    validation_plan=["search", "search"],
                )
            )
        with self.assertRaisesRegex(validator.RequestError, "invalid logical"):
            validator.validate_request(
                request(
                    request_mode="validation",
                    configuration="Release",
                    validation_plan=["bad target"],
                )
            )

    def test_deprecated_retry_and_legacy_fields_are_rejected(self):
        for field, value in (
            ("validation_kind", ["source"]),
            ("retry_scope", "focused-reuse"),
            ("retry_reason", "old retry path"),
            ("harness_revision", "old"),
            ("reuse_evidence", {"run_id": 1}),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(
                    validator.RequestError, "deprecated remote control-plane"
                ):
                    validator.validate_request(request(**{field: value}))

    def test_command_is_not_reparsed_into_a_second_stage_declaration(self):
        normalized = validator.validate_request(
            request(command=r"python tests\winui\test_large_owned_folder_gui.py --items 2300")
        )
        self.assertEqual("diagnostic", normalized["request_mode"])


if __name__ == "__main__":
    unittest.main()
