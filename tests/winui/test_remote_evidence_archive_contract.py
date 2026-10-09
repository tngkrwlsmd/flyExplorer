"""Privacy and boundedness contracts for Git-backed remote evidence."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "store_remote_evidence", ROOT / "tools/winui/store_remote_evidence.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

SHA = "a" * 40
REPO = "tngkrwlsmd/flyExplorer"


class RemoteEvidenceArchiveContract(unittest.TestCase):
    def fixture(self, source):
        result = {
            "request_id": "sample-run",
            "request_mode": "validation",
            "candidate_sha": SHA,
            "logical_unit": "search-v3-indexed-extension",
            "validation_plan": ["source", "gui"],
            "stages": {
                "REQUEST_VALIDATION": "PASS",
                "STATIC_PREFLIGHT": "PASS",
                "RUNNER_HEALTH": "PASS",
                "COMMAND": "PASS",
            },
            "failure_category": None,
            "unexpected_private_field": "MY_SECRET_TOKEN",
        }
        (source / "remote-result.json").write_text(
            json.dumps(result), encoding="utf-8"
        )
        (source / "remote-command.log").write_text(
            "INDEXED_EXTENSION_GUI=PASS\n"
            "M19_NATIVE_TESTED_HELPER_CONFIG Release\n"
            "C:\\Users\\person\\Private\\path\n"
            "Write-Host 'INJECTED_SOURCE=PASS'\n"
            "token=MY_SECRET_TOKEN\n",
            encoding="utf-8",
        )

    def test_snapshot_only_carries_allowlisted_fields_and_markers(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, dest = root / "source", root / "repo"
            source.mkdir()
            dest.mkdir()
            self.fixture(source)
            (source / "remote-command-error.txt").write_text(
                "PASSWORD=MY_SECRET_TOKEN", encoding="utf-8"
            )
            (source / "private.bmp").write_bytes(b"BM" + b"x" * 100)
            out = mod.prepare_snapshot(
                source, dest, "37912684233", REPO, SHA, 1, "failure"
            )
            self.assertEqual(
                ["manifest.json", "markers.json", "remote-result.json"],
                sorted(p.name for p in out.iterdir()),
            )
            saved = "\n".join(p.read_text("utf-8") for p in out.iterdir())
            self.assertNotIn("MY_SECRET_TOKEN", saved)
            self.assertNotIn("C:\\Users\\", saved)
            self.assertNotIn("INJECTED_SOURCE", saved)
            self.assertIn("INDEXED_EXTENSION_GUI", saved)
            result = json.loads((out / "remote-result.json").read_text("utf-8"))
            self.assertNotIn("unexpected_private_field", result)
            self.assertEqual(
                "failure",
                json.loads((out / "manifest.json").read_text("utf-8"))[
                    "job_state_before_archive"
                ],
            )

    def test_missing_result_is_not_fabricated_as_pass(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, dest = root / "source", root / "repo"
            source.mkdir()
            dest.mkdir()
            out = mod.prepare_snapshot(
                source, dest, "11", REPO, SHA, 1, "failure"
            )
            manifest = json.loads((out / "manifest.json").read_text("utf-8"))
            self.assertEqual("missing_or_oversized", manifest["source_result"])
            self.assertFalse((out / "remote-result.json").exists())
            self.assertEqual(["manifest.json"], [p.name for p in out.iterdir()])

    def test_validation_rejects_unsafe_data_and_identifiers(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, dest = root / "source", root / "repo"
            source.mkdir()
            dest.mkdir()
            self.fixture(source)
            for run_id in ("../other", "", "123/456"):
                with self.subTest(run_id=run_id):
                    with self.assertRaises(ValueError):
                        mod.prepare_snapshot(source, dest, run_id, REPO, SHA, 1, "success")
            raw = json.loads((source / "remote-result.json").read_text("utf-8"))
            raw["request_id"] = "../../private"
            (source / "remote-result.json").write_text(
                json.dumps(raw), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                mod.prepare_snapshot(source, dest, "18", REPO, SHA, 1, "success")

    def test_oversize_and_symlink_files_are_not_copied(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source, dest = root / "source", root / "repo"
            source.mkdir()
            dest.mkdir()
            self.fixture(source)
            (source / "remote-command.log").write_bytes(
                b"PRIVATE_CONTENT" * (mod.MAX_LOG_BYTES // 14 + 2)
            )
            (source / "remote-result.json").write_bytes(
                b"x" * (mod.MAX_JSON_BYTES + 1)
            )
            out = mod.prepare_snapshot(source, dest, "200", REPO, SHA, 1, "success")
            self.assertFalse((out / "markers.json").exists())
            self.assertFalse((out / "remote-result.json").exists())
            self.assertTrue((out / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
