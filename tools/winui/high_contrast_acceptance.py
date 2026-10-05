"""Orchestrate High Contrast runner setup, product acceptance, and cleanup."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from high_contrast_runner_setup import set_target
from high_contrast_state import query

ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "tests" / "winui" / "test_high_contrast_gui.py"
DEFAULT_EVIDENCE = ROOT / "logs" / "remote-evidence"


def _status() -> dict[str, str]:
    return {
        "RUNNER_SETUP": "NOT_RUN",
        "BASELINE": "NOT_RUN",
        "CANDIDATE_GUI": "NOT_RUN",
        "VISUAL": "NOT_RUN",
        "CLEANUP": "NOT_RUN",
    }


def _run_gui(exe: Path, configuration: str, prefix: str) -> tuple[int, str]:
    command = [
        sys.executable,
        "-X",
        "utf8",
        "-u",
        str(GUI),
        configuration,
        "--exe",
        str(exe),
        "--evidence-prefix",
        prefix,
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(result.stdout, end="", flush=True)
    match = re.findall(r"FAILURE_CATEGORY=([A-Z0-9_]+)", result.stdout)
    category = match[-1] if match else "GUI_ACCEPTANCE_FAILURE"
    return result.returncode, category


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--configuration", choices=("Debug", "Release"), default="Release"
    )
    parser.add_argument("--candidate-exe", type=Path)
    parser.add_argument("--baseline-exe", type=Path)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args(argv)

    candidate = args.candidate_exe or (
        ROOT / "out" / "winui" / args.configuration / "flyExplorer.exe"
    )
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.evidence_dir / "high-contrast-result.json"
    stages = _status()
    original = query()
    failure_category = ""
    started = time.time()
    exit_code = 0

    try:
        set_target(True)
        stages["RUNNER_SETUP"] = "PASS"

        if args.baseline_exe is not None:
            code, category = _run_gui(
                args.baseline_exe, args.configuration, "baseline-high-contrast"
            )
            if code:
                stages["BASELINE"] = "FAIL"
                failure_category = "BASELINE_" + category
                exit_code = 1
            else:
                stages["BASELINE"] = "PASS"
        else:
            stages["BASELINE"] = "SKIPPED"

        if exit_code == 0:
            if not candidate.is_file():
                stages["CANDIDATE_GUI"] = "FAIL"
                failure_category = "CANDIDATE_BINARY_MISSING"
                exit_code = 1
            else:
                code, category = _run_gui(
                    candidate, args.configuration, "candidate-high-contrast"
                )
                if code:
                    stages["CANDIDATE_GUI"] = "FAIL"
                    failure_category = category
                    exit_code = 1
                else:
                    stages["CANDIDATE_GUI"] = "PASS"
                    stages["VISUAL"] = "NOT_RUN"
                    print(
                        "HIGH_CONTRAST_PRODUCT_ACCEPTANCE_PASS "
                        "VISUAL_REVIEW_REQUIRED",
                        flush=True,
                    )
    except Exception as exc:
        if stages["RUNNER_SETUP"] == "NOT_RUN":
            stages["RUNNER_SETUP"] = "FAIL"
            failure_category = "WINDOWS_SETTINGS_FAILURE"
        elif not failure_category:
            failure_category = "HARNESS_OR_INFRA_FAILURE"
        exit_code = 1
        print("HIGH_CONTRAST_ACCEPTANCE_ERROR", repr(exc), flush=True)
    finally:
        try:
            if query().enabled != original.enabled:
                set_target(original.enabled)
            stages["CLEANUP"] = "PASS"
        except Exception as cleanup_exc:
            stages["CLEANUP"] = "FAIL"
            if not failure_category:
                failure_category = "CLEANUP_FAILURE"
            exit_code = 1
            print("HIGH_CONTRAST_CLEANUP_ERROR", repr(cleanup_exc), flush=True)

        final_state = query()
        payload = {
            "stages": stages,
            "failure_category": failure_category or None,
            "original_high_contrast": original.enabled,
            "final_high_contrast": final_state.enabled,
            "elapsed_seconds": round(time.time() - started, 3),
            "candidate_exe": str(candidate),
            "baseline_exe": str(args.baseline_exe) if args.baseline_exe else None,
        }
        result_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("HIGH_CONTRAST_RESULT", result_path, flush=True)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
