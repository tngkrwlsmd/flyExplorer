"""Pure policy tests for Remote Windows Task prior-evidence gating."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import urllib.request
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "winui" / "remote_evidence_policy.py"

spec = importlib.util.spec_from_file_location("remote_evidence_policy", MODULE_PATH)
assert spec is not None and spec.loader is not None
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def result(category, *, candidate="a" * 40, plan=None):
    return {
        "logical_unit": "packaging",
        "candidate_sha": candidate,
        "validation_plan": plan
        or ["release-build", "provenance", "package", "installed-gui-lifecycle"],
        "failure_category": category,
        "stages": {"COMMAND": "FAIL"},
    }


class RemoteEvidencePolicyTests(unittest.TestCase):
    def test_unclassified_failure_blocks_validation_when_still_unknown(self):
        with self.assertRaisesRegex(
            policy.EvidencePolicyError, "still unclassified"
        ):
            policy.evaluate_previous(
                result=result("COMMAND_FAILURE_UNCLASSIFIED"),
                log_text="unknown failure",
                request_mode="validation",
                retry_scope="full",
            )

    def test_current_classifier_can_resolve_old_unclassified_timeout(self):
        category = policy.evaluate_previous(
            result=result("COMMAND_FAILURE_UNCLASSIFIED"),
            log_text=(
                'File "tests/winui/test_installed_lifecycle.py"\n'
                "subprocess.TimeoutExpired: Command ['C:\\x\\flyExplorer.exe'] "
                "timed out after 16 seconds\n"
                "AssertionError: owned installed app did not close within "
                "the accepted 16-second budget"
            ),
            request_mode="validation",
            retry_scope="focused-reuse",
        )
        self.assertEqual("INSTALLED_APP_SHUTDOWN_TIMEOUT", category)

    def test_current_classifier_can_resolve_legacy_missing_category(self):
        category = policy.evaluate_previous(
            result=result(None),
            log_text=(
                'File "tests/winui/test_installed_lifecycle.py"\n'
                "subprocess.TimeoutExpired: Command ['C:\\x\\flyExplorer.exe'] "
                "timed out after 16 seconds\n"
                "AssertionError: owned installed app did not close within "
                "the accepted 16-second budget"
            ),
            request_mode="validation",
            retry_scope="focused-reuse",
        )
        self.assertEqual("INSTALLED_APP_SHUTDOWN_TIMEOUT", category)

    def test_classified_harness_boundary_rejects_full_repeat(self):
        with self.assertRaisesRegex(
            policy.EvidencePolicyError, "requires focused-reuse"
        ):
            policy.evaluate_previous(
                result=result("INSTALLED_APP_SHUTDOWN_TIMEOUT"),
                log_text="",
                request_mode="validation",
                retry_scope="full",
            )

    def test_diagnostic_remains_available_for_unknown_failure(self):
        category = policy.evaluate_previous(
            result=result("COMMAND_FAILURE_UNCLASSIFIED"),
            log_text="unknown failure",
            request_mode="diagnostic",
            retry_scope="diagnostic",
        )
        self.assertEqual("COMMAND_FAILURE_UNCLASSIFIED", category)

    def test_cross_host_redirect_drops_authorization_header(self):
        request = urllib.request.Request(
            "https://api.github.com/repos/o/r/actions/runs/1/logs",
            headers={"Authorization": "Bearer secret"},
        )
        redirected = policy._SafeRedirectHandler().redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://results-receiver.actions.githubusercontent.com/signed/path",
        )
        self.assertIsNotNone(redirected)
        self.assertIsNone(redirected.get_header("Authorization"))

    def test_same_host_redirect_preserves_authorization_header(self):
        request = urllib.request.Request(
            "https://api.github.com/repos/o/r/actions/runs/1/logs",
            headers={"Authorization": "Bearer secret"},
        )
        redirected = policy._SafeRedirectHandler().redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://api.github.com/repos/o/r/actions/runs/1/logs?x=1",
        )
        self.assertEqual(
            "Bearer secret",
            redirected.get_header("Authorization"),
        )

    def test_packaging_success_markers_allow_focused_reuse(self):
        policy.validate_reuse(
            result=result(
                "INSTALLED_APP_SHUTDOWN_TIMEOUT",
                candidate="b" * 40,
            ),
            log_text=(
                "PROVENANCE_CHECK=PASS\n"
                "PAYLOAD_FILES=326\n"
                "SETUP=C:\\temp\\flyExplorer-Setup-x64.exe\n"
            ),
            logical_unit="packaging",
            candidate_sha="b" * 40,
            targets=["release-build", "provenance", "package"],
        )

    def test_reuse_rejects_missing_success_marker(self):
        with self.assertRaisesRegex(
            policy.EvidencePolicyError, "lacks prior success evidence"
        ):
            policy.validate_reuse(
                result=result("INSTALLED_APP_SHUTDOWN_TIMEOUT"),
                log_text="PROVENANCE_CHECK=PASS",
                logical_unit="packaging",
                candidate_sha="a" * 40,
                targets=["package"],
            )


if __name__ == "__main__":
    unittest.main()
