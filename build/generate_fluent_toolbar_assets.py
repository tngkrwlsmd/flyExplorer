#!/usr/bin/env python3
"""Generate deterministic Fluent toolbar overlay strips.

The runtime toolbar keeps the historical 51-frame bitmap/index contract.
This generator rasterizes only the representative Microsoft Fluent SVG
commands listed in toolbar_manifest.json and leaves every other frame fully
transparent (RGB 255,0,255 mask).

No third-party Python packages are used. The supported SVG subset is
intentionally narrow and validated: absolute M/L/H/V/C/Z path commands,
plain path fills, and a rectangular viewBox. This matches the vendored
Fluent command sources in this repository.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLUENT_DIR = ROOT / "src" / "fxfile" / "res" / "fluent"
RESOURCE_DIR = ROOT / "src" / "fxfile" / "res"
MANIFEST_PATH = FLUENT_DIR / "toolbar_manifest.json"

_NUMBER_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_TOKEN_RE = re.compile(rf"[MLHVCZ]|{_NUMBER_RE}")
_SUPPORTED_COMMANDS = frozenset("MLHVCZ")
_CUBIC_STEPS = 32
_SUPERSAMPLE = 4


class AssetError(RuntimeError):
    pass


def _parse_hex_color(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise AssetError(f"invalid RGB color: {value}")
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))


def _rgb555(color: tuple[int, int, int]) -> int:
    r, g, b = color
    r5 = (r * 31 + 127) // 255
    g5 = (g * 31 + 127) // 255
    b5 = (b * 31 + 127) // 255
    return (r5 << 10) | (g5 << 5) | b5


def _tokenize_path(data: str) -> list[str]:
    tokens = _TOKEN_RE.findall(data.replace(",", " "))
    letters = {ch for ch in re.findall(r"[A-Za-z]", data)}
    unsupported = letters - _SUPPORTED_COMMANDS
    if unsupported:
        raise AssetError(
            "unsupported SVG path command(s): " + ", ".join(sorted(unsupported))
        )
    return tokens


def _flatten_path(data: str) -> list[list[tuple[float, float]]]:
    tokens = _tokenize_path(data)
    index = 0
    command: str | None = None
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    subpath: list[tuple[float, float]] | None = None
    paths: list[list[tuple[float, float]]] = []

    def number() -> float:
        nonlocal index
        if index >= len(tokens) or tokens[index] in _SUPPORTED_COMMANDS:
            raise AssetError("malformed SVG path")
        value = float(tokens[index])
        index += 1
        return value

    def begin(point: tuple[float, float]) -> None:
        nonlocal subpath, start, current
        if subpath and len(subpath) >= 2:
            paths.append(subpath)
        subpath = [point]
        start = point
        current = point

    def line(point: tuple[float, float]) -> None:
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
            point = (number(), number())
            begin(point)
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
                    x = (
                        mt * mt * mt * x0
                        + 3.0 * mt * mt * t * x1
                        + 3.0 * mt * t * t * x2
                        + t * t * t * x3
                    )
                    y = (
                        mt * mt * mt * y0
                        + 3.0 * mt * mt * t * y1
                        + 3.0 * mt * t * t * y2
                        + t * t * t * y3
                    )
                    line((x, y))
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


def _load_svg(path: Path) -> tuple[tuple[float, float, float, float], list[list[tuple[float, float]]]]:
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
    vb = (parts[0], parts[1], parts[2], parts[3])

    paths: list[list[tuple[float, float]]] = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in ("svg",):
            continue
        if tag != "path":
            raise AssetError(f"{path}: unsupported SVG element <{tag}>")
        if element.get("transform"):
            raise AssetError(f"{path}: path transform is not supported")
        fill_rule = element.get("fill-rule", "nonzero")
        if fill_rule != "nonzero":
            raise AssetError(f"{path}: unsupported fill-rule {fill_rule!r}")
        data = element.get("d")
        if not data:
            raise AssetError(f"{path}: path is missing d attribute")
        paths.extend(_flatten_path(data))

    if not paths:
        raise AssetError(f"{path}: no path data")
    return vb, paths


def _is_left(
    p0: tuple[float, float],
    p1: tuple[float, float],
    x: float,
    y: float,
) -> float:
    return (p1[0] - p0[0]) * (y - p0[1]) - (x - p0[0]) * (p1[1] - p0[1])


def _inside_nonzero(
    paths: list[list[tuple[float, float]]],
    x: float,
    y: float,
) -> bool:
    winding = 0
    for path in paths:
        for p0, p1 in zip(path, path[1:]):
            if p0[1] <= y:
                if p1[1] > y and _is_left(p0, p1, x, y) > 0:
                    winding += 1
            else:
                if p1[1] <= y and _is_left(p0, p1, x, y) < 0:
                    winding -= 1
    return winding != 0


def _transform_paths(
    paths: list[list[tuple[float, float]]],
    view_box: tuple[float, float, float, float],
    cell: int,
    design: int,
) -> list[list[tuple[float, float]]]:
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


def _render_cell(
    svg_path: Path,
    cell: int,
    design: int,
) -> list[bool]:
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


def _encode_bmp(
    frame_count: int,
    cell: int,
    frame_pixels: dict[int, list[bool]],
    glyph_color: tuple[int, int, int],
    mask_color: tuple[int, int, int],
) -> bytes:
    width = frame_count * cell
    height = cell
    stride = ((width * 2 + 3) // 4) * 4
    glyph = _rgb555(glyph_color)
    mask = _rgb555(mask_color)

    data = bytearray(stride * height)
    for y in range(height):
        target_y = height - 1 - y
        row = target_y * stride
        for frame in range(frame_count):
            pixels = frame_pixels.get(frame)
            for x in range(cell):
                value = glyph if pixels and pixels[y * cell + x] else mask
                offset = row + (frame * cell + x) * 2
                data[offset : offset + 2] = struct.pack("<H", value)

    pixel_offset = 54
    file_size = pixel_offset + len(data)
    header = struct.pack(
        "<2sIHHI",
        b"BM",
        file_size,
        0,
        0,
        pixel_offset,
    )
    info = struct.pack(
        "<IiiHHIIiiII",
        40,
        width,
        height,
        1,
        16,
        0,
        len(data),
        0,
        0,
        0,
        0,
    )
    return header + info + bytes(data)


def _load_manifest() -> dict:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetError(f"cannot read {MANIFEST_PATH}: {exc}") from exc

    if manifest.get("version") != 1:
        raise AssetError("unsupported toolbar manifest version")
    frame_count = manifest.get("frame_count")
    if not isinstance(frame_count, int) or frame_count <= 0:
        raise AssetError("invalid frame_count")

    frames: set[int] = set()
    commands: set[str] = set()
    for item in manifest.get("commands", []):
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

    return manifest


def _generate_all() -> dict[str, bytes]:
    manifest = _load_manifest()
    frame_count = manifest["frame_count"]
    mask_color = _parse_hex_color(manifest["mask_color"])

    raster_cache: dict[tuple[str, int, int], list[bool]] = {}
    frame_sets: dict[str, dict[int, list[bool]]] = {"small": {}, "large": {}}

    for size_name in ("small", "large"):
        spec = manifest["sizes"][size_name]
        cell = int(spec["cell"])
        design = int(spec["design"])
        svg_key = f"{size_name}_svg"
        for item in manifest["commands"]:
            svg_name = item[svg_key]
            cache_key = (svg_name, cell, design)
            if cache_key not in raster_cache:
                raster_cache[cache_key] = _render_cell(
                    FLUENT_DIR / svg_name,
                    cell,
                    design,
                )
            frame_sets[size_name][item["frame"]] = raster_cache[cache_key]

    generated: dict[str, bytes] = {}
    for theme_name, color_value in manifest["themes"].items():
        glyph_color = _parse_hex_color(color_value)
        for size_name in ("small", "large"):
            spec = manifest["sizes"][size_name]
            key = f"{theme_name}_{size_name}"
            output_name = manifest["outputs"][key]
            generated[output_name] = _encode_bmp(
                frame_count,
                int(spec["cell"]),
                frame_sets[size_name],
                glyph_color,
                mask_color,
            )
    return generated


def _check(generated: dict[str, bytes]) -> int:
    mismatched: list[str] = []
    for name, expected in generated.items():
        path = RESOURCE_DIR / name
        try:
            actual = path.read_bytes()
        except OSError:
            mismatched.append(name)
            continue
        if actual != expected:
            mismatched.append(name)

    if mismatched:
        print(
            "Fluent toolbar assets are stale or missing: "
            + ", ".join(mismatched),
            file=sys.stderr,
        )
        print(
            "Run: python build/generate_fluent_toolbar_assets.py --write",
            file=sys.stderr,
        )
        return 1

    print("Fluent toolbar generated assets: PASS")
    return 0


def _write(generated: dict[str, bytes]) -> int:
    for name, data in generated.items():
        path = RESOURCE_DIR / name
        path.write_bytes(data)
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
