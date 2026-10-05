"""Release source bundle and binary/source identity contracts."""

from pathlib import Path
import importlib.util
import json
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE_BUNDLE = ROOT / "packaging" / "source_bundle.py"
RELEASE_IDENTITY = ROOT / "packaging" / "release_identity.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


source_bundle = load_module(SOURCE_BUNDLE, "fly_source_bundle_contract")
release_identity = load_module(RELEASE_IDENTITY, "fly_release_identity_contract")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def create_repo(root: Path) -> str:
    git(root, "init")
    git(root, "config", "user.name", "flyExplorer test")
    git(root, "config", "user.email", "test@flyexplorer.local")
    (root / "app" / "winui").mkdir(parents=True)
    (root / "README").write_text("source bundle fixture\n", encoding="utf-8")
    (root / "build.bat").write_text("@echo off\necho build\n", encoding="utf-8")
    (root / "app" / "winui" / "product_version.h").write_text(
        '#define FLYEXPLORER_VERSION_STRING "1.2.3.4"\n',
        encoding="utf-8",
    )
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture")
    return git(root, "rev-parse", "HEAD").lower()


class ReleaseSourceBundleContract(unittest.TestCase):
    def test_bundle_is_deterministic_and_exactly_matches_git_tree(self):
        with tempfile.TemporaryDirectory(prefix="fly-source-bundle-") as raw:
            root = Path(raw)
            revision = create_repo(root)
            one = root / "out-one"
            two = root / "out-two"
            bundle1, manifest1, data1 = source_bundle.write_bundle(
                root=root, revision=revision, output_dir=one
            )
            bundle2, manifest2, data2 = source_bundle.write_bundle(
                root=root, revision=revision, output_dir=two
            )
            self.assertEqual(data1["bundle_sha256"], data2["bundle_sha256"])
            self.assertEqual(bundle1.read_bytes(), bundle2.read_bytes())
            self.assertEqual(data1["source_revision"], revision)
            self.assertEqual(3, data1["file_count"])
            checked = source_bundle.verify_bundle(
                root=root,
                revision=revision,
                bundle=bundle1,
                manifest_path=manifest1,
            )
            self.assertEqual(data1, checked)
            self.assertTrue(manifest2.is_file())

    def test_bundle_rejects_tampering_and_unsafe_paths(self):
        with tempfile.TemporaryDirectory(prefix="fly-source-tamper-") as raw:
            root = Path(raw)
            revision = create_repo(root)
            bundle, manifest, _ = source_bundle.write_bundle(
                root=root, revision=revision, output_dir=root / "out"
            )
            bundle.write_bytes(bundle.read_bytes() + b"tamper")
            with self.assertRaises(source_bundle.SourceBundleError):
                source_bundle.verify_bundle(
                    root=root,
                    revision=revision,
                    bundle=bundle,
                    manifest_path=manifest,
                )
            for path in ("../escape.txt", "/absolute.txt", "dir\\alias.txt"):
                with self.assertRaises(source_bundle.SourceBundleError):
                    source_bundle.safe_archive_path(path)

    def test_release_identity_binds_source_runtime_and_setup_hashes(self):
        with tempfile.TemporaryDirectory(prefix="fly-release-identity-") as raw:
            root = Path(raw)
            revision = create_repo(root)
            bundle, manifest_path, manifest = source_bundle.write_bundle(
                root=root, revision=revision, output_dir=root / "out"
            )
            provenance = root / "PAYLOAD_PROVENANCE.json"
            provenance_md = root / "PAYLOAD_PROVENANCE.md"
            setup = root / "flyExplorer-Setup-x64.exe"
            provenance.write_text(
                json.dumps(
                    {
                        "format": "flyexplorer-runtime-provenance-v1",
                        "runtime_source_revision": revision,
                        "runtime_manifest_sha256": "a" * 64,
                        "runtime_file_count": 3,
                        "product_generated_file_count": 2,
                        "nuget_matched_file_count": 1,
                    }
                ),
                encoding="utf-8",
            )
            provenance_md.write_text("provenance\n", encoding="utf-8")
            setup.write_bytes(b"unsigned-setup")
            identity = release_identity.build_identity(
                source_manifest_path=manifest_path,
                source_bundle_path=bundle,
                setup_path=setup,
                provenance_path=provenance,
                provenance_markdown_path=provenance_md,
                root=root,
            )
            self.assertEqual(revision, identity["binary_source_revision"])
            self.assertEqual(manifest["source_tree_sha"], identity["source_tree_sha"])
            self.assertEqual(manifest["bundle_sha256"], identity["source_bundle"]["sha256"])
            self.assertEqual("a" * 64, identity["runtime"]["manifest_sha256"])
            self.assertEqual("unsigned", identity["setup"]["signing_status"])
            self.assertEqual("private-evidence-only", identity["publication_status"])

            broken = json.loads(provenance.read_text(encoding="utf-8"))
            broken["runtime_source_revision"] = "0" * 40
            provenance.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(release_identity.ReleaseIdentityError):
                release_identity.build_identity(
                    source_manifest_path=manifest_path,
                    source_bundle_path=bundle,
                    setup_path=setup,
                    provenance_path=provenance,
                    provenance_markdown_path=provenance_md,
                    root=root,
                )

    def test_current_release_source_policy_is_fail_closed(self):
        bundle = SOURCE_BUNDLE.read_text(encoding="utf-8")
        identity = RELEASE_IDENTITY.read_text(encoding="utf-8")
        for token in (
            "MAX_FILES",
            "MAX_FILE_BYTES",
            "MAX_TOTAL_BYTES",
            "portable path collision",
            "symbolic links are not allowed",
            "ZIP_STORED",
            "bundle_sha256",
            "source_tree_sha",
        ):
            self.assertIn(token, bundle)
        for token in (
            "binary_source_revision",
            "source_tree_sha",
            "source_bundle",
            "runtime_manifest_sha256",
            "setup",
            "sha256",
            "public_distribution_clearance",
            "not-cleared",
        ):
            self.assertIn(token, identity)


if __name__ == "__main__":
    unittest.main()
