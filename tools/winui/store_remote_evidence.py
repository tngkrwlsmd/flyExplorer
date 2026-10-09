"""Publish a small, privacy-preserving Remote Windows Task evidence snapshot.

This is intentionally NOT a general-purpose artifact uploader. The remote
command can emit arbitrary text and paths, so only strict structured fields
and pass/fail-only log markers are eligible for Git history.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

MAX_JSON_BYTES = 65536
MAX_LOG_BYTES = 2 * 1024 * 1024
MAX_MARKERS = 128
SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,95}$")
SAFE_SHA = re.compile(r"^[0-9a-f]{40}$")
SAFE_CATEGORY = re.compile(r"^[A-Z][A-Z0-9_]{0,95}$")
SAFE_STAGE = {"PASS", "FAIL", "NOT_RUN"}
ALLOWED_STAGES = {
    "REQUEST_VALIDATION", "STATIC_PREFLIGHT", "RUNNER_HEALTH", "COMMAND",
    "RUNNER_SETUP", "BASELINE", "CANDIDATE_GUI", "VISUAL", "CLEANUP",
}
MARKER = re.compile(
    r"^([A-Z][A-Z0-9_]{3,95})(?:=|\s+)"
    r"(PASS|FAIL|NOT_RUN|SKIPPED|TRUE|FALSE|True|False|0)"
    r"(?=\s|$)"
)


def regular_bytes(path: Path, limit: int) -> bytes | None:
    if path.is_symlink() or not path.is_file():
        return None
    if path.stat().st_size > limit:
        return None
    data = path.read_bytes()
    return data if len(data) <= limit else None


def safe_label(value: object, field: str) -> str:
    if not isinstance(value, str) or not SAFE_LABEL.fullmatch(value):
        raise ValueError(f"invalid {field}")
    return value


def safe_sha(value: object) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not SAFE_SHA.fullmatch(value):
        raise ValueError("invalid candidate_sha")
    return value


def structured_result(raw: bytes) -> dict:
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("remote-result must be an object")
    mode = data.get("request_mode")
    if mode not in ("diagnostic", "validation"):
        raise ValueError("invalid request_mode")
    plan = data.get("validation_plan", [])
    if not isinstance(plan, list) or len(plan) > 16:
        raise ValueError("invalid validation_plan")
    plan = [safe_label(item, "validation_plan") for item in plan]
    stages = data.get("stages")
    if not isinstance(stages, dict) or set(stages) - ALLOWED_STAGES:
        raise ValueError("invalid stages")
    if any(stage not in SAFE_STAGE for stage in stages.values()):
        raise ValueError("invalid stage outcome")
    category = data.get("failure_category")
    if category is not None and (
        not isinstance(category, str) or not SAFE_CATEGORY.fullmatch(category)
    ):
        raise ValueError("invalid failure_category")
    return {
        "request_id": safe_label(data.get("request_id"), "request_id"),
        "request_mode": mode,
        "candidate_sha": safe_sha(data.get("candidate_sha")),
        "logical_unit": safe_label(data.get("logical_unit"), "logical_unit"),
        "validation_plan": plan,
        "stages": {key: stages[key] for key in sorted(stages)},
        "failure_category": category,
    }


def failure_result(raw: bytes) -> dict:
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("check-result must be an object")
    code = data.get("exit_code")
    if type(code) is not int or code < 0 or code > 65535:
        raise ValueError("invalid exit_code")
    category = data.get("failure_category")
    if not isinstance(category, str) or not SAFE_CATEGORY.fullmatch(category):
        raise ValueError("invalid failure_category")
    return {
        "failure_category": category,
        "exit_code": code,
        "stage": safe_label(data.get("stage"), "stage"),
    }


def markers_from(source: Path) -> dict[str, str]:
    markers: dict[str, str] = {}
    for name in ("static-preflight.log", "remote-command.log"):
        raw = regular_bytes(source / name, MAX_LOG_BYTES)
        if raw is None:
            continue
        for line in raw.decode("utf-8-sig", errors="replace").splitlines():
            found = MARKER.match(line.strip())
            if found:
                key, value = found.groups()
                if key not in markers and len(markers) >= MAX_MARKERS:
                    break
                markers[key] = value.upper()
    return dict(sorted(markers.items()))


def dump_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def prepare_snapshot(
    source: Path, destination: Path, run_id: str, repository: str,
    workflow_sha: str, attempt: int, prior_job_state: str,
) -> Path:
    if not re.fullmatch(r"[1-9][0-9]{0,19}", run_id):
        raise ValueError("invalid run ID")
    if repository != "tngkrwlsmd/flyExplorer":
        raise ValueError("unexpected repository")
    if not SAFE_SHA.fullmatch(workflow_sha):
        raise ValueError("invalid workflow SHA")
    if attempt < 1 or attempt > 1000 or prior_job_state not in (
        "success", "failure", "cancelled"
    ):
        raise ValueError("invalid workflow status")
    if source.is_symlink() or not source.is_dir():
        raise ValueError("invalid source directory")
    if destination.is_symlink() or not destination.is_dir():
        raise ValueError("invalid destination directory")
    root = destination / "runs"
    if root.is_symlink():
        raise ValueError("symlink runs directory")
    root.mkdir(exist_ok=True)
    target = root / run_id
    if target.is_symlink():
        raise ValueError("symlink run directory")
    target.mkdir(exist_ok=True)
    files: list[str] = []
    raw_result = regular_bytes(source / "remote-result.json", MAX_JSON_BYTES)
    result = structured_result(raw_result) if raw_result is not None else None
    if result is not None:
        dump_json(target / "remote-result.json", result)
        files.append("remote-result.json")
    raw_failure = regular_bytes(source / "check-result.json", MAX_JSON_BYTES)
    if raw_failure is not None:
        dump_json(target / "check-result.json", failure_result(raw_failure))
        files.append("check-result.json")
    markers = markers_from(source)
    if markers:
        dump_json(target / "markers.json", markers)
        files.append("markers.json")
    manifest = {
        "schema": 1,
        "repository": repository,
        "run_id": int(run_id),
        "run_url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "run_attempt": attempt,
        "workflow_sha": workflow_sha,
        "candidate_sha": result["candidate_sha"] if result else None,
        "source_result": "available" if result else "missing_or_oversized",
        "job_state_before_archive": prior_job_state,
        "remote_result_sha256": (
            hashlib.sha256(raw_result).hexdigest() if raw_result else None
        ),
        "files": sorted(files),
        "scope": (
            "sanitized structured results and allowlisted status markers only; "
            "raw logs, credentials, binaries and desktop screenshots excluded"
        ),
    }
    dump_json(target / "manifest.json", manifest)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--workflow-sha", required=True)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--prior-job-state", required=True)
    args = parser.parse_args()
    try:
        target = prepare_snapshot(
            args.source, args.destination, args.run_id, args.repository,
            args.workflow_sha, args.attempt, args.prior_job_state
        )
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"EVIDENCE_ARCHIVE_PREPARE=FAIL reason={type(exc).__name__}")
        return 2
    print(f"EVIDENCE_ARCHIVE_PREPARE=PASS run={args.run_id} files={len(list(target.iterdir()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
