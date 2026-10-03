"""Bounded local WinUI checks. No CI dispatch, OS clipboard, or real user mutations."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui"
TESTS = ROOT / "tests" / "winui"
LOGS = ROOT / "logs" / "winui-scoped"
CONTRACTS = [
    str(p.relative_to(ROOT))
    for p in sorted(TESTS.glob("test_*contract.py"))
    if p.name != "test_structure_contract.py"
] + [
    str((TESTS/"helper"/"test_contract.py").relative_to(ROOT)),
    str((TESTS/"helper"/"test_winui_integration_contract.py").relative_to(ROOT)),
]
OWNED_FLAGS = ("FLY_V7_WINDOW_TABS", "FLY_V7_WINDOW_TABS_SESSION", "FLY_M19_OWNED_FEATURES", "FLY_M20_OWNED_SHELL",
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
    parser.add_argument("--v7-window-tabs-only", action="store_true",
        help="Run only the owned v7 functional/session window-tab acceptance.")
    parser.add_argument("--isolate-feature-panels", action="store_true",
        help="Close test-owned M1.9 panels before M2.0; does not accept the open-panel case.")
    args = parser.parse_args()
    if args.stage != "source":
        assert os.name == "nt", "Build and owned GUI stages require Windows"
    LOGS.mkdir(parents=True, exist_ok=True)
    tag = time.strftime("%Y%m%d-%H%M%S")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(TESTS)
    # Never inherit diagnostics or a non-owned GUI scenario by accident.
    for key in OWNED_FLAGS + FAULT_FLAGS + ("FLY_V7_WINDOW_TABS_ONLY",):
        env.pop(key, None)
    stages = (["source", "build-Debug", "build-Release",
               "gui-Debug", "gui-Release"] if args.stage == "full"
              else [args.stage + ("-" + args.configuration
                    if args.stage != "source" else "")])
    if any(stage.startswith("gui-") for stage in stages):
        dep_rc = execute(
            "gui-python-dependencies",
            [sys.executable, "-X", "utf8",
             str(ROOT / "tools" / "winui" / "check_python_deps.py"), "--gui"],
            30, env, tag)
        if dep_rc:
            return dep_rc
    for stage in stages:
        if stage == "source":
            official = execute("canonical-structure-preflight",
                               [sys.executable, str(TESTS /
                                                 "test_structure_contract.py")],
                               30, env, tag)
            if official:
                return official
            cmd = [sys.executable, "-m", "unittest", *CONTRACTS]
            timeout = 90
        elif stage.startswith("build-"):
            configuration = stage.split("-")[1]
            cmd = ["cmd", "/c", str(APP / "build.cmd"), configuration]
            timeout = 210
        else:
            configuration = stage.split("-")[1]
            gui_env = env.copy()
            gui_env["FLY_MIGRATION_CONFIGURATION"] = configuration
            for key in OWNED_FLAGS:
                gui_env[key] = "YES"
            if args.v7_window_tabs_only:
                gui_env["FLY_V7_WINDOW_TABS_ONLY"] = "YES"
            if args.isolate_feature_panels:
                gui_env["FLY_M20_OWNED_COLLAPSE_M19_PANELS"] = "YES"
            cmd = [sys.executable, "-u", str(TESTS / "test_shell_gui.py")]
            timeout = 230
            env_to_use = gui_env
        rc = execute(stage, cmd, timeout,
                     env_to_use if stage.startswith("gui-") else env, tag)
        if rc != 0:
            return rc
        if stage.startswith("gui-"):
            bookmark_rc = execute(
                stage + "-bookmarks",
                [sys.executable, "-u", str(TESTS / "test_bookmark_gui.py")],
                120, env_to_use, tag)
            if bookmark_rc != 0:
                return bookmark_rc
    print("SCOPED_CHECKS_COMPLETE=PASS; physical drag and global clipboard "
          "NOT TESTED by this runner; actual owned Recycle Bin has separate test",
          flush=True)
    return 0
if __name__ == "__main__":
    sys.exit(main())
