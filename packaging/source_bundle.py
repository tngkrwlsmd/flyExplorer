from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "out" / "release"
FORMAT = "flyexplorer-source-bundle-v1"
MAX_FILES = 20_000
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class SourceBundleError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_text(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if result.returncode:
        raise SourceBundleError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def resolve_revision(root: Path, revision: str) -> tuple[str, str]:
    source_revision = _git_text(root, "rev-parse", "--verify", f"{revision}^{{commit}}").lower()
    tree_sha = _git_text(root, "rev-parse", "--verify", f"{source_revision}^{{tree}}").lower()
    return source_revision, tree_sha


def safe_archive_path(path: str) -> str:
    if not path or path.startswith("/") or "\\" in path:
        raise SourceBundleError(f"unsafe tracked path: {path!r}")
    pure = PurePosixPath(path)
    if any(part in ("", ".", "..") for part in pure.parts):
        raise SourceBundleError(f"unsafe tracked path: {path!r}")
    if unicodedata.normalize("NFC", path) != path:
        raise SourceBundleError(f"tracked path is not NFC-normalized: {path!r}")
    return path


def list_tree(root: Path, revision: str) -> tuple[str, str, list[dict[str, object]]]:
    source_revision, tree_sha = resolve_revision(root, revision)
    result = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "-l", "--full-tree", source_revision],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise SourceBundleError(
            result.stderr.decode("utf-8", "replace").strip() or "git ls-tree failed"
        )
    entries: list[dict[str, object]] = []
    seen: dict[str, str] = {}
    total = 0
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, raw_path = raw.split(b"\t", 1)
            mode_b, kind_b, object_b, size_b = metadata.split(maxsplit=3)
            path = raw_path.decode("utf-8", "strict")
            mode = mode_b.decode("ascii")
            kind = kind_b.decode("ascii")
            object_id = object_b.decode("ascii").lower()
        except (ValueError, UnicodeDecodeError) as exc:
            raise SourceBundleError("malformed or non-UTF-8 git tree entry") from exc
        safe_archive_path(path)
        if kind != "blob":
            raise SourceBundleError(f"unsupported tracked object {kind} at {path}")
        if mode == "120000":
            raise SourceBundleError(f"symbolic links are not allowed in source bundle: {path}")
        if mode not in ("100644", "100755"):
            raise SourceBundleError(f"unsupported tracked mode {mode} at {path}")
        try:
            size = int(size_b.decode("ascii"))
        except ValueError as exc:
            raise SourceBundleError(f"missing tracked blob size for {path}") from exc
        if size < 0 or size > MAX_FILE_BYTES:
            raise SourceBundleError(f"tracked file exceeds source-bundle file bound: {path}")
        collision_key = unicodedata.normalize("NFC", path).casefold()
        prior = seen.get(collision_key)
        if prior is not None and prior != path:
            raise SourceBundleError(f"portable path collision: {prior!r} vs {path!r}")
        seen[collision_key] = path
        total += size
        if total > MAX_TOTAL_BYTES:
            raise SourceBundleError("tracked source exceeds source-bundle total-byte bound")
        entries.append({"path": path, "mode": mode, "git_object": object_id, "bytes": size})
        if len(entries) > MAX_FILES:
            raise SourceBundleError("tracked source exceeds source-bundle file-count bound")
    if not entries:
        raise SourceBundleError("source revision contains no tracked files")
    return source_revision, tree_sha, entries


def _read_blobs(root: Path, entries: list[dict[str, object]]) -> list[bytes]:
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None
    blobs: list[bytes] = []
    try:
        for entry in entries:
            object_id = str(entry["git_object"])
            process.stdin.write(object_id.encode("ascii") + b"\n")
            process.stdin.flush()
            header = process.stdout.readline().rstrip(b"\n").split()
            if len(header) != 3 or header[0].decode("ascii").lower() != object_id:
                raise SourceBundleError(f"unexpected git cat-file header for {entry['path']}")
            kind = header[1].decode("ascii")
            size = int(header[2])
            if kind != "blob" or size != int(entry["bytes"]):
                raise SourceBundleError(f"git blob metadata mismatch for {entry['path']}")
            data = process.stdout.read(size)
            if len(data) != size or process.stdout.read(1) != b"\n":
                raise SourceBundleError(f"truncated git blob for {entry['path']}")
            blobs.append(data)
    finally:
        try:
            process.stdin.close()
        except OSError:
            pass
        return_code = process.wait(timeout=10)
        if return_code:
            stderr = process.stderr.read().decode("utf-8", "replace").strip() if process.stderr else ""
            raise SourceBundleError(stderr or "git cat-file --batch failed")
    return blobs


def write_bundle(
    *,
    root: Path = ROOT,
    revision: str = "HEAD",
    output_dir: Path = DEFAULT_OUTPUT,
) -> tuple[Path, Path, dict[str, object]]:
    source_revision, tree_sha, entries = list_tree(root, revision)
    blobs = _read_blobs(root, entries)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"flyExplorer-source-{source_revision}/"
    bundle = output_dir / f"flyExplorer-source-{source_revision}.zip"
    manifest_path = output_dir / f"flyExplorer-source-{source_revision}.manifest.json"
    file_manifest: list[dict[str, object]] = []
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for entry, data in zip(entries, blobs, strict=True):
            path = str(entry["path"])
            info = zipfile.ZipInfo(prefix + path, FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (int(str(entry["mode"]), 8) & 0xFFFF) << 16
            info.flag_bits |= 0x800
            archive.writestr(info, data)
            file_manifest.append({**entry, "sha256": hashlib.sha256(data).hexdigest()})
    manifest: dict[str, object] = {
        "format": FORMAT,
        "source_revision": source_revision,
        "source_tree_sha": tree_sha,
        "archive_prefix": prefix,
        "file_count": len(file_manifest),
        "total_file_bytes": sum(int(item["bytes"]) for item in file_manifest),
        "bundle_file": bundle.name,
        "bundle_bytes": bundle.stat().st_size,
        "bundle_sha256": sha256_file(bundle),
        "files": file_manifest,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return bundle, manifest_path, manifest


def verify_bundle(
    *,
    root: Path = ROOT,
    revision: str,
    bundle: Path,
    manifest_path: Path,
) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("format") != FORMAT:
        raise SourceBundleError("source bundle manifest format mismatch")
    source_revision, tree_sha, entries = list_tree(root, revision)
    if manifest.get("source_revision") != source_revision:
        raise SourceBundleError("source bundle revision mismatch")
    if manifest.get("source_tree_sha") != tree_sha:
        raise SourceBundleError("source bundle tree mismatch")
    if manifest.get("bundle_file") != bundle.name:
        raise SourceBundleError("source bundle filename mismatch")
    if manifest.get("bundle_bytes") != bundle.stat().st_size:
        raise SourceBundleError("source bundle size mismatch")
    if manifest.get("bundle_sha256") != sha256_file(bundle):
        raise SourceBundleError("source bundle SHA-256 mismatch")

    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, list) or len(manifest_files) != len(entries):
        raise SourceBundleError("source bundle file manifest count mismatch")
    expected_by_path = {str(item["path"]): item for item in entries}
    manifest_by_path = {
        str(item.get("path")): item for item in manifest_files if isinstance(item, dict)
    }
    if set(manifest_by_path) != set(expected_by_path):
        raise SourceBundleError("source bundle manifest paths do not match git tree")
    for path, expected in expected_by_path.items():
        actual = manifest_by_path[path]
        for key in ("mode", "git_object", "bytes"):
            if actual.get(key) != expected[key]:
                raise SourceBundleError(f"source manifest {key} mismatch for {path}")

    prefix = str(manifest.get("archive_prefix") or "")
    if prefix != f"flyExplorer-source-{source_revision}/":
        raise SourceBundleError("source bundle prefix mismatch")
    with zipfile.ZipFile(bundle, "r") as archive:
        infos = archive.infolist()
        if len(infos) != len(entries):
            raise SourceBundleError("source bundle archive entry count mismatch")
        seen: set[str] = set()
        for info in infos:
            if info.is_dir() or not info.filename.startswith(prefix):
                raise SourceBundleError(f"unexpected source archive entry: {info.filename}")
            relative = info.filename[len(prefix):]
            safe_archive_path(relative)
            if relative in seen:
                raise SourceBundleError(f"duplicate source archive entry: {relative}")
            seen.add(relative)
            expected = manifest_by_path.get(relative)
            if expected is None:
                raise SourceBundleError(f"unexpected source archive path: {relative}")
            data = archive.read(info)
            if len(data) != int(expected["bytes"]):
                raise SourceBundleError(f"source archive size mismatch for {relative}")
            if hashlib.sha256(data).hexdigest() != expected.get("sha256"):
                raise SourceBundleError(f"source archive hash mismatch for {relative}")
            if info.compress_type != zipfile.ZIP_STORED:
                raise SourceBundleError(f"source archive entry is not stored deterministically: {relative}")
        if seen != set(expected_by_path):
            raise SourceBundleError("source bundle archive is missing tracked files")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    try:
        source_revision, _ = resolve_revision(ROOT, args.revision)
        default_bundle = args.output_dir / f"flyExplorer-source-{source_revision}.zip"
        default_manifest = args.output_dir / f"flyExplorer-source-{source_revision}.manifest.json"
        if args.write:
            bundle, manifest_path, manifest = write_bundle(
                root=ROOT, revision=source_revision, output_dir=args.output_dir
            )
        else:
            bundle = args.bundle or default_bundle
            manifest_path = args.manifest or default_manifest
            manifest = verify_bundle(
                root=ROOT,
                revision=source_revision,
                bundle=bundle,
                manifest_path=manifest_path,
            )
    except (OSError, ValueError, json.JSONDecodeError, SourceBundleError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"SOURCE_BUNDLE_REVISION={manifest['source_revision']}")
    print(f"SOURCE_BUNDLE_TREE_SHA={manifest['source_tree_sha']}")
    print(f"SOURCE_BUNDLE_FILES={manifest['file_count']}")
    print(f"SOURCE_BUNDLE_TOTAL_FILE_BYTES={manifest['total_file_bytes']}")
    print(f"SOURCE_BUNDLE_SHA256={manifest['bundle_sha256']}")
    print(f"SOURCE_BUNDLE={bundle}")
    print(f"SOURCE_BUNDLE_MANIFEST={manifest_path}")
    print("SOURCE_BUNDLE_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
