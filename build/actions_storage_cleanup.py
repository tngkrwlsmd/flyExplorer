#!/usr/bin/env python3
"""Inspect and prune GitHub Actions artifact storage for flyExplorer.

The default mode is read-only. Use --apply to perform deletions and/or change
repository artifact/log retention. This tool deliberately runs locally instead
of as another hosted Actions workflow so storage cleanup never creates a new
hosted run just to clean hosted-run storage.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

API_VERSION = "2026-03-10"
DEFAULT_REPO = "tngkrwlsmd/flyExplorer"
DEFAULT_NAMES = ("flyExplorer-release-package",)


@dataclass(frozen=True)
class Artifact:
    artifact_id: int
    name: str
    size_bytes: int
    created_at: str
    expires_at: str
    expired: bool
    workflow_run_id: Optional[int]

    @property
    def created_sort_key(self) -> Tuple[str, int]:
        return (self.created_at, self.artifact_id)


class GitHubApi:
    def __init__(self, token: str, repo: str) -> None:
        if "/" not in repo:
            raise ValueError("--repo must be OWNER/REPO")
        self._token = token
        self.repo = repo
        self.base = f"https://api.github.com/repos/{repo}"

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, object]] = None,
    ) -> Tuple[int, Optional[object]]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base + path,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "flyExplorer-actions-storage-cleanup",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                if not raw:
                    return response.status, None
                return response.status, json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub API {method} {path} failed: HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"GitHub API {method} {path} failed: {exc.reason}"
            ) from exc

    def list_artifacts(self) -> list[Artifact]:
        artifacts: list[Artifact] = []
        page = 1
        while True:
            query = urllib.parse.urlencode({"per_page": 100, "page": page})
            _, payload = self._request(
                "GET", f"/actions/artifacts?{query}"
            )
            if not isinstance(payload, dict):
                raise RuntimeError("artifact list response was not a JSON object")
            items = payload.get("artifacts")
            if not isinstance(items, list):
                raise RuntimeError("artifact list response has no artifacts array")
            for item in items:
                if not isinstance(item, dict):
                    continue
                workflow_run = item.get("workflow_run")
                workflow_run_id = (
                    int(workflow_run.get("id"))
                    if isinstance(workflow_run, dict)
                    and workflow_run.get("id") is not None
                    else None
                )
                artifacts.append(
                    Artifact(
                        artifact_id=int(item["id"]),
                        name=str(item.get("name", "")),
                        size_bytes=int(item.get("size_in_bytes", 0)),
                        created_at=str(item.get("created_at", "")),
                        expires_at=str(item.get("expires_at", "")),
                        expired=bool(item.get("expired", False)),
                        workflow_run_id=workflow_run_id,
                    )
                )
            if len(items) < 100:
                break
            page += 1
        return artifacts

    def get_retention_days(self) -> tuple[int, Optional[int]]:
        _, payload = self._request(
            "GET", "/actions/permissions/artifact-and-log-retention"
        )
        if not isinstance(payload, dict) or "days" not in payload:
            raise RuntimeError("retention response did not include days")
        maximum = payload.get("maximum_allowed_days")
        return int(payload["days"]), int(maximum) if maximum is not None else None

    def set_retention_days(self, days: int) -> None:
        self._request(
            "PUT",
            "/actions/permissions/artifact-and-log-retention",
            {"days": days},
        )

    def delete_artifact(self, artifact_id: int) -> None:
        self._request("DELETE", f"/actions/artifacts/{artifact_id}")


def format_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB")
    size = float(value)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{value} B"


def select_deletions(
    artifacts: Iterable[Artifact],
    names: set[str],
    keep_newest: int,
) -> Tuple[list[Artifact], list[Artifact]]:
    candidates = [
        artifact
        for artifact in artifacts
        if not artifact.expired and artifact.name in names
    ]
    candidates.sort(key=lambda item: item.created_sort_key, reverse=True)
    kept = candidates[:keep_newest]
    deleted = candidates[keep_newest:]
    return kept, deleted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect flyExplorer GitHub Actions artifact storage and optionally "
            "delete old duplicate release packages."
        )
    )
    parser.add_argument("--repo", default=DEFAULT_REPO, help="OWNER/REPO")
    parser.add_argument(
        "--name",
        action="append",
        dest="names",
        help=(
            "artifact name to manage; may be repeated "
            f"(default: {DEFAULT_NAMES[0]})"
        ),
    )
    parser.add_argument(
        "--keep-newest",
        type=int,
        default=1,
        help="number of newest matching non-expired artifacts to retain",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=None,
        help=(
            "also set repository artifact/log retention; only changed with "
            "--apply"
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="perform deletes and retention change; otherwise dry-run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.keep_newest < 0:
        print("--keep-newest must be >= 0", file=sys.stderr)
        return 2
    if args.retention_days is not None and args.retention_days < 1:
        print("--retention-days must be >= 1", file=sys.stderr)
        return 2

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "Set GH_TOKEN or GITHUB_TOKEN. For this private repository, "
            "listing needs Actions read; --apply deletion needs Actions write; "
            "changing retention needs repository Administration write "
            "(classic tokens may use repo scope).",
            file=sys.stderr,
        )
        return 2

    names = set(args.names or DEFAULT_NAMES)
    api = GitHubApi(token, args.repo)

    try:
        artifacts = api.list_artifacts()
        current_retention, maximum_retention = api.get_retention_days()
    except (RuntimeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    nonexpired = [item for item in artifacts if not item.expired]
    total_nonexpired = sum(item.size_bytes for item in nonexpired)
    kept, deletions = select_deletions(
        artifacts,
        names,
        args.keep_newest,
    )
    reclaim = sum(item.size_bytes for item in deletions)

    print(f"Repository: {args.repo}")
    print(
        "Retention: "
        f"{current_retention} day(s)"
        + (
            f" (maximum {maximum_retention})"
            if maximum_retention is not None else ""
        )
    )
    print(
        f"Non-expired artifacts: {len(nonexpired)} / "
        f"{format_bytes(total_nonexpired)}"
    )
    print(
        f"Managed names: {', '.join(sorted(names))}; "
        f"keep newest: {args.keep_newest}"
    )
    print(f"Would reclaim: {format_bytes(reclaim)}")

    if kept:
        print("Keep:")
        for item in kept:
            print(
                f"  {item.artifact_id} {item.name} "
                f"{format_bytes(item.size_bytes)} created={item.created_at}"
            )

    if deletions:
        print("Delete candidates:")
        for item in deletions:
            print(
                f"  {item.artifact_id} {item.name} "
                f"{format_bytes(item.size_bytes)} created={item.created_at}"
            )
    else:
        print("Delete candidates: none")

    if args.retention_days is not None:
        print(
            "Retention change: "
            f"{current_retention} -> {args.retention_days} day(s)"
        )

    if not args.apply:
        print("DRY RUN: no GitHub data was changed. Re-run with --apply.")
        return 0

    try:
        for item in deletions:
            api.delete_artifact(item.artifact_id)
            print(f"Deleted artifact {item.artifact_id} ({item.name})")
        if (
            args.retention_days is not None
            and args.retention_days != current_retention
        ):
            api.set_retention_days(args.retention_days)
            print(f"Set repository retention to {args.retention_days} day(s)")
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(
        f"Applied cleanup. Requested artifact reclaim: {format_bytes(reclaim)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
