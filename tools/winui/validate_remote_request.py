"""Static validator for control/remote-shell request.json.

This module is intentionally cross-platform and has no Windows or third-party
runtime dependency. It exists so request-shape mistakes are rejected before a
Remote Windows Task is created.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ALLOWED_KINDS = {"none", "source", "build", "native", "gui", "visual"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
LOGICAL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{1,95}$")

COMMAND_BOUNDARY = r"(?:^|[;\r\n&]\s*)"
PYTHON = r"(?:py|python)(?:\.exe)?(?:\s+-\S+)*\s+"


class RequestError(ValueError):
    pass


def _has(pattern: str, command: str) -> bool:
    return re.search(pattern, command, flags=re.IGNORECASE | re.MULTILINE) is not None


def detect_stages(command: str) -> set[str]:
    """Detect only executable validation invocations, not incidental filenames."""
    stages: set[str] = set()

    if _has(
        COMMAND_BOUNDARY + r"(?:cmd\s+/c\s+)?test\.bat\s+source(?:\s|$)",
        command,
    ) or _has(r"run_checks\.py[^\r\n;&]*\bsource\b", command):
        stages.add("source")

    if _has(
        COMMAND_BOUNDARY
        + r"(?:cmd\s+/c\s+)?build\.bat\s+(?:debug|release)(?:\s|$)",
        command,
    ) or _has(
        COMMAND_BOUNDARY + r"(?:cmd\s+/c\s+)?app[\\/]winui[\\/]build\.cmd",
        command,
    ) or _has(r"run_checks\.py[^\r\n;&]*\b(?:build|full)\b", command):
        stages.add("build")

    if _has(
        COMMAND_BOUNDARY
        + PYTHON
        + r"[^\r\n;&]*(?:test_native\.py|test_process_isolation\.py)(?:\s|$)",
        command,
    ):
        stages.add("native")

    if _has(
        COMMAND_BOUNDARY
        + PYTHON
        + r"[^\r\n;&]*test_[A-Za-z0-9_]*gui\.py(?:\s|$)",
        command,
    ) or _has(r"run_checks\.py[^\r\n;&]*\b(?:gui|full)\b", command):
        stages.add("gui")

    if _has(
        COMMAND_BOUNDARY
        + PYTHON
        + r"[^\r\n;&]*(?:capture_[A-Za-z0-9_]*\.py|visual[_-]acceptance)(?:\s|$)",
        command,
    ):
        stages.add("visual")

    return stages


def validate_request(data: dict) -> None:
    if not isinstance(data, dict):
        raise RequestError("request root must be a JSON object")

    request_id = str(data.get("request_id", "")).strip()
    expected = str(data.get("expected_main_sha", "")).strip().lower()
    candidate = str(data.get("candidate_sha", "")).strip().lower()
    logical = str(data.get("logical_unit", "")).strip()
    configuration = str(data.get("configuration", "")).strip()
    kinds = data.get("validation_kind")
    evidence = data.get("invalidated_evidence")
    command = str(data.get("command", ""))

    if not request_id:
        raise RequestError("request_id is required")
    if not SHA_RE.fullmatch(expected):
        raise RequestError("expected_main_sha must be a 40-character Git SHA")
    if not SHA_RE.fullmatch(candidate):
        raise RequestError("candidate_sha must be a 40-character Git SHA")
    if not LOGICAL_RE.fullmatch(logical):
        raise RequestError("logical_unit must be a stable 2-96 character identifier")
    if configuration not in {"none", "Debug", "Release"}:
        raise RequestError("configuration must be none, Debug or Release")
    if not isinstance(kinds, list) or not kinds:
        raise RequestError("validation_kind must be a non-empty JSON array")

    normalized = [str(item).strip().lower() for item in kinds]
    if any(kind not in ALLOWED_KINDS for kind in normalized):
        raise RequestError("validation_kind contains unsupported stage")
    if len(set(normalized)) != len(normalized):
        raise RequestError("validation_kind contains duplicate stages")

    declared = set(normalized)
    if "none" in declared and declared != {"none"}:
        raise RequestError("validation_kind none cannot be combined with validation stages")

    evidence_map = evidence if isinstance(evidence, dict) else {}
    evidence_keys = {str(key).strip().lower() for key in evidence_map}
    if declared == {"none"}:
        if configuration != "none":
            raise RequestError("non-validation requests must use configuration none")
        if candidate != expected:
            raise RequestError(
                "non-validation requests must use candidate_sha equal to expected_main_sha"
            )
        if evidence_keys:
            raise RequestError(
                "non-validation requests must leave invalidated_evidence empty"
            )
    else:
        if configuration == "none":
            raise RequestError(
                "validation requests must declare Debug or Release configuration"
            )
        if not isinstance(evidence, dict):
            raise RequestError("validation requests must declare invalidated_evidence")
        missing = [
            kind
            for kind in sorted(declared)
            if not str(evidence_map.get(kind, "")).strip()
        ]
        if missing:
            raise RequestError(
                "invalidated_evidence missing reason(s): " + ", ".join(missing)
            )
        extra = sorted(evidence_keys - declared)
        if extra:
            raise RequestError(
                "invalidated_evidence contains undeclared stage(s): " + ", ".join(extra)
            )

    if not command.strip():
        raise RequestError("command is required")
    detected = detect_stages(command)
    undeclared = sorted(detected - declared)
    if undeclared:
        raise RequestError(
            "command runs undeclared validation stage(s): " + ", ".join(undeclared)
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.request.read_text(encoding="utf-8"))
        validate_request(data)
    except (OSError, json.JSONDecodeError, RequestError) as exc:
        print(f"REMOTE_REQUEST_PREFLIGHT=FAIL: {exc}", file=sys.stderr)
        return 2
    print("REMOTE_REQUEST_PREFLIGHT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
