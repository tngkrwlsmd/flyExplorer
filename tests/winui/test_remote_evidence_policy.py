"""Pure policy tests for Remote Windows Task prior-evidence gating."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import urllib.request
import unittest
import zipfile

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
    }


def reuse_archive(*, candidate="b" * 40):
    files = {
        "reuse/runtime.zip": b"runtime-archive",
        "reuse/PAYLOAD_PROVENANCE.json": b'{"format":"demo"}',
        "reuse/flyExplorer-Setup-x64.exe": b"setup-bytes",
    }
    targets = {
        "release-build": "reuse/runtime.zip",
        "provenance": "reuse/PAYLOAD_PROVENANCE.json",
        "package": "reuse/flyExplorer-Setup-x64.exe",
    }
    manifest = {
        "format": "flyexplorer-reuse-evidence-v1",
        "logical_unit": "packaging",
        "candidate_sha": candidate,
        "targets": {
            target: {
                "path": path,
                "bytes": len(files[path]),
                "sha256": hashlib.sha256(files[path]).hexdigest(),
            }
            for target, path in targets.items()
        },
    }
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("reuse-evidence.json", json.dumps(manifest))
        for path, raw in files.items():
            archive.writestr(path, raw)
    return stream.getvalue()


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

    def test_focused_reuse_requires_real_hashed_artifacts(self):
        data = reuse_archive()
        files = policy.validate_reuse_artifacts(
            data=data,
            logical_unit="packaging",
            candidate_sha="b" * 40,
            targets=["release-build", "provenance", "package"],
        )
        self.assertEqual(
            {
                "reuse/runtime.zip",
                "reuse/PAYLOAD_PROVENANCE.json",
                "reuse/flyExplorer-Setup-x64.exe",
            },
            set(files),
        )

    def test_focused_reuse_extracts_only_verified_files(self):
        files = policy.validate_reuse_artifacts(
            data=reuse_archive(),
            logical_unit="packaging",
            candidate_sha="b" * 40,
            targets=["release-build", "package"],
        )
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "reuse"
            policy.extract_reuse_artifacts(files, output)
            self.assertEqual(b"runtime-archive", (output/"runtime.zip").read_bytes())
            self.assertEqual(
                b"setup-bytes",
                (output/"flyExplorer-Setup-x64.exe").read_bytes(),
            )
            self.assertFalse((output/"PAYLOAD_PROVENANCE.json").exists())

    def test_log_markers_without_binary_bundle_are_not_reusable(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("remote-result.json", "{}")
        with self.assertRaisesRegex(
            policy.EvidencePolicyError, "no reuse-evidence.json"
        ):
            policy.validate_reuse_artifacts(
                data=stream.getvalue(),
                logical_unit="packaging",
                candidate_sha="b" * 40,
                targets=["package"],
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
