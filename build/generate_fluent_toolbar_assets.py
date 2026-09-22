#!/usr/bin/env python3
"""Generate deterministic Fluent toolbar masks from vendored Microsoft SVGs.

The runtime toolbar keeps the historical 51-frame bitmap/index contract.
Only the representative commands listed in toolbar_manifest.json are
rasterized. Generated output is a pair of C++ include fragments containing
theme-neutral 1-bit masks. Runtime code applies ThemePalette.mText so one
canonical SVG source works for System, Light, Dark, and High Contrast.

No third-party Python package or network access is required. The supported
SVG subset is deliberately narrow and validated: absolute M/L/H/V/C/Z path
commands, nonzero path fill, no transforms, and a rectangular viewBox.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
FLUENT_DIR = ROOT / "src" / "fxfile" / "res" / "fluent"
MANIFEST_PATH = FLUENT_DIR / "toolbar_manifest.json"

_NUMBER_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_TOKEN_RE = re.compile(rf"[MLHVCZ]|{_NUMBER_RE}")
_SUPPORTED_COMMANDS = frozenset("MLHVCZ")
_CUBIC_STEPS = 32
_SUPERSAMPLE = 4

Point = Tuple[float, float]
PathPoints = List[Point]


class AssetError(RuntimeError):
    pass


def _tokenize_path(data: str) -> List[str]:
    tokens = _TOKEN_RE.findall(data.replace(",", " "))
    letters = {ch for ch in re.findall(r"[A-Za-z]", data)}
    unsupported = letters - _SUPPORTED_COMMANDS
    if unsupported:
        raise AssetError(
            "unsupported SVG path command(s): " + ", ".join(sorted(unsupported))
        )
    return tokens


def _flatten_path(data: str) -> List[PathPoints]:
    tokens = _tokenize_path(data)
    index = 0
    command: Optional[str] = None
    current: Point = (0.0, 0.0)
    start: Point = (0.0, 0.0)
    subpath: Optional[PathPoints] = None
    paths: List[PathPoints] = []

    def number() -> float:
        nonlocal index
        if index >= len(tokens) or tokens[index] in _SUPPORTED_COMMANDS:
            raise AssetError("malformed SVG path")
        value = float(tokens[index])
        index += 1
        return value

    def begin(point: Point) -> None:
        nonlocal subpath, start, current
        if subpath and len(subpath) >= 2:
            paths.append(subpath)
        subpath = [point]
        start = point
        current = point

    def line(point: Point) -> None:
        nonlocal subpath, current
        if subpath is None:
            raise AssetError("SVG line command before moveto")
        subpath.append(point)
        current = point

    while index < len(tokens):
        if tokens[index] in _SUPPORTED_COMMANDS:
            command = tokens[index]
            index += 1
        elif command is None:
            raise AssetError("SVG path does not start with a command")

        if command == "M":
            begin((number(), number()))
            command = "L"
            while index < len(tokens) and tokens[index] not in _SUPPORTED_COMMANDS:
                line((number(), number()))
        elif command == "L":
            while index < len(tokens) and tokens[index] not in _SUPPORTED_COMMANDS:
                line((number(), number()))
        elif command == "H":
            while index < len(tokens) and tokens[index] not in _SUPPORTED_COMMANDS:
                line((number(), current[1]))
        elif command == "V":
            while index < len(tokens) and tokens[index] not in _SUPPORTED_COMMANDS:
                line((current[0], number()))
        elif command == "C":
            while index < len(tokens) and tokens[index] not in _SUPPORTED_COMMANDS:
                x1, y1 = number(), number()
                x2, y2 = number(), number()
                x3, y3 = number(), number()
                x0, y0 = current
                for step in range(1, _CUBIC_STEPS + 1):
                    t = step / _CUBIC_STEPS
                    mt = 1.0 - t
                    line((
                        mt * mt * mt * x0
                        + 3.0 * mt * mt * t * x1
                        + 3.0 * mt * t * t * x2
                        + t * t * t * x3,
                        mt * mt * mt * y0
                        + 3.0 * mt * mt * t * y1
                        + 3.0 * mt * t * t * y2
                        + t * t * t * y3,
                    ))
        elif command == "Z":
            if subpath is None:
                raise AssetError("SVG close command before moveto")
            if subpath[-1] != start:
                subpath.append(start)
            current = start
            if len(subpath) >= 3:
                paths.append(subpath)
            subpath = None
            command = None
        else:
            raise AssetError(f"unsupported SVG path command: {command}")

    if subpath and len(subpath) >= 2:
        if subpath[-1] != subpath[0]:
            subpath.append(subpath[0])
        paths.append(subpath)

    if not paths:
        raise AssetError("SVG contains no drawable path")
    return paths


def _load_svg(path: Path) -> Tuple[Tuple[float, float, float, float], List[PathPoints]]:
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except (OSError, ET.ParseError) as exc:
        raise AssetError(f"{path}: cannot parse SVG: {exc}") from exc

    if root.get("transform"):
        raise AssetError(f"{path}: root transform is not supported")

    view_box = root.get("viewBox")
    if view_box is None:
        raise AssetError(f"{path}: missing viewBox")

    parts = [float(item) for item in view_box.replace(",", " ").split()]
    if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        raise AssetError(f"{path}: invalid viewBox {view_box!r}")
    parsed_view_box = (parts[0], parts[1], parts[2], parts[3])

    paths: List[PathPoints] = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "svg":
            continue
        if tag != "path":
            raise AssetError(f"{path}: unsupported SVG element <{tag}>")
        if element.get("transform"):
            raise AssetError(f"{path}: path transform is not supported")
        if element.get("fill-rule", "nonzero") != "nonzero":
            raise AssetError(f"{path}: only nonzero fill-rule is supported")
        fill = element.get("fill", "#212121")
        if fill.upper() != "#212121":
            raise AssetError(f"{path}: unexpected Fluent source fill {fill!r}")
        data = element.get("d")
        if not data:
            raise AssetError(f"{path}: path is missing d attribute")
        paths.extend(_flatten_path(data))

    if not paths:
        raise AssetError(f"{path}: no path data")
    return parsed_view_box, paths


def _is_left(p0: Point, p1: Point, x: float, y: float) -> float:
    return (p1[0] - p0[0]) * (y - p0[1]) - (x - p0[0]) * (p1[1] - p0[1])


def _inside_nonzero(paths: List[PathPoints], x: float, y: float) -> bool:
    winding = 0
    for path in paths:
        for p0, p1 in zip(path, path[1:]):
            if p0[1] <= y:
                if p1[1] > y and _is_left(p0, p1, x, y) > 0:
                    winding += 1
            elif p1[1] <= y and _is_left(p0, p1, x, y) < 0:
                winding -= 1
    return winding != 0


def _transform_paths(
    paths: List[PathPoints],
    view_box: Tuple[float, float, float, float],
    cell: int,
    design: int,
) -> List[PathPoints]:
    vb_x, vb_y, vb_w, vb_h = view_box
    scale = min(design / vb_w, design / vb_h)
    width = vb_w * scale
    height = vb_h * scale
    offset_x = (cell - width) / 2.0 - vb_x * scale
    offset_y = (cell - height) / 2.0 - vb_y * scale
    return [
        [
            (point[0] * scale + offset_x, point[1] * scale + offset_y)
            for point in path
        ]
        for path in paths
    ]


def _render_cell(svg_path: Path, cell: int, design: int) -> List[bool]:
    view_box, raw_paths = _load_svg(svg_path)
    paths = _transform_paths(raw_paths, view_box, cell, design)

    min_x = max(0, math.floor(min(p[0] for path in paths for p in path)) - 1)
    max_x = min(cell - 1, math.ceil(max(p[0] for path in paths for p in path)) + 1)
    min_y = max(0, math.floor(min(p[1] for path in paths for p in path)) - 1)
    max_y = min(cell - 1, math.ceil(max(p[1] for path in paths for p in path)) + 1)

    pixels = [False] * (cell * cell)
    sample_count = _SUPERSAMPLE * _SUPERSAMPLE
    threshold = (sample_count + 1) // 2

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            covered = 0
            for sy in range(_SUPERSAMPLE):
                py = y + (sy + 0.5) / _SUPERSAMPLE
                for sx in range(_SUPERSAMPLE):
                    px = x + (sx + 0.5) / _SUPERSAMPLE
                    if _inside_nonzero(paths, px, py):
                        covered += 1
            if covered >= threshold:
                pixels[y * cell + x] = True
    return pixels


def _pack_mask(pixels: List[bool]) -> bytes:
    packed = bytearray((len(pixels) + 7) // 8)
    for index, enabled in enumerate(pixels):
        if enabled:
            packed[index // 8] |= 0x80 >> (index % 8)
    return bytes(packed)


def _load_manifest() -> dict:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetError(f"cannot read {MANIFEST_PATH}: {exc}") from exc

    if manifest.get("version") != 1:
        raise AssetError("unsupported toolbar manifest version")
    frame_count = manifest.get("frame_count")
    if not isinstance(frame_count, int) or frame_count != 51:
        raise AssetError("toolbar frame_count must remain 51")

    frames: Set[int] = set()
    commands: Set[str] = set()
    items = manifest.get("commands")
    if not isinstance(items, list) or not items:
        raise AssetError("toolbar manifest has no commands")

    for item in items:
        frame = item.get("frame")
        command = item.get("command")
        if not isinstance(frame, int) or not 0 <= frame < frame_count:
            raise AssetError(f"invalid frame index: {frame!r}")
        if frame in frames:
            raise AssetError(f"duplicate frame index: {frame}")
        if not isinstance(command, str) or not command:
            raise AssetError(f"invalid command for frame {frame}")
        if command in commands:
            raise AssetError(f"duplicate command: {command}")
        frames.add(frame)
        commands.add(command)

        for key in ("small_svg", "large_svg"):
            name = item.get(key)
            if not isinstance(name, str) or not name.endswith(".svg"):
                raise AssetError(f"{command}: invalid {key}")
            if not (FLUENT_DIR / name).is_file():
                raise AssetError(f"{command}: missing source {name}")

    for size_name in ("small", "large"):
        spec = manifest.get("sizes", {}).get(size_name, {})
        cell = spec.get("cell")
        design = spec.get("design")
        if not isinstance(cell, int) or not isinstance(design, int):
            raise AssetError(f"invalid {size_name} size contract")
        output = manifest.get("outputs", {}).get(size_name)
        if not isinstance(output, str) or not output.endswith(".inc"):
            raise AssetError(f"invalid {size_name} generated output")

    return manifest


def _format_include(manifest: dict, size_name: str) -> str:
    spec = manifest["sizes"][size_name]
    cell = int(spec["cell"])
    design = int(spec["design"])
    svg_key = f"{size_name}_svg"
    byte_count = (cell * cell + 7) // 8

    lines = [
        "// Generated by build/generate_fluent_toolbar_assets.py. DO NOT EDIT.",
        f"// {size_name}: {cell}x{cell}, {byte_count} bytes per command mask.",
    ]

    for item in manifest["commands"]:
        pixels = _render_cell(FLUENT_DIR / item[svg_key], cell, design)
        packed = _pack_mask(pixels)
        if len(packed) != byte_count:
            raise AssetError(f"{item['command']}: generated mask size mismatch")

        values = ", ".join(f"0x{value:02x}" for value in packed)
        lines.append(
            "    { "
            + values
            + f" }}, // frame {item['frame']} {item['command']}"
        )

    lines.append("")
    return "\n".join(lines)


def _generate_all() -> Dict[str, str]:
    manifest = _load_manifest()
    generated: Dict[str, str] = {}
    for size_name in ("small", "large"):
        generated[manifest["outputs"][size_name]] = _format_include(
            manifest, size_name
        )
    return generated


def _check(generated: Dict[str, str]) -> int:
    mismatched: List[str] = []
    for name, expected in generated.items():
        path = FLUENT_DIR / name
        try:
            actual = path.read_text(encoding="utf-8")
        except OSError:
            mismatched.append(name)
            continue
        if actual != expected:
            mismatched.append(name)

    if mismatched:
        print(
            "Fluent toolbar generated masks are stale or missing: "
            + ", ".join(mismatched),
            file=sys.stderr,
        )
        print(
            "Run: python build/generate_fluent_toolbar_assets.py --write",
            file=sys.stderr,
        )
        return 1

    print("Fluent toolbar generated masks: PASS")
    return 0


def _write(generated: Dict[str, str]) -> int:
    for name, content in generated.items():
        path = FLUENT_DIR / name
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()

    try:
        generated = _generate_all()
        if args.write:
            return _write(generated)
        return _check(generated)
    except AssetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
