"""Opt-in cleanup for the migration worktree. Dry-run unless --apply.

Never removes Debug intermediates, built executables, NuGet packages or evidence
logs; only recognized, unreferenced old successful *source* check logs qualify.
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BRANCH = "migration/winui3-full-shell-20260929"
SOURCE_LOG = re.compile(
    r"^\d{8}-\d{6}-(?:source|official-source-preflight)\.log$")


def command(*args, timeout=12):
    result = subprocess.run(args, cwd=ROOT, capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"Command returned {result.returncode}: {args[0:2]}")
    return result.stdout.strip()


def no_links_under(root, path):
    base = root.absolute()
    candidate = path.absolute()
    if not candidate.is_relative_to(base):
        raise RuntimeError("Cleanup candidate escapes this worktree.")
    parent = candidate
    while True:
        if parent.is_symlink() or (hasattr(parent, "is_junction")
                                   and parent.is_junction()):
            raise RuntimeError(f"Cleanup candidate has a link: {parent}")
        if parent == base:
            break
        parent = parent.parent


def release_targets(root):
    shell = root / "experiments" / "phase6_winui_shell"
    no_links_under(root, shell)
    if not shell.is_dir():
        return []
    results = []
    for parent in shell.glob("FlyExplo.*/x64/Release"):
        no_links_under(root, parent)
        if parent.is_dir() and parent.parent.name == "x64" \
                and parent.parent.parent.name.startswith("FlyExplo."):
            results.append(parent)
    return sorted(results)


def tree_size(path):
    amount = count = 0
    if path.is_file():
        return path.stat().st_size, 1
    for current, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            child = Path(current) / name
            if child.is_symlink() or (hasattr(child, "is_junction")
                                      and child.is_junction()):
                raise RuntimeError("Linked file in cleanup target: " + str(child))
        for name in files:
            amount += (Path(current) / name).stat().st_size
            count += 1
    return amount, count


def documentation(root):
    texts = []
    for path in (root / "AGENTS.md", root / "README.md"):
        if path.is_file():
            texts.append(path.read_text(encoding="utf-8-sig",
                                        errors="replace"))
    for base in (root / "docs", root / ".agent-policy",
                 root / "experiments", root / "build"):
        if base.is_dir():
            for path in base.rglob("*.md"):
                texts.append(path.read_text(encoding="utf-8-sig",
                                            errors="replace"))
    return "\n".join(texts)


def successful_source_log(path):
    data = path.read_text(encoding="utf-8", errors="replace")
    if path.name.endswith("-official-source-preflight.log"):
        return data.strip() == "Source invariant/regression preflight: PASS"
    if path.name.endswith("-source.log"):
        return bool(re.search(r"(?m)^Ran \d+ tests? in ", data)) and \
            data.rstrip().endswith("\nOK") and \
            "FAILED" not in data and "Traceback" not in data
    return False


def prune_candidates(log_dir, referenced, *, now, days=30, keep=2):
    if not log_dir.is_dir():
        return []
    all_logs = [p for p in log_dir.iterdir()
                if p.is_file() and SOURCE_LOG.fullmatch(p.name)]
    labels = collections.defaultdict(list)
    for p in all_logs:
        label = "preflight" if p.name.endswith(
            "-official-source-preflight.log") else "source"
        labels[label].append(p)
    retained = set()
    for group in labels.values():
        retained.update(sorted(group, key=lambda p: p.stat().st_mtime,
                               reverse=True)[:keep])
    result = []
    for p in all_logs:
        if p in retained or p.name in referenced or str(p.name) in referenced:
            continue
        if now - p.stat().st_mtime < days * 86400:
            continue
        if successful_source_log(p):
            result.append(p)
    return sorted(result)


def git_guard(checkpoint):
    if command("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError("Not on the migration branch.")
    if command("git", "rev-parse", "HEAD") != checkpoint:
        raise RuntimeError("Checkpoint must exactly match current HEAD.")
    if command("git", "status", "--porcelain=v1", "-uall"):
        raise RuntimeError("Worktree is not clean.")
    remote = command("git", "ls-remote", "origin",
                     "refs/heads/" + BRANCH).split()
    if not remote or remote[0] != checkpoint:
        raise RuntimeError("Remote checkpoint does not match local HEAD.")


def idle_guard():
    raw = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
                         encoding="utf-8", errors="replace", timeout=12,
                         check=True).stdout
    active = {row[0].lower() for row in csv.reader(raw.splitlines())
              if row}
    blocked = active.intersection({"msbuild.exe", "cl.exe", "link.exe",
                                   "flyexplorerwinuishell.exe"})
    if blocked:
        raise RuntimeError("Build or owned GUI running: " + ", ".join(sorted(blocked)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-intermediates", action="store_true",
                        help="Preview/remove ONLY intermediate x64 Release subtree.")
    parser.add_argument("--prune-success-source-logs", action="store_true",
                        help="Preview/remove strictly verified 30+ day source success logs.")
    parser.add_argument("--apply", action="store_true",
                        help="Actually remove selected files; defaults to dry-run.")
    parser.add_argument("--checkpoint", help="Exact remote-verified local HEAD; "
                        "required for apply.")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("This cleanup is Windows only.")
    if not (args.release_intermediates or args.prune_success_source_logs):
        parser.error("Choose at least one explicit, limited cleanup category.")
    if args.apply and not args.checkpoint:
        parser.error("--apply requires --checkpoint after successful verification.")
    targets = release_targets(ROOT) if args.release_intermediates else []
    source_logs = prune_candidates(
        ROOT / "logs" / "winui-scoped", documentation(ROOT),
        now=dt.datetime.now().timestamp()
    ) if args.prune_success_source_logs else []
    entries = []
    for p in targets + source_logs:
        no_links_under(ROOT, p)
        size, count = tree_size(p)
        entries.append({"path":str(p.relative_to(ROOT)), "bytes":size,
                        "files":count})
    summary = {"mode":"apply" if args.apply else "dry-run",
               "candidates":entries,
               "candidate_bytes":sum(p["bytes"] for p in entries),
               "release_only":args.release_intermediates,
               "log_policy":"Only unreferenced 30+ day successful source/preflight logs; retain latest 2 per type",
               "preserve":"Debug, WinUI executables, NuGet, failing logs, evidence references, main worktree"}
    if args.apply:
        # A clean checkpoint is evidence of reproducibility, not proof of
        # Release validation. The operator must verify that separately.
        git_guard(args.checkpoint)
        idle_guard()
        for p in targets:
            ignore = subprocess.run(["git", "check-ignore", "-q", str(p.absolute())],
                                    cwd=ROOT, capture_output=True)
            if ignore.returncode != 0:
                raise RuntimeError("Target is not git ignored.")
            relative=p.relative_to(ROOT)
            if command("git", "ls-files", "--", str(relative)):
                raise RuntimeError("Tracked content present in target.")
        # Redo conservative checks after preflight before each deletion.
        import shutil
        for p in targets:
            no_links_under(ROOT, p)
            tree_size(p)
            shutil.rmtree(p)
        for p in source_logs:
            no_links_under(ROOT, p)
            if p.is_symlink() or not successful_source_log(p):
                raise RuntimeError("Source log changed before cleanup.")
            p.unlink()
        if command("git", "status", "--porcelain=v1", "-uall"):
            raise RuntimeError("Unexpected worktree change after cleanup.")
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
