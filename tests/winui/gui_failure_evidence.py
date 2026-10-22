"""Bounded, test-owned evidence captured before a failed WinUI test closes its app.

Never enumerate a desktop, unrelated process, user profile, environment or
arbitrary filesystem path. Only the launched app HWND and synthetic GUI fixture
are eligible. Collection errors must never hide the original GUI failure.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import traceback
from uuid import uuid4

MAX_ENTRIES = 70
MAX_UIA_NODES = 90
MAX_TEXT = 160


def _short(value):
    return str(value).replace("\r", " ").replace("\n", " ")[:MAX_TEXT]


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except (ValueError, OSError):
        return False


def _safe_address(value, owned: Path):
    value = str(value)
    if not value:
        return ""
    if _inside(Path(value), owned):
        return _short(value)
    return "[outside test-owned scope]"


def _disk_rows(directory: Path, owned: Path):
    if not _inside(directory, owned) or not directory.is_dir():
        return {"error": "not a test-owned directory"}
    items = []
    try:
        for child in sorted(directory.iterdir(), key=lambda p: p.name.casefold()):
            if len(items) >= MAX_ENTRIES:
                break
            if child.is_symlink():
                items.append({"name": _short(child.name), "kind": "symlink-skipped"})
                continue
            st = child.stat()
            items.append({"name": _short(child.name),
                          "kind": "directory" if child.is_dir() else "file",
                          "bytes": st.st_size if child.is_file() else None})
        return {"items": items, "truncated": len(list(directory.iterdir())) > MAX_ENTRIES}
    except (OSError, PermissionError) as exc:
        return {"error_type": type(exc).__name__}


def _owned_labels(left: Path, right: Path):
    known = {"", "Left", "Right", "Nested", "Secondary"}
    for folder in (left, right):
        try:
            known.update(child.name for child in folder.iterdir()
                         if not child.is_symlink())
        except OSError:
            pass
    return known


def _uia_pane(win, control_id: str, allowed_names: set[str]):
    """Read only descendants of a known pane in the launched app."""
    try:
        spec = win.child_window(auto_id=control_id)
        if not spec.exists(timeout=0.25):
            return {"present": False, "nodes": []}
        nodes = []
        for node in spec.descendants():
            if len(nodes) >= MAX_UIA_NODES:
                break
            info = node.element_info
            label = _short(node.window_text())
            # A WinUI ListItem may include metadata alongside its filename.
            # Do not export arbitrary shell/user text as an accessible name.
            if label and not any(label == name or label.startswith(name + " ")
                                 for name in allowed_names if name):
                label = "[non-fixture label]"
            nodes.append({"type": _short(info.control_type),
                          "automation_id": _short(info.automation_id),
                          "name": label})
        return {"present": True, "nodes": nodes,
                "node_limit": MAX_UIA_NODES}
    except Exception as exc:
        return {"error_type": type(exc).__name__, "nodes": []}


def _screenshot_app_window(win, hwnd: int, pid: int, destination: Path):
    """Only grab a foreground HWND belonging to the spawned test application."""
    if os.name != "nt" or not win or not hwnd or not pid:
        return "skipped: no owned Windows app"
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        foreground = int(user32.GetForegroundWindow())
        owned_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(wintypes.HWND(hwnd),
                                        ctypes.byref(owned_pid))
        if owned_pid.value != pid or foreground != hwnd:
            return "skipped: test app does not own foreground HWND"
        rect = win.rectangle()
        width, height = rect.right - rect.left, rect.bottom - rect.top
        if not (100 <= width <= 5000 and 100 <= height <= 3000):
            return "skipped: invalid owned window bounds"
        from PIL import ImageGrab
        shot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom),
                              include_layered_windows=True)
        shot.thumbnail((1600, 1000))
        shot.save(destination, format="PNG", optimize=True)
        if destination.stat().st_size > 4 * 1024 * 1024:
            destination.unlink()
            return "skipped: screenshot exceeds 4 MiB"
        return "application.png"
    except Exception as exc:
        return "failed: " + type(exc).__name__


def _startup_status_category(value):
    """Fixed status enums only; never store arbitrary app/status text."""
    if value is None:
        return "unavailable"
    for prefix, category in (
        ("독립 Shell 탐색 준비 중", "native-initializing"),
        ("폴더를 불러오는 중입니다.", "loading"),
        ("폴더를 불러왔습니다.", "loaded"),
        ("응답 지연 후 폴더를 불러왔습니다.", "recovered"),
        ("Shell 폴더가 4.5초씩 두 번", "helper-timeout"),
        ("Shell 폴더를 열지 못했습니다.", "shell-failed"),
        ("네트워크 폴더에 접근할 수 없거나", "network-failed"),
        ("이 위치로 이동할 수 없습니다.", "submit-failed"),
        ("기본 파일 작업 엔진을 연결하지 못했습니다.", "native-link-failed"),
    ):
        if value.startswith(prefix):
            return category
    return "other"


def _owned_startup_summary(win, ui: dict, left: Path, right: Path) -> dict:
    """Bounded, failure-only UIA categories for the synthetic startup route.

    Never emit raw StatusText/ActivePaneText or paths outside the owned fixture.
    This differentiates a still-loading route, failed route, wrong active pane,
    and the presence of known test-only child entries without native logging.
    """
    value = ui.get("AddressBox", {}).get("value")
    if not value:
        address = "empty" if value == "" else "unavailable"
    elif value == "[outside test-owned scope]":
        address = "outside-owned"
    else:
        normalized = os.path.normcase(os.path.normpath(str(value))).casefold()
        if normalized == os.path.normcase(os.path.normpath(str(left))).casefold():
            address = "owned-left"
        elif normalized == os.path.normcase(os.path.normpath(str(right))).casefold():
            address = "owned-right"
        else:
            address = "other-owned"
    observed = {}
    for control in ("StatusText", "ActivePaneText"):
        observed[control] = None
        if win is None:
            continue
        try:
            spec = win.child_window(auto_id=control)
            if spec.exists(timeout=0.25):
                observed[control] = str(spec.window_text())
        except Exception:
            pass
    active = {"활성: 왼쪽": "left", "활성: 오른쪽": "right"}.get(
        observed["ActivePaneText"], "other" if observed["ActivePaneText"] is not None
        else "unavailable"
    )
    def fixture_visible(pane: str, label: str) -> bool:
        return any(
            node.get("type") == "ListItem" and
            (node.get("name") == label or node.get("name", "").startswith(label + " "))
            for node in ui.get(pane, {}).get("nodes", [])
        )
    return {
        "address_route": address,
        "active_pane": active,
        "status_category": _startup_status_category(observed["StatusText"]),
        "left_expected_child_visible": fixture_visible("LeftFiles", "Nested"),
        "right_expected_child_visible": fixture_visible("RightFiles", "Secondary"),
        "left_uia_list_items": sum(
            node.get("type") == "ListItem"
            for node in ui.get("LeftFiles", {}).get("nodes", [])
        ),
        "right_uia_list_items": sum(
            node.get("type") == "ListItem"
            for node in ui.get("RightFiles", {}).get("nodes", [])
        ),
    }


def capture_failure(*, base: Path, owned: Path, left: Path, right: Path,
                    win, hwnd: int | None, pid: int | None, error: Exception):
    """Return evidence directory. A missing app/UIA peer is an evidence fact."""
    base, owned, left, right = map(Path, (base, owned, left, right))
    if not (_inside(owned, base) and _inside(left, owned)
            and _inside(right, owned)):
        raise ValueError("Refusing to collect outside the synthetic GUI fixture")
    output = base.parent / "remote-evidence" / "gui-failure" / uuid4().hex
    output.mkdir(parents=True, exist_ok=False)
    labels = _owned_labels(left, right)
    manifest = {"schema": 1, "result": "FAIL",
                "exception": type(error).__name__,
                "note": "Only synthetic fixture and launched app window inspected"}
    try:
        manifest["screenshot"] = _screenshot_app_window(
            win, hwnd, pid, output / "application.png")
        ui = {}
        for pane in ("LeftFiles", "RightFiles", "LeftTabs", "RightTabs"):
            ui[pane] = _uia_pane(win, pane, labels) if win is not None else {
                "present": False, "nodes": []}
        ui["AddressBox"] = {"present": False}
        if win is not None:
            try:
                spec = win.child_window(auto_id="AddressBox")
                if spec.exists(timeout=.25):
                    ui["AddressBox"] = {
                        "present": True,
                        "value": _safe_address(spec.get_value(), owned)}
            except Exception as exc:
                ui["AddressBox"] = {"error_type": type(exc).__name__}
        ui["Startup"] = _owned_startup_summary(win, ui, left, right)
        (output / "panes.json").write_text(json.dumps(ui, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
        disk = {"left": {"path": _safe_address(left, owned),
                         **_disk_rows(left, owned)},
                "right": {"path": _safe_address(right, owned),
                          **_disk_rows(right, owned)}}
        (output / "owned-files.json").write_text(
            json.dumps(disk, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        manifest["collection_error"] = type(exc).__name__
    finally:
        # Traceback is from our harness, not a dump of UI contents or user data.
        trace = "".join(traceback.format_exception(
            type(error), error, error.__traceback__))[-16000:]
        (output / "failure-trace.txt").write_text(trace, encoding="utf-8")
        (output / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
