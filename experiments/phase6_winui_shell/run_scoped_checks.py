"""Bounded local WinUI checks. No CI dispatch, OS clipboard, or real user mutations."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LOGS = ROOT / "logs" / "winui-scoped"
CONTRACTS = [
    "experiments/phase6_winui_shell/test_arch_contract.py",
    "experiments/phase6_winui_shell/isolation/test_contract.py",
    "experiments/phase6_winui_shell/isolation/test_winui_integration_contract.py",
    "experiments/phase6_winui_shell/test_m19_arch_contract.py",
    "experiments/phase6_winui_shell/test_m19_contract.py",
    "experiments/phase6_winui_shell/test_m20_contract.py",
    "experiments/phase6_winui_shell/test_m21_contract.py",
    "experiments/phase6_winui_shell/test_m22_contract.py",
    "experiments/phase6_winui_shell/test_m23_contract.py",
    "experiments/phase6_winui_shell/test_m23_followup_contract.py",
    "experiments/phase6_winui_shell/test_clipboard_manual_contract.py",
    "experiments/phase6_winui_shell/test_registered_file_type_contract.py",
    "experiments/phase6_winui_shell/test_thumbnail_contract.py",
    "experiments/phase6_winui_shell/test_external_context_contract.py",
    "experiments/phase6_winui_shell/test_lifecycle_safety_contract.py",
    "experiments/phase6_winui_shell/test_accessibility_scope_contract.py",
    "experiments/phase6_winui_shell/test_owned_explorer_clipboard_contract.py",
    "experiments/phase6_winui_shell/test_manual_accessibility_contract.py",
    "experiments/phase6_winui_shell/test_recycle_owned_contract.py",
    "experiments/phase6_winui_shell/test_large_folder_contract.py",
    "experiments/phase6_winui_shell/test_m25_parity_contract.py",
    "experiments/phase6_winui_shell/test_portable_safety_contract.py",
    "build/test_ui_uxh07_workspace_contract.py",
    "build/test_ui_uxh06_recent_scope_contract.py",
    "build/test_ui02_layered_scrollbar.py",
    "build/test_ui02_scrollbar_coverage.py",
    "build/test_ui02_owned_harness_safety_contract.py",
    "build/test_dev_artifact_cleanup.py",
    "build/test_phase5_retirement_contract.py",
]
OWNED_FLAGS = ("FLY_M19_OWNED_FEATURES", "FLY_M20_OWNED_SHELL",
               "FLY_M21_OWNED_FEATURES", "FLY_M22_OWNED_FEATURES",
               "FLY_M23_OWNED_FEATURES")
FAULT_FLAGS = ("FLY_M18_OWNED_COM_HANG", "FLY_M18_EXHAUST_TIMEOUT",
               "FLY_M18_OWNED_SHELL_NOTIFY", "FLY_M18_LOOPBACK_UNC",
               "FLY_M23_OWNED_DRAG_TEST", "FLY_M23_OWNED_DRAG_TRACE",
               "FLY_M20_OWNED_COLLAPSE_M19_PANELS")
def execute(label, command, timeout, env, tag):
    path = LOGS / (tag + "-" + label + ".log")
    start = time.monotonic()
    with path.open("w", encoding="utf-8", newline="\n") as output:
        try:
            result = subprocess.run(command, cwd=ROOT, env=env,
                                    stdout=output, stderr=subprocess.STDOUT,
                                    timeout=timeout, check=False)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
            output.write("\nTIMEOUT: bounded local subprocess terminated\n")
    content = path.read_text(encoding="utf-8", errors="replace")
    summary = re.findall(r"Ran \d+ tests.*|^OK(?: \([^\n]*\))?$|^FAILED.*", content, re.M)
    if not summary:
        summary = [line for line in content.splitlines()
                   if line.startswith(("REAL_M23_", "OWNED_WINUI_SHELL_EXIT",
                                       "ORIGINAL_SIX_USER_CONFIG_"))][-3:]
    first_error = next((line.strip()[:240] for line in content.splitlines()
        if re.search(r"error C\d+|error LNK\d+|error MSB\d+|fatal error|"
                     r"AssertionError:|RuntimeError:|ElementNotFoundError:|TimeoutError|^FAIL:|^ERROR:", line)), "")
    print(f"{label}: EXIT={code} SECONDS={time.monotonic()-start:.1f} "
          f"LOG={path.relative_to(ROOT)}", flush=True)
    if summary:
        print("RESULT=" + " / ".join(summary[-3:])[:280], flush=True)
    if code and first_error:
        print("FIRST_RELEVANT_ERROR=" + first_error, flush=True)
    return code

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("source", "build", "gui", "full"))
    parser.add_argument("--configuration", choices=("Debug", "Release"),
                        default="Debug")
    parser.add_argument("--isolate-feature-panels", action="store_true",
        help="Close test-owned M1.9 panels before M2.0; does not accept the open-panel case.")
    args = parser.parse_args()
    assert os.name == "nt", "Windows-only build and owned GUI runner"
    LOGS.mkdir(parents=True, exist_ok=True)
    tag = time.strftime("%Y%m%d-%H%M%S")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT / "build")
    # Never inherit diagnostics or a non-owned GUI scenario by accident.
    for key in OWNED_FLAGS + FAULT_FLAGS:
        env.pop(key, None)
    stages = (["source", "build-Debug", "build-Release",
               "gui-Debug", "gui-Release"] if args.stage == "full"
              else [args.stage + ("-" + args.configuration
                    if args.stage != "source" else "")])
    for stage in stages:
        if stage == "source":
            official = execute("official-source-preflight",
                               [sys.executable, str(ROOT / "build" /
                                                 "validate_source_invariants.py")],
                               120, env, tag)
            if official:
                return official
            cmd = [sys.executable, "-m", "unittest", *CONTRACTS]
            timeout = 90
        elif stage.startswith("build-"):
            configuration = stage.split("-")[1]
            cmd = ["cmd", "/c", str(HERE / "build.cmd"), configuration]
            timeout = 210
        else:
            configuration = stage.split("-")[1]
            gui_env = env.copy()
            gui_env["FLY_MIGRATION_CONFIGURATION"] = configuration
            for key in OWNED_FLAGS:
                gui_env[key] = "YES"
            if args.isolate_feature_panels:
                gui_env["FLY_M20_OWNED_COLLAPSE_M19_PANELS"] = "YES"
            cmd = [sys.executable, "-u", str(HERE / "test_shell_gui.py")]
            timeout = 230
            env_to_use = gui_env
        rc = execute(stage, cmd, timeout,
                     env_to_use if stage.startswith("gui-") else env, tag)
        if rc != 0:
            return rc
    print("SCOPED_CHECKS_COMPLETE=PASS; physical drag and global clipboard "
          "NOT TESTED by this runner; actual owned Recycle Bin has separate test",
          flush=True)
    return 0
if __name__ == "__main__":
    sys.exit(main())
