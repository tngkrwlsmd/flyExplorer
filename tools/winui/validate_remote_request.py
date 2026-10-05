"""Static validator for control/remote-shell request.json.

Validation requests declare a plan plus an execution scope. A focused-reuse
retry must name the earlier evidence it reuses and may not invoke known
build/package entry points again. The command is not regex-inferred back into
validation metadata; these checks are safety boundaries, not stage discovery.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
LOGICAL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{1,95}$")
PLAN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,95}$")
REVISION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
FOCUSED_REUSE_FORBIDDEN = (
    "build.bat",
    "package.bat",
    "clean.bat build",
    "provenance.py --write",
    "run_checks.py full",
)


class RequestError(ValueError):
    pass


def _normalize_targets(raw: object, field: str) -> list[str]:
    if not isinstance(raw, list):
        raise RequestError(f"{field} must be a JSON array")
    values = [str(item).strip().lower() for item in raw]
    if any(not item or not PLAN_RE.fullmatch(item) for item in values):
        raise RequestError(f"{field} contains an invalid logical target")
    if len(set(values)) != len(values):
        raise RequestError(f"{field} must not contain duplicate targets")
    return values


def normalize_request(data: dict) -> dict:
    if not isinstance(data, dict):
        raise RequestError("request root must be a JSON object")

    explicit_mode = str(data.get("request_mode", "")).strip().lower()
    legacy_kinds = data.get("validation_kind")
    if explicit_mode:
        if explicit_mode not in {"diagnostic", "validation"}:
            raise RequestError("request_mode must be diagnostic or validation")
        if legacy_kinds is not None:
            raise RequestError(
                "new request_mode schema must not also declare validation_kind"
            )
        plan = _normalize_targets(data.get("validation_plan", []), "validation_plan")
    else:
        if not isinstance(legacy_kinds, list) or not legacy_kinds:
            raise RequestError(
                "request_mode is required for new requests; legacy validation_kind "
                "must be a non-empty array"
            )
        normalized_legacy = [str(item).strip().lower() for item in legacy_kinds]
        if normalized_legacy == ["none"]:
            explicit_mode = "diagnostic"
            plan = []
        else:
            explicit_mode = "validation"
            plan = _normalize_targets(normalized_legacy, "validation_kind")

    retry_scope = str(data.get("retry_scope", "")).strip().lower()
    if not retry_scope:
        retry_scope = "diagnostic" if explicit_mode == "diagnostic" else "full"
    allowed_scopes = (
        {"diagnostic"} if explicit_mode == "diagnostic"
        else {"full", "focused-reuse"}
    )
    if retry_scope not in allowed_scopes:
        raise RequestError(
            f"retry_scope must be one of {', '.join(sorted(allowed_scopes))}"
        )

    normalized = dict(data)
    normalized["request_mode"] = explicit_mode
    normalized["validation_plan"] = plan
    normalized["retry_scope"] = retry_scope
    return normalized


def validate_request(data: dict) -> dict:
    normalized = normalize_request(data)

    request_id = str(normalized.get("request_id", "")).strip()
    expected = str(normalized.get("expected_main_sha", "")).strip().lower()
    candidate = str(normalized.get("candidate_sha", "")).strip().lower()
    logical = str(normalized.get("logical_unit", "")).strip()
    configuration = str(normalized.get("configuration", "")).strip()
    command = str(normalized.get("command", ""))
    mode = normalized["request_mode"]
    plan = normalized["validation_plan"]
    retry_scope = normalized["retry_scope"]
    retry_reason = str(normalized.get("retry_reason", "")).strip()
    harness_revision = str(
        normalized.get("harness_revision", candidate)
    ).strip()

    if not request_id:
        raise RequestError("request_id is required")
    if not SHA_RE.fullmatch(expected):
        raise RequestError("expected_main_sha must be a 40-character Git SHA")
    if not SHA_RE.fullmatch(candidate):
        raise RequestError("candidate_sha must be a 40-character Git SHA")
    if not LOGICAL_RE.fullmatch(logical):
        raise RequestError(
            "logical_unit must be a stable 2-96 character identifier"
        )
    if configuration not in {"none", "Debug", "Release"}:
        raise RequestError("configuration must be none, Debug or Release")
    if not command.strip():
        raise RequestError("command is required")
    if retry_reason and ("\n" in retry_reason or "\r" in retry_reason):
        raise RequestError("retry_reason must be a single line")
    if harness_revision and not REVISION_RE.fullmatch(harness_revision):
        raise RequestError("harness_revision has an invalid identifier")

    if mode == "diagnostic":
        if configuration != "none":
            raise RequestError("diagnostic requests must use configuration none")
        if plan:
            raise RequestError(
                "diagnostic requests must leave validation_plan empty"
            )
        if normalized.get("reuse_evidence") is not None:
            raise RequestError("diagnostic requests must not declare reuse_evidence")
    else:
        if configuration not in {"Debug", "Release"}:
            raise RequestError(
                "validation requests must declare Debug or Release configuration"
            )
        if not plan:
            raise RequestError("validation requests must declare validation_plan")

    if retry_scope == "focused-reuse":
        if not retry_reason:
            raise RequestError("focused-reuse requires retry_reason")
        reuse = normalized.get("reuse_evidence")
        if not isinstance(reuse, dict):
            raise RequestError("focused-reuse requires reuse_evidence")
        run_id = reuse.get("run_id")
        reuse_candidate = str(reuse.get("candidate_sha", "")).strip().lower()
        reused_targets = _normalize_targets(
            reuse.get("validated_targets", []),
            "reuse_evidence.validated_targets",
        )
        if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
            raise RequestError("reuse_evidence.run_id must be a positive integer")
        if not SHA_RE.fullmatch(reuse_candidate):
            raise RequestError(
                "reuse_evidence.candidate_sha must be a 40-character Git SHA"
            )
        if not reused_targets:
            raise RequestError(
                "reuse_evidence.validated_targets must not be empty"
            )
        overlap = sorted(set(plan) & set(reused_targets))
        if overlap:
            raise RequestError(
                "validation_plan must not rerun reused targets: "
                + ", ".join(overlap)
            )
        lowered = re.sub(r"\s+", " ", command.lower())
        forbidden = [token for token in FOCUSED_REUSE_FORBIDDEN if token in lowered]
        if forbidden:
            raise RequestError(
                "focused-reuse command must not rebuild/repackage reused evidence: "
                + ", ".join(forbidden)
            )
        normalized["reuse_evidence"] = {
            "run_id": run_id,
            "candidate_sha": reuse_candidate,
            "validated_targets": reused_targets,
        }
    elif normalized.get("reuse_evidence") is not None:
        raise RequestError("reuse_evidence is only valid with focused-reuse")

    return normalized


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.request.read_text(encoding="utf-8"))
        normalized = validate_request(data)
    except (OSError, json.JSONDecodeError, RequestError) as exc:
        print(f"REMOTE_REQUEST_PREFLIGHT=FAIL: {exc}", file=sys.stderr)
        return 2
    print(
        "REMOTE_REQUEST_PREFLIGHT=PASS "
        f"mode={normalized['request_mode']} "
        f"scope={normalized['retry_scope']} "
        f"plan={','.join(normalized['validation_plan']) or '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
