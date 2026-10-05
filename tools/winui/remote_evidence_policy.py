"""GitHub Actions evidence policy for Remote Windows Task retries.

This tool runs before an expensive retry. It reads prior workflow artifacts/logs
through the GitHub Actions API, reclassifies older unclassified failures with the
current classifier, and requires focused evidence reuse for harness/automation
failures. Stdlib-only by design.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile

try:
    from classify_remote_failure import classify
except ModuleNotFoundError:
    import importlib.util

    _path = Path(__file__).with_name("classify_remote_failure.py")
    _spec = importlib.util.spec_from_file_location("classify_remote_failure", _path)
    assert _spec is not None and _spec.loader is not None
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    classify = _module.classify

UNCLASSIFIED = "COMMAND_FAILURE_UNCLASSIFIED"
FOCUSED_ONLY_CATEGORIES = {
    "INSTALLED_APP_SHUTDOWN_TIMEOUT",
    "INSTALLED_APP_WINDOW_CLOSE_TIMEOUT",
    "INSTALLED_APP_PROCESS_EXIT_TIMEOUT",
    "HARNESS_PROGRAMMING_FAILURE",
    "HARNESS_CONTRACT_FAILURE",
    "AUTOMATION_API_FAILURE",
    "AUTOMATION_DISCOVERY_FAILURE",
    "AUTOMATION_TIMEOUT_FAILURE",
    "SUBPROCESS_TIMEOUT_FAILURE",
}
REUSE_TARGET_MARKERS = {
    # PROVENANCE_CHECK occurs only after the command's canonical Release build
    # succeeds and the current runtime can be inventoried.
    "release-build": ("PROVENANCE_CHECK=PASS",),
    "provenance": ("PROVENANCE_CHECK=PASS",),
    # package.py prints these only after the installer executable exists.
    "package": ("PAYLOAD_FILES=", "SETUP="),
}


class EvidencePolicyError(RuntimeError):
    pass


def effective_category(result: dict, log_text: str) -> str | None:
    value = str(result.get("failure_category") or "").strip()
    if value == UNCLASSIFIED:
        return classify(log_text)
    return value or None


def evaluate_previous(
    *,
    result: dict,
    log_text: str,
    request_mode: str,
    retry_scope: str,
) -> str | None:
    category = effective_category(result, log_text)
    if request_mode != "validation":
        return category
    if category == UNCLASSIFIED:
        raise EvidencePolicyError(
            "previous failure is still unclassified; run a focused diagnostic "
            "before another validation"
        )
    if category in FOCUSED_ONLY_CATEGORIES and retry_scope != "focused-reuse":
        raise EvidencePolicyError(
            f"previous failure category {category} requires focused-reuse; "
            "do not repeat the full validation plan"
        )
    return category


def validate_reuse(
    *,
    result: dict,
    log_text: str,
    logical_unit: str,
    candidate_sha: str,
    targets: list[str],
) -> None:
    if str(result.get("logical_unit") or "") != logical_unit:
        raise EvidencePolicyError("reuse evidence logical_unit does not match")
    if str(result.get("candidate_sha") or "").lower() != candidate_sha.lower():
        raise EvidencePolicyError("reuse evidence candidate_sha does not match")

    prior_plan = {
        str(item).strip().lower()
        for item in result.get("validation_plan", [])
        if str(item).strip()
    }
    missing_plan = sorted(set(targets) - prior_plan)
    if missing_plan:
        raise EvidencePolicyError(
            "reuse targets were not part of the prior validation plan: "
            + ", ".join(missing_plan)
        )

    for target in targets:
        markers = REUSE_TARGET_MARKERS.get(target)
        if markers is None:
            raise EvidencePolicyError(
                f"reuse target has no canonical success markers: {target}"
            )
        missing = [marker for marker in markers if marker not in log_text]
        if missing:
            raise EvidencePolicyError(
                f"reuse target {target} lacks prior success evidence: "
                + ", ".join(missing)
            )


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never forward the GitHub bearer token to signed storage redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(
            req, fp, code, msg, headers, newurl
        )
        if redirected is None:
            return None
        old_host = urllib.parse.urlsplit(req.full_url).hostname
        new_host = urllib.parse.urlsplit(newurl).hostname
        if old_host != new_host:
            redirected.remove_header("Authorization")
        return redirected


def _request(url: str, token: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "flyExplorer-remote-evidence-policy",
        },
    )
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    with opener.open(request, timeout=30) as response:
        return response.read()


def _json(url: str, token: str) -> dict:
    return json.loads(_request(url, token).decode("utf-8-sig"))


def _zip_text(data: bytes) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            if name.lower().endswith((".txt", ".log")):
                chunks.append(
                    archive.read(name).decode("utf-8-sig", errors="replace")
                )
    return "\n".join(chunks)


def run_artifact_zip(
    repository: str,
    token: str,
    run_id: int,
) -> bytes | None:
    payload = _json(
        f"https://api.github.com/repos/{repository}/actions/runs/{run_id}/artifacts",
        token,
    )
    expected = f"flyexplorer-remote-evidence-{run_id}"
    artifact = next(
        (
            item
            for item in payload.get("artifacts", [])
            if item.get("name") == expected and not item.get("expired")
        ),
        None,
    )
    if artifact is None:
        return None
    return _request(
        f"https://api.github.com/repos/{repository}/actions/artifacts/"
        f"{artifact['id']}/zip",
        token,
    )


def _zip_json(data: bytes, name: str) -> dict | None:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        try:
            raw = archive.read(name)
        except KeyError:
            return None
    value = json.loads(raw.decode("utf-8-sig"))
    return value if isinstance(value, dict) else None


def run_artifact_result(
    repository: str,
    token: str,
    run_id: int,
) -> dict | None:
    data = run_artifact_zip(repository, token, run_id)
    return None if data is None else _zip_json(data, "remote-result.json")


def validate_reuse_artifacts(
    *,
    data: bytes,
    logical_unit: str,
    candidate_sha: str,
    targets: list[str],
) -> dict[str, bytes]:
    manifest = _zip_json(data, "reuse-evidence.json")
    if manifest is None:
        raise EvidencePolicyError(
            "reuse run has no reuse-evidence.json; prior PASS logs alone are "
            "not a reusable binary artifact"
        )
    if manifest.get("format") != "flyexplorer-reuse-evidence-v1":
        raise EvidencePolicyError("reuse-evidence.json format is unsupported")
    if str(manifest.get("logical_unit") or "") != logical_unit:
        raise EvidencePolicyError("reuse artifact logical_unit does not match")
    if str(manifest.get("candidate_sha") or "").lower() != candidate_sha.lower():
        raise EvidencePolicyError("reuse artifact candidate_sha does not match")
    declared = manifest.get("targets")
    if not isinstance(declared, dict):
        raise EvidencePolicyError("reuse artifact targets map is missing")

    extracted: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = set(archive.namelist())
        for target in targets:
            item = declared.get(target)
            if not isinstance(item, dict):
                raise EvidencePolicyError(
                    f"reuse artifact does not preserve target: {target}"
                )
            path = str(item.get("path") or "").replace("\\", "/")
            expected_hash = str(item.get("sha256") or "").lower()
            expected_bytes = item.get("bytes")
            parts = Path(path).parts
            if (
                not path.startswith("reuse/")
                or not path
                or ".." in parts
                or path not in names
            ):
                raise EvidencePolicyError(
                    f"reuse artifact path is invalid or missing for {target}: {path}"
                )
            raw = archive.read(path)
            if not isinstance(expected_bytes, int) or expected_bytes != len(raw):
                raise EvidencePolicyError(
                    f"reuse artifact byte count mismatch for {target}"
                )
            digest = hashlib.sha256(raw).hexdigest()
            if expected_hash != digest:
                raise EvidencePolicyError(
                    f"reuse artifact SHA-256 mismatch for {target}"
                )
            extracted[path] = raw
    return extracted


def extract_reuse_artifacts(files: dict[str, bytes], output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    for path, raw in files.items():
        rel = Path(path).relative_to("reuse")
        target = output / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)


def run_log_text(repository: str, token: str, run_id: int) -> str:
    data = _request(
        f"https://api.github.com/repos/{repository}/actions/runs/{run_id}/logs",
        token,
    )
    return _zip_text(data)


def latest_same_unit(
    repository: str,
    token: str,
    logical_unit: str,
    current_run_id: int,
) -> tuple[int, dict, str] | None:
    payload = _json(
        f"https://api.github.com/repos/{repository}/actions/runs"
        "?branch=control%2Fremote-shell&status=completed&per_page=10",
        token,
    )
    for run in payload.get("workflow_runs", []):
        run_id = int(run.get("id") or 0)
        if not run_id or run_id == current_run_id:
            continue
        result = run_artifact_result(repository, token, run_id)
        if result is None or str(result.get("logical_unit") or "") != logical_unit:
            continue
        return run_id, result, run_log_text(repository, token, run_id)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument(
        "--token",
        default=os.environ.get("GH_EVIDENCE_TOKEN", ""),
    )
    parser.add_argument("--logical-unit", required=True)
    parser.add_argument("--current-run-id", type=int, required=True)
    parser.add_argument(
        "--request-mode", choices=("diagnostic", "validation"), required=True
    )
    parser.add_argument(
        "--retry-scope",
        choices=("diagnostic", "full", "focused-reuse"),
        required=True,
    )
    parser.add_argument("--reuse-run-id", type=int)
    parser.add_argument("--reuse-candidate-sha", default="")
    parser.add_argument("--reused-target", action="append", default=[])
    parser.add_argument("--extract-reuse-dir", type=Path)
    args = parser.parse_args(argv)
    if not args.token:
        print("REMOTE_EVIDENCE_POLICY=FAIL: GitHub Actions token is required", file=sys.stderr)
        return 3

    try:
        previous = latest_same_unit(
            args.repository,
            args.token,
            args.logical_unit,
            args.current_run_id,
        )
        if previous is not None:
            previous_id, previous_result, previous_log = previous
            category = evaluate_previous(
                result=previous_result,
                log_text=previous_log,
                request_mode=args.request_mode,
                retry_scope=args.retry_scope,
            )
            print(
                f"PRIOR_REMOTE_RESULT run_id={previous_id} "
                f"category={category or '-'}"
            )
            if (
                str(previous_result.get("failure_category") or "").strip()
                == UNCLASSIFIED
                and category
                and category != UNCLASSIFIED
            ):
                print(
                    f"PRIOR_FAILURE_RECLASSIFIED run_id={previous_id} "
                    f"category={category}"
                )

        if args.retry_scope == "focused-reuse":
            if not args.reuse_run_id:
                raise EvidencePolicyError("focused-reuse requires reuse run id")
            reuse_zip = run_artifact_zip(
                args.repository, args.token, args.reuse_run_id
            )
            if reuse_zip is None:
                raise EvidencePolicyError("reuse run has no remote evidence artifact")
            reuse_result = _zip_json(reuse_zip, "remote-result.json")
            if reuse_result is None:
                raise EvidencePolicyError("reuse run has no remote-result artifact")
            reuse_log = run_log_text(
                args.repository, args.token, args.reuse_run_id
            )
            validate_reuse(
                result=reuse_result,
                log_text=reuse_log,
                logical_unit=args.logical_unit,
                candidate_sha=args.reuse_candidate_sha,
                targets=args.reused_target,
            )
            reusable_files = validate_reuse_artifacts(
                data=reuse_zip,
                logical_unit=args.logical_unit,
                candidate_sha=args.reuse_candidate_sha,
                targets=args.reused_target,
            )
            if args.extract_reuse_dir is None:
                raise EvidencePolicyError(
                    "focused-reuse requires --extract-reuse-dir"
                )
            extract_reuse_artifacts(reusable_files, args.extract_reuse_dir)
            print(
                f"REMOTE_EVIDENCE_REUSE=PASS run_id={args.reuse_run_id} "
                f"targets={','.join(args.reused_target)} "
                f"files={len(reusable_files)}"
            )
    except (
        EvidencePolicyError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        urllib.error.URLError,
        zipfile.BadZipFile,
    ) as exc:
        print(f"REMOTE_EVIDENCE_POLICY=FAIL: {exc}", file=sys.stderr)
        return 3

    print("REMOTE_EVIDENCE_POLICY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
