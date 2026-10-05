from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROVENANCE = ROOT / "packaging" / "licenses" / "PAYLOAD_PROVENANCE.json"
DEFAULT_PROVENANCE_MD = ROOT / "packaging" / "licenses" / "PAYLOAD_PROVENANCE.md"
DEFAULT_SETUP = ROOT / "out" / "package" / "flyExplorer-Setup-x64.exe"
DEFAULT_OUTPUT = ROOT / "out" / "release" / "RELEASE_IDENTITY.json"
FORMAT = "flyexplorer-release-identity-v1"


class ReleaseIdentityError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_revision(root: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    value = result.stdout.strip().lower()
    if result.returncode or not re.fullmatch(r"[0-9a-f]{40,64}", value):
        raise ReleaseIdentityError(result.stderr.strip() or "cannot resolve identity generation revision")
    return value


def product_version(root: Path = ROOT) -> str:
    text = (root / "app" / "winui" / "product_version.h").read_text(encoding="utf-8")
    match = re.search(
        r'#define\s+FLYEXPLORER_VERSION_STRING\s+"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"',
        text,
    )
    if not match:
        raise ReleaseIdentityError("product version is missing or malformed")
    return match.group(1)


def build_identity(
    *,
    source_manifest_path: Path,
    source_bundle_path: Path,
    setup_path: Path,
    provenance_path: Path = DEFAULT_PROVENANCE,
    provenance_markdown_path: Path = DEFAULT_PROVENANCE_MD,
    root: Path = ROOT,
    release_tag: str | None = None,
) -> dict[str, object]:
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8-sig"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8-sig"))
    if source_manifest.get("format") != "flyexplorer-source-bundle-v1":
        raise ReleaseIdentityError("source bundle manifest format mismatch")
    source_revision = str(source_manifest.get("source_revision") or "").lower()
    runtime_revision = str(provenance.get("runtime_source_revision") or "").lower()
    if not source_revision or source_revision != runtime_revision:
        raise ReleaseIdentityError(
            "source bundle revision does not match runtime provenance source revision"
        )
    if source_manifest.get("bundle_file") != source_bundle_path.name:
        raise ReleaseIdentityError("source bundle filename does not match source manifest")
    if source_manifest.get("bundle_bytes") != source_bundle_path.stat().st_size:
        raise ReleaseIdentityError("source bundle size does not match source manifest")
    if source_manifest.get("bundle_sha256") != sha256_file(source_bundle_path):
        raise ReleaseIdentityError("source bundle hash does not match source manifest")
    if not setup_path.is_file():
        raise ReleaseIdentityError(f"setup artifact missing: {setup_path}")
    if provenance.get("format") != "flyexplorer-runtime-provenance-v1":
        raise ReleaseIdentityError("runtime provenance format mismatch")
    return {
        "format": FORMAT,
        "product": "flyExplorer",
        "product_version": product_version(root),
        "release_tag": release_tag,
        "publication_status": "private-evidence-only",
        "public_distribution_clearance": "not-cleared",
        "identity_generation_revision": git_revision(root),
        "binary_source_revision": source_revision,
        "source_tree_sha": source_manifest.get("source_tree_sha"),
        "source_bundle": {
            "file": source_bundle_path.name,
            "bytes": source_bundle_path.stat().st_size,
            "sha256": sha256_file(source_bundle_path),
            "manifest_file": source_manifest_path.name,
            "manifest_bytes": source_manifest_path.stat().st_size,
            "manifest_sha256": sha256_file(source_manifest_path),
            "tracked_file_count": source_manifest.get("file_count"),
            "tracked_file_bytes": source_manifest.get("total_file_bytes"),
        },
        "runtime": {
            "source_revision": runtime_revision,
            "manifest_sha256": provenance.get("runtime_manifest_sha256"),
            "file_count": provenance.get("runtime_file_count"),
            "product_generated_file_count": provenance.get("product_generated_file_count"),
            "nuget_matched_file_count": provenance.get("nuget_matched_file_count"),
            "provenance_json_sha256": sha256_file(provenance_path),
            "provenance_markdown_sha256": sha256_file(provenance_markdown_path),
        },
        "setup": {
            "file": setup_path.name,
            "bytes": setup_path.stat().st_size,
            "sha256": sha256_file(setup_path),
            "signing_status": "unsigned",
        },
    }


def write_identity(*, output: Path = DEFAULT_OUTPUT, **kwargs: object) -> dict[str, object]:
    identity = build_identity(**kwargs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(identity, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return identity


def verify_identity(*, identity_path: Path, **kwargs: object) -> dict[str, object]:
    tracked = json.loads(identity_path.read_text(encoding="utf-8-sig"))
    current = build_identity(**kwargs)
    if tracked != current:
        raise ReleaseIdentityError("release identity does not match current binary/source artifacts")
    return tracked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-bundle", type=Path, required=True)
    parser.add_argument("--setup", type=Path, default=DEFAULT_SETUP)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--provenance-markdown", type=Path, default=DEFAULT_PROVENANCE_MD)
    parser.add_argument("--identity", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--release-tag")
    args = parser.parse_args()
    kwargs = {
        "source_manifest_path": args.source_manifest,
        "source_bundle_path": args.source_bundle,
        "setup_path": args.setup,
        "provenance_path": args.provenance,
        "provenance_markdown_path": args.provenance_markdown,
        "root": ROOT,
        "release_tag": args.release_tag,
    }
    try:
        identity = (
            write_identity(output=args.identity, **kwargs)
            if args.write
            else verify_identity(identity_path=args.identity, **kwargs)
        )
    except (OSError, ValueError, json.JSONDecodeError, ReleaseIdentityError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"RELEASE_IDENTITY_SOURCE_REVISION={identity['binary_source_revision']}")
    print(f"RELEASE_IDENTITY_SOURCE_BUNDLE_SHA256={identity['source_bundle']['sha256']}")
    print(f"RELEASE_IDENTITY_RUNTIME_MANIFEST_SHA256={identity['runtime']['manifest_sha256']}")
    print(f"RELEASE_IDENTITY_SETUP_SHA256={identity['setup']['sha256']}")
    print(f"RELEASE_IDENTITY={args.identity}")
    print("RELEASE_IDENTITY_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
