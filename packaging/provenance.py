from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELEASE = ROOT / "out" / "winui" / "Release"
DEFAULT_ASSETS = ROOT / "out" / "obj" / "winui" / "Release" / "project.assets.json"
DEFAULT_PACKAGES = ROOT / ".cache" / "nuget" / "packages"
NOTICE_ROOT = ROOT / "packaging" / "licenses" / "nuget"
MARKDOWN_PATH = ROOT / "packaging" / "licenses" / "PAYLOAD_PROVENANCE.md"
JSON_PATH = ROOT / "packaging" / "licenses" / "PAYLOAD_PROVENANCE.json"

BAD_RUNTIME_SUFFIXES = {".pdb", ".obj", ".lib", ".exp", ".ilk", ".py", ".cpp", ".h"}
RETIRED_RUNTIME_TOKENS = (
    "flyexplorerwinuishell",
    "phase5",
    "islandbridge",
    "legacy/mfc",
)


class ProvenanceError(RuntimeError):
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
    if result.returncode or len(value) != 40:
        raise ProvenanceError(result.stderr.strip() or "cannot resolve source revision")
    return value


def _is_linked(path: Path) -> bool:
    if path.is_symlink():
        return True
    checker = getattr(path, "is_junction", None)
    return bool(checker and checker())


def runtime_files(release_root: Path) -> list[Path]:
    if not release_root.is_dir():
        raise ProvenanceError(f"Release runtime missing: {release_root}")
    files: list[Path] = []
    for base, dirs, names in os.walk(release_root, followlinks=False):
        base_path = Path(base)
        for name in list(dirs):
            child = base_path / name
            if _is_linked(child):
                raise ProvenanceError(f"linked runtime directory is not allowed: {child}")
        for name in names:
            path = base_path / name
            if _is_linked(path):
                raise ProvenanceError(f"linked runtime file is not allowed: {path}")
            rel = path.relative_to(release_root)
            if rel.suffix.lower() in BAD_RUNTIME_SUFFIXES:
                raise ProvenanceError(f"non-runtime build/source file in Release output: {rel}")
            lower = rel.as_posix().lower()
            if any(token in lower for token in RETIRED_RUNTIME_TOKENS):
                raise ProvenanceError(f"retired artifact in Release output: {rel}")
            files.append(path)
    if not files:
        raise ProvenanceError("Release runtime contains no files")
    return sorted(files, key=lambda item: item.relative_to(release_root).as_posix().lower())


def asset_packages(assets_path: Path, packages_root: Path) -> dict[tuple[str, str], Path]:
    if not assets_path.is_file():
        raise ProvenanceError(f"project.assets.json missing: {assets_path}")
    data = json.loads(assets_path.read_text(encoding="utf-8-sig"))
    libraries = data.get("libraries")
    if not isinstance(libraries, dict):
        raise ProvenanceError("project.assets.json libraries map is missing")
    packages: dict[tuple[str, str], Path] = {}
    for key, metadata in libraries.items():
        if not isinstance(metadata, dict) or metadata.get("type") != "package":
            continue
        if "/" not in key:
            raise ProvenanceError(f"malformed package identity: {key}")
        package, version = key.rsplit("/", 1)
        cache_rel = metadata.get("path")
        if not isinstance(cache_rel, str) or not cache_rel.strip():
            cache_rel = f"{package.lower()}/{version}"
        package_root = packages_root / Path(cache_rel)
        if not package_root.is_dir():
            raise ProvenanceError(
                f"restored package directory missing for {package} {version}: {package_root}"
            )
        packages[(package.lower(), version)] = package_root
    if not packages:
        raise ProvenanceError("no restored packages found in project.assets.json")
    return packages


def _package_hash_index(
    packages: dict[tuple[str, str], Path],
    wanted_sizes: set[int],
) -> dict[tuple[int, str], list[tuple[str, str, str]]]:
    index: dict[tuple[int, str], list[tuple[str, str, str]]] = {}
    for (package, version), package_root in sorted(packages.items()):
        for base, dirs, names in os.walk(package_root, followlinks=False):
            base_path = Path(base)
            dirs[:] = [name for name in dirs if not _is_linked(base_path / name)]
            for name in names:
                path = base_path / name
                if _is_linked(path):
                    continue
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                if size not in wanted_sizes:
                    continue
                digest = sha256_file(path)
                rel = path.relative_to(package_root).as_posix()
                index.setdefault((size, digest), []).append((package, version, rel))
    return index


def _runtime_manifest_digest(entries: Iterable[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for entry in entries:
        digest.update(str(entry["path"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(entry["bytes"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(entry["sha256"]).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _notice_packages(
    origins: set[tuple[str, str]],
    all_packages: dict[tuple[str, str], Path],
    notice_root: Path,
) -> list[dict[str, object]]:
    required = set(origins)
    required.update(
        identity for identity in all_packages
        if identity[0] == "microsoft.windowsappsdk"
    )
    result: list[dict[str, object]] = []
    for package, version in sorted(required):
        directory = notice_root / package / version
        files = (
            sorted(
                path.relative_to(directory).as_posix()
                for path in directory.rglob("*")
                if path.is_file()
            )
            if directory.is_dir()
            else []
        )
        if not files:
            raise ProvenanceError(
                f"tracked redistribution notice missing for {package} {version}"
            )
        result.append(
            {"package": package, "version": version, "notice_files": files}
        )
    return result


def build_manifest(
    *,
    release_root: Path = DEFAULT_RELEASE,
    assets_path: Path = DEFAULT_ASSETS,
    packages_root: Path = DEFAULT_PACKAGES,
    notice_root: Path = NOTICE_ROOT,
    source_revision: str | None = None,
    generated_date: str | None = None,
) -> dict[str, object]:
    runtime = runtime_files(release_root)
    packages = asset_packages(assets_path, packages_root)
    sizes = {path.stat().st_size for path in runtime}
    package_index = _package_hash_index(packages, sizes)

    entries: list[dict[str, object]] = []
    origins: set[tuple[str, str]] = set()
    counts: Counter[tuple[str, str]] = Counter()
    product_count = 0

    for path in runtime:
        rel = path.relative_to(release_root).as_posix()
        size = path.stat().st_size
        digest = sha256_file(path)
        matches = package_index.get((size, digest), [])
        identities = sorted({(package, version) for package, version, _ in matches})
        if len(identities) > 1:
            rendered = ", ".join(f"{package} {version}" for package, version in identities)
            raise ProvenanceError(f"ambiguous NuGet byte origin for {rel}: {rendered}")
        if identities:
            package, version = identities[0]
            package_paths = sorted(
                package_path
                for match_package, match_version, package_path in matches
                if (match_package, match_version) == (package, version)
            )
            origin = {
                "kind": "nuget",
                "package": package,
                "version": version,
                "package_path": package_paths[0],
            }
            origins.add((package, version))
            counts[(package, version)] += 1
        else:
            origin = {"kind": "product-generated"}
            product_count += 1
        entries.append(
            {
                "path": rel,
                "bytes": size,
                "sha256": digest,
                "origin": origin,
            }
        )

    revision = source_revision or git_revision()
    date = generated_date or dt.date.today().isoformat()
    notices = _notice_packages(origins, packages, notice_root)
    package_counts = [
        {"package": package, "version": version, "files": count}
        for (package, version), count in sorted(counts.items())
    ]
    return {
        "format": "flyexplorer-runtime-provenance-v1",
        "generated_date": date,
        "runtime_source_revision": revision,
        "runtime_file_count": len(entries),
        "product_generated_file_count": product_count,
        "nuget_matched_file_count": len(entries) - product_count,
        "runtime_manifest_sha256": _runtime_manifest_digest(entries),
        "package_match_counts": package_counts,
        "notice_packages": notices,
        "files": entries,
    }


def render_markdown(manifest: dict[str, object]) -> str:
    lines = [
        f"# Current packaged payload provenance snapshot — {manifest['generated_date']}",
        "",
        "This snapshot is generated from the exact canonical Release runtime before",
        "distribution materials are added to the installer. Runtime bytes are matched",
        "by SHA-256 against package versions in the build's project.assets.json and",
        "the repository-local NuGet cache.",
        "",
        f"- Runtime source revision: `{manifest['runtime_source_revision']}`",
        f"- Runtime files before distribution materials: **{manifest['runtime_file_count']}**",
        f"- Product/generated files with no NuGet byte match: **{manifest['product_generated_file_count']}**",
        f"- Files with an exact NuGet package byte match: **{manifest['nuget_matched_file_count']}**",
        f"- Runtime manifest SHA-256: `{manifest['runtime_manifest_sha256']}`",
        "",
        "## Exact NuGet payload matches",
        "",
    ]
    package_counts = manifest["package_match_counts"]
    assert isinstance(package_counts, list)
    if package_counts:
        for item in package_counts:
            assert isinstance(item, dict)
            lines.append(
                f"- `{item['package']} {item['version']}`: {item['files']} files"
            )
    else:
        lines.append("- None")

    lines += ["", "## Product/generated files", ""]
    files = manifest["files"]
    assert isinstance(files, list)
    product = [
        item for item in files
        if isinstance(item, dict)
        and isinstance(item.get("origin"), dict)
        and item["origin"].get("kind") == "product-generated"
    ]
    if product:
        for item in product:
            lines.append(
                f"- `{item['path']}` — {item['bytes']} bytes — "
                f"`sha256:{item['sha256']}`"
            )
    else:
        lines.append("- None")

    lines += ["", "## Tracked redistribution notices", ""]
    notices = manifest["notice_packages"]
    assert isinstance(notices, list)
    for item in notices:
        assert isinstance(item, dict)
        lines.append(
            f"- `{item['package']} {item['version']}`: "
            + ", ".join(f"`{name}`" for name in item["notice_files"])
        )

    lines += [
        "",
        "## Private installer dependency notices",
        "",
        "- The installer carries the active Fluent icon notice from `CREDITS`.",
        "- `packaging/licenses/nuget/` must contain notice/license material for every",
        "  package version identified above, plus the top-level Microsoft.WindowsAppSDK",
        "  package terms from the active restore graph.",
        "- `PAYLOAD_PROVENANCE.json` is the machine-readable per-file SHA-256 inventory",
        "  corresponding to this summary.",
        "- Direct build-only PackageReferences whose bytes do not appear in the Release",
        "  runtime are not classified as redistributed runtime components by this audit.",
        "",
        "Any runtime byte set, restored package origin, or tracked notice change makes",
        "this snapshot stale and must fail packaging until the audit is regenerated.",
        "",
    ]
    return "\n".join(lines)


def _snapshot_signature(manifest: dict[str, object]) -> dict[str, object]:
    return {
        key: manifest[key]
        for key in (
            "format",
            "runtime_file_count",
            "product_generated_file_count",
            "nuget_matched_file_count",
            "runtime_manifest_sha256",
            "package_match_counts",
            "notice_packages",
            "files",
        )
    }


def write_snapshot(**kwargs: object) -> dict[str, object]:
    manifest = build_manifest(**kwargs)
    JSON_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    MARKDOWN_PATH.write_text(
        render_markdown(manifest),
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def verify_snapshot(**kwargs: object) -> dict[str, object]:
    if not JSON_PATH.is_file() or not MARKDOWN_PATH.is_file():
        raise ProvenanceError("tracked payload provenance snapshot is missing")
    tracked = json.loads(JSON_PATH.read_text(encoding="utf-8-sig"))
    current = build_manifest(**kwargs)
    if _snapshot_signature(tracked) != _snapshot_signature(current):
        raise ProvenanceError(
            "tracked payload provenance does not match the current Release runtime; "
            "run packaging/provenance.py --write after a clean Release build"
        )
    expected_markdown = render_markdown(tracked)
    if MARKDOWN_PATH.read_text(encoding="utf-8-sig") != expected_markdown:
        raise ProvenanceError("PAYLOAD_PROVENANCE.md does not match its JSON inventory")
    return tracked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        manifest = write_snapshot() if args.write else verify_snapshot()
    except (OSError, ValueError, json.JSONDecodeError, ProvenanceError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"PROVENANCE_RUNTIME_FILES={manifest['runtime_file_count']}")
    print(f"PROVENANCE_PRODUCT_FILES={manifest['product_generated_file_count']}")
    print(f"PROVENANCE_NUGET_FILES={manifest['nuget_matched_file_count']}")
    print(f"PROVENANCE_MANIFEST_SHA256={manifest['runtime_manifest_sha256']}")
    print("PROVENANCE_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
