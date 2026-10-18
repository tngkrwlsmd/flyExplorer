"""Bounded WinUI checks with change-scoped FAST and targeted GUI selection."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from resolve_validation_scope import PRODUCT_AREAS, affected_areas, change_families

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui"
TESTS = ROOT / "tests" / "winui"
LOGS = ROOT / "logs" / "winui-scoped"
DEFAULT_RESULT = ROOT / "logs" / "remote-evidence" / "check-result.json"
_ACTIVE_STAGE = ""
_RESULT_PATH = DEFAULT_RESULT

PRODUCT_SUITES = {
    "core": [
        "tests/winui/test_arch_contract.py",
        "tests/winui/test_m26_fluent_contract.py",
        "tests/winui/test_file_display_options_contract.py",
        "tests/winui/test_shortcut_semantics_contract.py",
        "tests/winui/test_window_tab_navigation_chrome_contract.py",
        "tests/winui/test_file_metadata_controller_contract.py",
        "tests/winui/test_localization_contract.py",
    ],
    "shell": [
        "tests/winui/helper/test_contract.py",
        "tests/winui/helper/test_winui_integration_contract.py",
        "tests/winui/test_external_context_contract.py",
        "tests/winui/test_file_detail_controller_contract.py",
        "tests/winui/test_f03_preview_policy_contract.py",
        "tests/winui/test_f05_group_projection_contract.py",
        "tests/winui/test_f05_winui_group_integration_contract.py",
        "tests/winui/test_f05_extended_group_contract.py",
        "tests/winui/test_f05_extended_winui_contract.py",
        "tests/winui/test_f05_modes_gui_harness_contract.py",
        "tests/winui/test_f03_preview_reader_contract.py",
        "tests/winui/test_f03_safe_open_contract.py",
        "tests/winui/test_f03_worker_wire_contract.py",
        "tests/winui/test_f03_supervisor_contract.py",
        "tests/winui/test_f03_winui_controller_contract.py",
        "tests/winui/test_known_folder_artwork_contract.py",
        "tests/winui/test_sidebar_known_folder_artwork_contract.py",
        "tests/winui/test_f04_tree_path_contract.py",
        "tests/winui/test_f04_sidebar_tree_contract.py",
        "tests/winui/test_thumbnail_contract.py",
    ],
    "search": [
        "tests/winui/test_search_controller_contract.py",
        "tests/winui/test_filter_preset_contract.py",
    ],
    "file-operations": [
        "tests/winui/test_file_operation_controller_contract.py",
        "tests/winui/test_clipboard_manual_contract.py",
        "tests/winui/test_owned_explorer_clipboard_contract.py",
        "tests/winui/test_recycle_owned_contract.py",
    ],
    "session": [
        "tests/winui/test_session_coordinator_contract.py",
        "tests/winui/test_workspace_restore_coordinator_contract.py",
    ],
    "accessibility": [
        "tests/winui/test_accessibility_scope_contract.py",
        "tests/winui/test_high_contrast_contract.py",
        "tests/winui/test_manual_accessibility_contract.py",
    ],
    "packaging": [
        "tests/winui/test_installer_contract.py",
        "tests/winui/test_lifecycle_safety_contract.py",
        "tests/winui/test_portable_safety_contract.py",
        "tests/winui/test_registered_file_type_contract.py",
        "tests/winui/test_release_payload_contract.py",
    ],
    "large-folder": [
        "tests/winui/test_large_folder_streaming_contract.py",
    ],
    "identity-settings": [
        "tests/winui/test_bookmark_contract.py",
        "tests/winui/test_preferences_coordinator_contract.py",
        "tests/winui/test_product_identity_contract.py",
    ],
}
HARNESS_CONTRACTS = [
    "tests/winui/test_build_environment_contract.py",
    "tests/winui/test_gui_harness_contract.py",
    "tests/winui/test_gui_failure_evidence_contract.py",
]
INFRA_CONTRACTS = [
    "tests/winui/test_dev_entrypoint_contract.py",
    "tests/winui/test_remote_failure_classifier.py",
    "tests/winui/test_remote_request_preflight_contract.py",
    "tests/winui/test_remote_windows_task_contract.py",
    "tests/winui/test_remote_evidence_archive_contract.py",
    "tests/winui/test_validation_scope_contract.py",
]
STRUCTURE_CONTRACT = "tests/winui/test_structure_contract.py"

OWNED_FLAGS = (
    "FLY_V7_WINDOW_TABS",
    "FLY_V7_WINDOW_TABS_SESSION",
    "FLY_M19_OWNED_FEATURES",
    "FLY_M20_OWNED_SHELL",
    "FLY_M21_OWNED_FEATURES",
    "FLY_M22_OWNED_FEATURES",
    "FLY_M23_OWNED_FEATURES",
)
FAULT_FLAGS = (
    "FLY_M18_OWNED_COM_HANG",
    "FLY_M18_EXHAUST_TIMEOUT",
    "FLY_M18_OWNED_SHELL_NOTIFY",
    "FLY_M18_LOOPBACK_UNC",
    "FLY_M23_OWNED_DRAG_TEST",
    "FLY_M23_OWNED_DRAG_TRACE",
    "FLY_M20_OWNED_COLLAPSE_M19_PANELS",
)
GUI_AREAS = (
    "core",
    "shortcuts",
    "shell",
    "search",
    "search-content-regex",
    "unc-copy-move",
    "file-operations",
    "session",
    "window-tabs",
    "bookmark",
    "filter-preset",
    "accessibility",
    "large-folder",
    "folder-tree",
    "all",
)


def unique(paths):
    return list(dict.fromkeys(paths))


def begin_result(stage):
    global _ACTIVE_STAGE, _RESULT_PATH
    _ACTIVE_STAGE = stage
    configured = os.environ.get("FLYEXPLORER_CHECK_RESULT_PATH", "").strip()
    _RESULT_PATH = Path(configured) if configured else DEFAULT_RESULT
    _RESULT_PATH.unlink(missing_ok=True)
    _RESULT_PATH.with_suffix(_RESULT_PATH.suffix + ".tmp").unlink(missing_ok=True)


def write_failure_result(category, code):
    payload = {
        "failure_category": category,
        "exit_code": int(code),
        "stage": _ACTIVE_STAGE,
    }
    _RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = _RESULT_PATH.with_suffix(_RESULT_PATH.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, _RESULT_PATH)


def execute(label, command, timeout, env, tag):
    LOGS.mkdir(parents=True, exist_ok=True)
    path = LOGS / (tag + "-" + label + ".log")
    start = time.monotonic()
    with path.open("w", encoding="utf-8", newline="\n") as output:
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
            output.write("\nTIMEOUT: bounded local subprocess terminated\n")

    body = path.read_text(encoding="utf-8", errors="replace")
    summary = re.findall(r"Ran \d+ tests.*|^OK(?: \([^\n]*\))?$|^FAILED.*", body, re.M)
    first_error = next(
        (
            line.strip()[:240]
            for line in body.splitlines()
            if re.search(
                r"error C\d+|error LNK\d+|error MSB\d+|fatal error|"
                r"AssertionError:|RuntimeError:|ElementNotFoundError:|"
                r"TimeoutError|TypeError:|AttributeError:|COMError:|^FAIL:|^ERROR:",
                line,
            )
        ),
        "",
    )
    print(
        f"{label}: EXIT={code} SECONDS={time.monotonic()-start:.1f} "
        f"LOG={path.relative_to(ROOT)}",
        flush=True,
    )
    if summary:
        print("RESULT=" + " / ".join(summary[-3:])[:280], flush=True)
    if code and first_error:
        print("FIRST_RELEVANT_ERROR=" + first_error, flush=True)
    if code and label.startswith("gui-folder-tree-"):
        # Surface only bounded F04 diagnostic stage tokens in the central
        # Actions log. Full test logs stay inside ignored owned evidence.
        allowed = (
            "F04_FOCUSED_PANE=", "F04_FOCUSED_READY_PANE=",
            "F04_CLICK_DIAG_ROOT_STILL_ACTIVE=",
            "F04_TREE_SELECTION_STAGE=", "F04_TREE_UIA_SELECTED=",
            "F04_DIAG_UIA_SELECTION_NAVIGATED=",
            "F04_FAILURE_CAPTURE_SKIPPED=",
        )
        for line in body.splitlines():
            if line.startswith(allowed):
                print("F04_FAILURE_DIAGNOSTIC=" + line[:180], flush=True)
    return code


def run_contracts(label, paths, env, tag):
    paths = unique(paths)
    if not paths:
        print(f"{label}: SKIPPED empty suite", flush=True)
        return 0
    return execute(
        label,
        [sys.executable, "-m", "unittest", *paths],
        120,
        env,
        tag,
    )


def fail(category, code):
    print(f"FAILURE_CATEGORY={category}", flush=True)
    write_failure_result(category, code)
    return code


def git_lines(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="strict",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return [line for line in result.stdout.splitlines() if line.strip()]


def product_contracts(areas):
    return unique(
        path
        for area in PRODUCT_AREAS
        if area in areas
        for path in PRODUCT_SUITES[area]
    )


def run_fast(before, head, env, tag):
    diff = subprocess.run(
        ["git", "diff", "--check", before, head],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if diff.returncode:
        print(diff.stdout, end="", flush=True)
        return fail("STATIC_DIFF_FAILURE", diff.returncode)

    paths = git_lines("diff", "--name-only", before, head)
    areas = affected_areas(paths)
    families = change_families(paths)
    print("FAST_CHANGED_PATHS=" + str(len(paths)), flush=True)
    print("FAST_AREAS=" + (",".join(sorted(areas)) or "-"), flush=True)
    print("FAST_FAMILIES=" + (",".join(sorted(families)) or "-"), flush=True)

    python_files = [
        ROOT / path
        for path in paths
        if path.endswith(".py")
        and path.startswith(("tools/winui/", "tests/winui/"))
        and (ROOT / path).is_file()
    ]
    if python_files:
        rc = execute(
            "changed-python-static",
            [
                sys.executable,
                "-X",
                "utf8",
                str(ROOT / "tools/winui/check_python_static.py"),
                *map(str, python_files),
            ],
            45,
            env,
            tag,
        )
        if rc:
            return fail("HELPER_STATIC_FAILURE", rc)

    if areas:
        rc = run_contracts(
            "canonical-structure-preflight",
            [STRUCTURE_CONTRACT],
            env,
            tag,
        )
        if rc:
            return fail("STRUCTURE_CONTRACT_FAILURE", rc)

    selected = product_contracts(areas)
    changed_contracts = [
        path
        for path in paths
        if path.endswith("_contract.py") and (ROOT / path).is_file()
    ]
    selected.extend(
        path
        for path in changed_contracts
        if path not in HARNESS_CONTRACTS
        and path not in INFRA_CONTRACTS
        and path != STRUCTURE_CONTRACT
    )
    rc = run_contracts("fast-product-contracts", selected, env, tag)
    if rc:
        return fail("PRODUCT_SOURCE_CONTRACT_FAILURE", rc)

    if "harness" in families:
        rc = run_contracts("fast-harness-contracts", HARNESS_CONTRACTS, env, tag)
        if rc:
            return fail("HARNESS_CONTRACT_FAILURE", rc)

    if "infra" in families:
        rc = run_contracts("fast-infra-contracts", INFRA_CONTRACTS, env, tag)
        if rc:
            return fail("INFRA_POLICY_CONTRACT_FAILURE", rc)

    print("FAST_CHECKS_COMPLETE=PASS", flush=True)
    return 0


def gui_command(area, configuration, env):
    gui_env = env.copy()
    gui_env["FLY_MIGRATION_CONFIGURATION"] = configuration
    for key in OWNED_FLAGS + FAULT_FLAGS + (
        "FLY_V7_WINDOW_TABS_ONLY",
        "FLY_M19_OWNED_FEATURES_ONLY",
    ):
        gui_env.pop(key, None)

    if area == "shortcuts":
        return [
            sys.executable, "-u", str(TESTS / "test_shortcut_gui.py"),
        ], gui_env, 150
    if area == "search-content-regex":
        return [
            sys.executable,
            "-u",
            str(TESTS / "test_content_regex_gui.py"),
        ], gui_env, 120
    if area == "unc-copy-move":
        return [
            sys.executable,
            "-u",
            str(TESTS / "test_unc_transfer_gui.py"),
        ], gui_env, 120
    if area == "bookmark":
        return [sys.executable, "-u", str(TESTS / "test_bookmark_gui.py")], gui_env, 150
    if area == "filter-preset":
        return [sys.executable, "-u", str(TESTS / "test_filter_preset_gui.py")], gui_env, 150
    if area == "accessibility":
        return [
            sys.executable,
            "-u",
            str(TESTS / "test_owned_accessibility_layout_gui.py"),
            configuration,
        ], gui_env, 160
    if area == "folder-tree":
        gui_env["FLY_F04_TREE_ONLY"] = "YES"
        gui_env["FLY_F04_TREE_VISUAL_CAPTURE"] = "YES"
        gui_env["FLY_F04_TREE_THEME"] = os.environ.get("FLY_F04_TREE_THEME", "light")
        return [sys.executable, "-u", str(TESTS / "test_shell_gui.py")], gui_env, 150
    if area == "large-folder":
        return [
            sys.executable,
            "-u",
            str(TESTS / "test_large_owned_folder_gui.py"),
            "--items",
            "1100",
            "--configuration",
            configuration,
        ], gui_env, 180

    flags = {
        "core": ("FLY_M20_OWNED_SHELL",),
        "shell": ("FLY_M20_OWNED_SHELL",),
        "search": ("FLY_M19_OWNED_FEATURES", "FLY_M19_OWNED_FEATURES_ONLY"),
        "file-operations": ("FLY_M21_OWNED_FEATURES", "FLY_M22_OWNED_FEATURES"),
        "session": ("FLY_M23_OWNED_FEATURES",),
        "window-tabs": (
            "FLY_V7_WINDOW_TABS", "FLY_V7_WINDOW_TABS_SESSION",
            "FLY_V7_WINDOW_TABS_ONLY",
        ),
        "all": OWNED_FLAGS,
    }[area]
    for key in flags:
        gui_env[key] = "YES"
    if area == "all":
        # M19 leaves test-owned Search/Workspace panels expanded. Restore
        # native file-list visibility before M20 retemplates its WinUI peers.
        # Keep the handoff scoped to the chained complete GUI profile.
        gui_env["FLY_M20_OWNED_COLLAPSE_M19_PANELS"] = "YES"
    return [sys.executable, "-u", str(TESTS / "test_shell_gui.py")], gui_env, 260


def run_gui(area, configuration, env, tag):
    dep_rc = execute(
        "gui-python-dependencies",
        [
            sys.executable,
            "-X",
            "utf8",
            str(ROOT / "tools/winui/check_python_deps.py"),
            "--gui",
        ],
        30,
        env,
        tag,
    )
    if dep_rc:
        return fail("HARNESS_DEPENDENCY_FAILURE", dep_rc)
    if area == "all":
        # Fail early on exact session-history cleanup before long GUI coverage.
        # Keep standalone focused probes independently runnable.
        for focused in ("window-tabs", "shortcuts", "filter-preset"):
            cmd, gui_env, timeout = gui_command(
                focused, configuration, env
            )
            rc = execute(
                f"gui-{focused}-{configuration}",
                cmd, timeout, gui_env, tag,
            )
            if rc:
                return fail("GUI_ACCEPTANCE_FAILURE", rc)
        # F04 is additive: keep the pre-existing shortcut acceptance order.
        cmd, gui_env, timeout = gui_command("folder-tree", configuration, env)
        rc = execute(
            f"gui-folder-tree-{configuration}",
            cmd, timeout, gui_env, tag,
        )
        if rc:
            return fail("GUI_ACCEPTANCE_FAILURE", rc)
    cmd, gui_env, timeout = gui_command(area, configuration, env)
    rc = execute(f"gui-{area}-{configuration}", cmd, timeout, gui_env, tag)
    return fail("GUI_ACCEPTANCE_FAILURE", rc) if rc else 0


def run_build(configuration, env, tag):
    rc = execute(
        "build-" + configuration,
        ["cmd", "/c", str(APP / "build.cmd"), configuration],
        240,
        env,
        tag,
    )
    return fail("PRODUCT_BUILD_FAILURE", rc) if rc else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage",
        choices=(
            "fast",
            "source",
            "product-source",
            "harness",
            "infra",
            "build",
            "gui",
            "full",
        ),
    )
    parser.add_argument("--before")
    parser.add_argument("--head")
    parser.add_argument("--area", default="all")
    parser.add_argument(
        "--configuration",
        choices=("Debug", "Release"),
        default="Release",
    )
    parser.add_argument(
        "--include-debug",
        action="store_true",
        help="FINAL-only opt-in for configuration-specific Debug coverage.",
    )
    args = parser.parse_args()

    if args.stage not in {"fast", "source", "product-source", "harness", "infra"}:
        assert os.name == "nt", "Build and owned GUI stages require Windows"
    if args.stage == "fast" and (not args.before or not args.head):
        parser.error("fast requires --before and --head")
    if args.stage == "product-source" and args.area not in ("all", *PRODUCT_AREAS):
        parser.error("product-source --area must name a product area or all")
    if args.stage == "gui" and args.area not in GUI_AREAS:
        parser.error("gui --area must name a supported targeted GUI area")

    begin_result(args.stage)
    tag = time.strftime("%Y%m%d-%H%M%S")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(TESTS)

    if args.stage == "fast":
        return run_fast(args.before, args.head, env, tag)

    if args.stage in {"source", "product-source", "harness", "infra"}:
        if args.stage in {"source", "product-source"}:
            rc = run_contracts(
                "canonical-structure-preflight",
                [STRUCTURE_CONTRACT],
                env,
                tag,
            )
            if rc:
                return fail("STRUCTURE_CONTRACT_FAILURE", rc)

        if args.stage in {"source", "product-source"}:
            areas = PRODUCT_AREAS if args.area == "all" else (args.area,)
            rc = run_contracts(
                "product-source-contracts",
                product_contracts(areas),
                env,
                tag,
            )
            if rc:
                return fail("PRODUCT_SOURCE_CONTRACT_FAILURE", rc)
        if args.stage in {"source", "harness"}:
            rc = run_contracts("harness-contracts", HARNESS_CONTRACTS, env, tag)
            if rc:
                return fail("HARNESS_CONTRACT_FAILURE", rc)
        if args.stage in {"source", "infra"}:
            rc = run_contracts("infra-contracts", INFRA_CONTRACTS, env, tag)
            if rc:
                return fail("INFRA_POLICY_CONTRACT_FAILURE", rc)
        print("SOURCE_CHECKS_COMPLETE=PASS", flush=True)
        return 0

    if args.stage == "build":
        return run_build(args.configuration, env, tag)

    if args.stage == "gui":
        return run_gui(args.area, args.configuration, env, tag)

    configurations = ["Release"]
    if args.include_debug:
        configurations.insert(0, "Debug")
    for configuration in configurations:
        rc = run_build(configuration, env, tag)
        if rc:
            return rc
        rc = run_gui("all", configuration, env, tag)
        if rc:
            return rc
    print(
        "FULL_CHECKS_COMPLETE=PASS; high-cost installer, High Contrast, "
        "8k/20k large-folder and visual review remain explicit FINAL gates",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
