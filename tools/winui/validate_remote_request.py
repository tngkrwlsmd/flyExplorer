"""Zero-run validator for the small control/remote-shell request schema."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
LOGICAL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{1,95}$")
PLAN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,95}$")
DEPRECATED_FIELDS = {
    "validation_kind",
    "retry_scope",
    "retry_reason",
    "harness_revision",
    "reuse_evidence",
}


class RequestError(ValueError):
    pass


def _targets(raw: object) -> list[str]:
    if not isinstance(raw, list):
        raise RequestError("validation_plan must be a JSON array")
    values = [str(item).strip().lower() for item in raw]
    if any(not item or not PLAN_RE.fullmatch(item) for item in values):
        raise RequestError("validation_plan contains an invalid logical target")
    if len(values) != len(set(values)):
        raise RequestError("validation_plan must not contain duplicate targets")
    return values


def validate_request(data: dict) -> dict:
    if not isinstance(data, dict):
        raise RequestError("request root must be a JSON object")
    deprecated = sorted(DEPRECATED_FIELDS & set(data))
    if deprecated:
        raise RequestError(
            "deprecated remote control-plane fields are not accepted: "
            + ", ".join(deprecated)
        )

    normalized = dict(data)
    request_id = str(data.get("request_id", "")).strip()
    expected = str(data.get("expected_main_sha", "")).strip().lower()
    candidate = str(data.get("candidate_sha", "")).strip().lower()
    logical = str(data.get("logical_unit", "")).strip()
    mode = str(data.get("request_mode", "")).strip().lower()
    configuration = str(data.get("configuration", "")).strip()
    command = str(data.get("command", ""))
    plan = _targets(data.get("validation_plan", []))

    if not request_id:
        raise RequestError("request_id is required")
    if not SHA_RE.fullmatch(expected):
        raise RequestError("expected_main_sha must be a 40-character Git SHA")
    if not SHA_RE.fullmatch(candidate):
        raise RequestError("candidate_sha must be a 40-character Git SHA")
    if not LOGICAL_RE.fullmatch(logical):
        raise RequestError("logical_unit must be a stable 2-96 character identifier")
    if mode not in {"diagnostic", "validation"}:
        raise RequestError("request_mode must be diagnostic or validation")
    if not command.strip():
        raise RequestError("command is required")

    if mode == "diagnostic":
        if configuration != "none":
            raise RequestError("diagnostic requests must use configuration none")
        if plan:
            raise RequestError("diagnostic requests must leave validation_plan empty")
    else:
        if configuration not in {"Debug", "Release"}:
            raise RequestError(
                "validation requests must declare Debug or Release configuration"
            )
        if not plan:
            raise RequestError("validation requests must declare validation_plan")

    normalized.update(
        expected_main_sha=expected,
        candidate_sha=candidate,
        logical_unit=logical,
        request_mode=mode,
        configuration=configuration,
        validation_plan=plan,
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
