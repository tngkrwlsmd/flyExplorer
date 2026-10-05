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


def focused_request(**overrides):
    previous = "2" * 40
    data = request(
        request_mode="validation",
        configuration="Release",
        validation_plan=["installed-gui-lifecycle"],
        retry_scope="focused-reuse",
        retry_reason="prior build and package passed; retry lifecycle harness only",
        reuse_evidence={
            "run_id": 12345,
            "candidate_sha": previous,
            "validated_targets":["release-build", "package", "provenance"],
        },
        command="python -X utf8 tests\winui\test_installed_lifecycle.py",
    )
    data.update(overrides)
    return data


class RemoteRequestPreflightContract(unittest.TestCase):
    def test_diagnostic_shape_passes_without_validation_metadata_duplication(self):
        normalized = validator.validate_request(request())
        self.assertEqual(normalized["request_mode"], "diagnostic")
        self.assertEqual(normalized["validation_plan"], [])
        self.assertEqual(normalized["retry_scope"], "diagnostic")

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
        self.assertEqual(normalized["retry_scope"], "full")

    def test_free_form_command_is_not_reparsed_as_a_second_stage_declaration(self):
        normalized = validator.validate_request(
            request(
                command=(
                    "python -X utf8 tests\winui\test_large_owned_folder_gui.py "
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
                    "python tools\winui\high_contrast_acceptance.py"
                ),
                harness_revision="hc-harness-v2",
            )
        )
        self.assertEqual(
            normalized["validation_plan"],
            ["source", "high-contrast-gui"],
        )

    def test_focused_reuse_requires_structured_prior_evidence(self):
        normalized = validator.validate_request(focused_request())
        self.assertEqual(normalized["retry_scope"], "focused-reuse")
        self.assertEqual(
            normalized["reuse_evidence"]["validated_targets"],
            ["release-build", "package", "provenance"],
        )

        with self.assertRaisesRegex(
            validator.RequestError, "requires reuse_evidence"
        ):
            validator.validate_request(
                focused_request(reuse_evidence=None)
            )

    def test_focused_reuse_must_not_repeat_reused_targets(self):
        with self.assertRaisesRegex(
            validator.RequestError, "must not rerun reused targets"
        ):
            validator.validate_request(
                focused_request(
                    validation_plan=["package", "installed-gui-lifecycle"]
                )
            )

    def test_focused_reuse_blocks_known_expensive_entry_points(self):
        for command in (
            r".\build.bat Release",
            r".\package.bat Release",
            r".\clean.bat build",
            r"python packaging\provenance.py --write",
            r"python tools\winui\run_checks.py full",
        ):
            with self.subTest(command=command):
                with self.assertRaisesRegex(
                    validator.RequestError, "must not rebuild/repackage"
                ):
                    validator.validate_request(
                        focused_request(command=command)
                    )

    def test_diagnostic_cannot_claim_reused_validation_evidence(self):
        with self.assertRaisesRegex(
            validator.RequestError, "must not declare reuse_evidence"
        ):
            validator.validate_request(
                request(
                    reuse_evidence={
                        "run_id": 1,
                        "candidate_sha": "2" * 40,
                        "validated_targets": ["package"],
                    }
                )
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
