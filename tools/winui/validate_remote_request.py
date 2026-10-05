"""Static validator for control/remote-shell request.json.

New requests declare one mode and one validation plan. The command is no longer
regex-inferred back into validation metadata. Legacy validation_kind requests
remain readable during migration.
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


class RequestError(ValueError):
    pass


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
        raw_plan = data.get("validation_plan", [])
    else:
        if not isinstance(legacy_kinds, list) or not legacy_kinds:
            raise RequestError(
                "request_mode is required for new requests; legacy validation_kind "
                "must be a non-empty array"
            )
        normalized_legacy = [
            str(item).strip().lower() for item in legacy_kinds
        ]
        if normalized_legacy == ["none"]:
            explicit_mode = "diagnostic"
            raw_plan = []
        else:
            explicit_mode = "validation"
            raw_plan = normalized_legacy

    if not isinstance(raw_plan, list):
        raise RequestError("validation_plan must be a JSON array")
    plan = [str(item).strip().lower() for item in raw_plan]
    if any(not item or not PLAN_RE.fullmatch(item) for item in plan):
        raise RequestError("validation_plan contains an invalid logical target")
    if len(set(plan)) != len(plan):
        raise RequestError("validation_plan must not contain duplicate targets")

    normalized = dict(data)
    normalized["request_mode"] = explicit_mode
    normalized["validation_plan"] = plan
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
            raise RequestError(
                "diagnostic requests must use configuration none"
            )
        if plan:
            raise RequestError(
                "diagnostic requests must leave validation_plan empty"
            )
    else:
        if configuration not in {"Debug", "Release"}:
            raise RequestError(
                "validation requests must declare Debug or Release configuration"
            )
        if not plan:
            raise RequestError(
                "validation requests must declare validation_plan"
            )

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
        f"plan={','.join(normalized['validation_plan']) or '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
