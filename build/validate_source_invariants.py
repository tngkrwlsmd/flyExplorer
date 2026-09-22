#!/usr/bin/env python3
"""Fast source-level invariant and regression preflight checks for flyExplorer.

This guard intentionally covers cheap, deterministic invariants and known
regressions that should fail before GYP generation or a Visual Studio build.
It does not replace compilation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FXFILE_SRC = ROOT / "src" / "fxfile"

# Project-wide helpers that are not guaranteed by stdafx.h must be included
# directly by each translation unit that uses them. Add future cross-cutting
# dependencies here instead of relying on accidental transitive includes.
DIRECT_HEADER_RULES = (
    {
        "name": "ModernUI",
        "tokens": re.compile(r"\bui::(?:ModernUI|ThemePalette)\b|\bWM_DPICHANGED\b"),
        "required_header_basename": "ModernUI.h",
    },
)

INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^">]+)[">]', re.MULTILINE)
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//.*?$", re.MULTILINE)

DIRECT_CDIALOG_ALLOWLIST = {
    "src/fxfile/gui/ModernDialog.h",
    "src/fxfile/gui/ResizingDialog.h",
    "src/fxfile/cfg/cfg_dlg.h",
    "src/fxfile/cfg/cfg_main_dlg.h",
    "src/fxfile/cmd/title_dlg.h",
    "src/fxfile/cmd/drive_detail_dlg.h",
}
DIRECT_CDIALOG_RE = re.compile(
    r"class\s+\w+[^;{\n]*:\s*public\s+CDialog(?:\s*[,\{])"
)
MODERN_DIALOG_RE = re.compile(
    r"class\s+\w+[^;{\n]*:\s*public\s+CModernDialog(?:\s*[,\{])"
)


def strip_comments(text: str) -> str:
    return LINE_COMMENT_RE.sub("", BLOCK_COMMENT_RE.sub("", text))


def direct_include_basenames(text: str) -> set[str]:
    return {Path(match).name for match in INCLUDE_RE.findall(text)}


def validate_translation_units() -> list[str]:
    errors: list[str] = []

    for path in sorted(FXFILE_SRC.rglob("*.cpp")):
        text = path.read_text(encoding="utf-8", errors="replace")
        code = strip_comments(text)
        includes = direct_include_basenames(text)

        for rule in DIRECT_HEADER_RULES:
            if not rule["tokens"].search(code):
                continue

            required = str(rule["required_header_basename"])
            if required not in includes:
                rel = path.relative_to(ROOT).as_posix()
                errors.append(
                    f"{rel}: uses {rule['name']} symbols but does not directly include {required}"
                )

    return errors


def validate_window_frame_theme_integration() -> list[str]:
    errors: list[str] = []
    modern_ui_header_path = FXFILE_SRC / "gui" / "ModernUI.h"
    modern_ui_source_path = FXFILE_SRC / "gui" / "ModernUI.cpp"
    main_frame_path = FXFILE_SRC / "main_frame.cpp"

    try:
        modern_ui_header = modern_ui_header_path.read_text(encoding="utf-8")
        modern_ui_source = modern_ui_source_path.read_text(encoding="utf-8")
        main_frame = main_frame_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"ModernUI title-bar integration source cannot be read: {exc}"]

    if "applyWindowFrameTheme(HWND aHwnd)" not in modern_ui_header:
        errors.append("src/fxfile/gui/ModernUI.h: missing window-frame theme helper declaration")

    for token in ("DwmSetWindowAttribute", "DWMWA_USE_IMMERSIVE_DARK_MODE", "dwmapi.dll"):
        if token not in modern_ui_source:
            errors.append(f"src/fxfile/gui/ModernUI.cpp: missing title-bar integration token {token}")

    if main_frame.count("ui::ModernUI::applyWindowFrameTheme(m_hWnd);") < 3:
        errors.append(
            "src/fxfile/main_frame.cpp: window-frame theme must be applied on create, settings change, and theme change"
        )

    return errors


def validate_common_control_theme_integration() -> list[str]:
    errors: list[str] = []
    modern_ui_header_path = FXFILE_SRC / "gui" / "ModernUI.h"
    modern_ui_source_path = FXFILE_SRC / "gui" / "ModernUI.cpp"

    try:
        modern_ui_header = modern_ui_header_path.read_text(encoding="utf-8")
        modern_ui_source = modern_ui_source_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"ModernUI control-theme integration source cannot be read: {exc}"]

    if "applyExplorerControlTheme(HWND aHwnd)" not in modern_ui_header:
        errors.append("src/fxfile/gui/ModernUI.h: missing Explorer control-theme helper declaration")
    if "resetControlTheme(HWND aHwnd)" not in modern_ui_header:
        errors.append("src/fxfile/gui/ModernUI.h: missing control-theme reset helper declaration")

    for token in ("SetWindowTheme", "uxtheme.dll", 'L"Explorer"'):
        if token not in modern_ui_source:
            errors.append(f"src/fxfile/gui/ModernUI.cpp: missing control-theme integration token {token}")

    for rel_path in ("gui/ListCtrlEx.cpp", "gui/TreeCtrlEx.cpp"):
        control_path = FXFILE_SRC / rel_path
        try:
            control_source = control_path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{control_path.relative_to(ROOT)}: cannot read: {exc}")
            continue

        if "ModernUI::applyExplorerControlTheme" not in control_source:
            errors.append(f"{control_path.relative_to(ROOT)}: Explorer theme is not routed through ModernUI")
        if "ModernUI::resetControlTheme" not in control_source:
            errors.append(f"{control_path.relative_to(ROOT)}: theme reset is not routed through ModernUI")
        if re.search(r"(?<!ModernUI::)SetWindowTheme\s*\(", strip_comments(control_source)):
            errors.append(f"{control_path.relative_to(ROOT)}: direct SetWindowTheme call remains")

    return errors


def validate_modern_dialog_migration() -> list[str]:
    """Keep standard dialogs on the shared ModernUI base unless explicitly owned elsewhere."""

    errors: list[str] = []
    modern_dialog_header = FXFILE_SRC / "gui" / "ModernDialog.h"
    modern_dialog_source = FXFILE_SRC / "gui" / "ModernDialog.cpp"
    gyp_path = FXFILE_SRC / "fxfile.gyp"

    try:
        modern_header = modern_dialog_header.read_text(encoding="utf-8")
        modern_source = modern_dialog_source.read_text(encoding="utf-8")
        gyp = gyp_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"ModernDialog integration source cannot be read: {exc}"]

    required_base_tokens = (
        "class CModernDialog : public CDialog",
        "refreshModernAppearance",
        "ON_WM_ERASEBKGND()",
        "ON_WM_CTLCOLOR()",
        "ON_WM_SETTINGCHANGE()",
        "ON_WM_SYSCOLORCHANGE()",
        "WM_THEMECHANGED",
        "WM_DPICHANGED",
        "WM_DPICHANGED_AFTERPARENT",
        "ModernUI::applyWindowFrameTheme",
        "ModernUI::applyExplorerControlTheme",
    )
    base_text = modern_header + "\n" + modern_source
    for token in required_base_tokens:
        if token not in base_text:
            errors.append(f"ModernDialog integration is missing token {token}")

    for entry in ("./gui/ModernDialog.cpp", "./gui/ModernDialog.h"):
        if entry not in gyp:
            errors.append(f"src/fxfile/fxfile.gyp: missing source registration {entry}")

    for path in sorted(FXFILE_SRC.rglob("*.h")):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        code = strip_comments(text)

        if DIRECT_CDIALOG_RE.search(code) and rel not in DIRECT_CDIALOG_ALLOWLIST:
            errors.append(
                f"{rel}: direct CDialog inheritance is not allowlisted; "
                "use CModernDialog or document specialized ModernUI ownership"
            )

        if MODERN_DIALOG_RE.search(code) and path.name != "ModernDialog.h":
            if "ModernDialog.h" not in direct_include_basenames(text):
                errors.append(
                    f"{rel}: CModernDialog subclass does not directly include ModernDialog.h"
                )

    return errors


def validate_toolbar_custom_draw_regression() -> list[str]:
    """Prevent recurrence of the ToolbarWindow32 color-message compile failure."""

    errors: list[str] = []
    toolbar_path = FXFILE_SRC / "gui" / "rebar" / "ToolBarEx.cpp"

    try:
        toolbar_source = toolbar_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{toolbar_path.relative_to(ROOT)}: cannot read: {exc}"]

    toolbar_code = strip_comments(toolbar_source)
    rel = toolbar_path.relative_to(ROOT).as_posix()

    # These messages belong to no supported ToolbarWindow32 contract. A previous
    # dark-mode change confused them with RB_SETBKCOLOR/RB_SETTEXTCOLOR and broke
    # the Visual Studio build with C2065 before runtime tests could start.
    for token in ("TB_SETBKCOLOR", "TB_SETTEXTCOLOR"):
        if token in toolbar_code:
            errors.append(
                f"{rel}: unsupported toolbar color message {token} reintroduced; "
                "use the existing NM_CUSTOMDRAW/NMTBCUSTOMDRAW path"
            )

    required_tokens = (
        "ApplyDarkToolBarCustomDraw",
        "ON_NOTIFY_REFLECT( NM_CUSTOMDRAW, OnCustomDraw )",
        "aCustomDraw->clrBtnFace",
        "aCustomDraw->clrText",
        "aCustomDraw->clrHighlightHotTrack",
        "ApplyDarkToolBarCustomDraw(lpNMCustomDraw)",
    )
    for token in required_tokens:
        if token not in toolbar_code:
            errors.append(f"{rel}: missing toolbar custom-draw regression token {token}")

    return errors


def validate_ui_resource_contracts() -> list[str]:
    """Protect icon/bitmap frame geometry and canonical resource wiring."""

    errors: list[str] = []
    resource_dir = FXFILE_SRC / "res"
    rc_path = FXFILE_SRC / "fxfile.rc"
    gyp_path = FXFILE_SRC / "fxfile.gyp"
    main_toolbar_path = FXFILE_SRC / "main_toolbar.cpp"
    scrap_toolbar_path = FXFILE_SRC / "file_scrap_toolbar.cpp"
    cfg_main_path = FXFILE_SRC / "cfg" / "cfg_main_dlg.cpp"

    def read_u16(data: bytes, offset: int) -> int:
        return int.from_bytes(data[offset:offset + 2], "little")

    def read_u32(data: bytes, offset: int) -> int:
        return int.from_bytes(data[offset:offset + 4], "little")

    def bitmap_geometry(name: str) -> tuple[int, int, int] | None:
        path = resource_dir / name
        try:
            data = path.read_bytes()
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read: {exc}")
            return None

        if len(data) < 54 or data[:2] != b"BM":
            errors.append(f"{path.relative_to(ROOT)}: invalid BMP header")
            return None

        width = int.from_bytes(data[18:22], "little", signed=True)
        height = int.from_bytes(data[22:26], "little", signed=True)
        bpp = read_u16(data, 28)
        return width, abs(height), bpp

    bitmap_contracts = {
        "config_tree.bmp": (528, 16, 16, 33),
        "tb_main_cold_small.bmp": (816, 16, 16, 51),
        "tb_main_hot_small.bmp": (816, 16, 16, 51),
        "tb_main_cold_large.bmp": (1122, 22, 22, 51),
        "tb_main_hot_large.bmp": (1122, 22, 22, 51),
        "tb_drive.bmp": (16, 16, 16, 1),
        "tb_rename.bmp": (176, 16, 16, 11),
        "sync_images.bmp": (80, 16, 16, 5),
    }

    for name, (expected_width, expected_height, cell_width, expected_frames) in bitmap_contracts.items():
        geometry = bitmap_geometry(name)
        if geometry is None:
            continue

        width, height, bpp = geometry
        rel = (resource_dir / name).relative_to(ROOT).as_posix()
        if bpp != 16:
            errors.append(f"{rel}: expected legacy mask-strip 16bpp contract, got {bpp}bpp")

        if (width, height) != (expected_width, expected_height):
            errors.append(
                f"{rel}: geometry {width}x{height} changed; "
                f"expected {expected_width}x{expected_height}"
            )
            continue

        if width % cell_width != 0 or width // cell_width != expected_frames:
            errors.append(
                f"{rel}: frame contract changed; expected {expected_frames} frames "
                f"at {cell_width}px"
            )

    icon_path = resource_dir / "fxfile.ico"
    try:
        icon = icon_path.read_bytes()
    except OSError as exc:
        errors.append(f"{icon_path.relative_to(ROOT)}: cannot read: {exc}")
    else:
        if len(icon) < 6 or read_u16(icon, 0) != 0 or read_u16(icon, 2) != 1:
            errors.append("src/fxfile/res/fxfile.ico: invalid ICO header")
        else:
            count = read_u16(icon, 4)
            frames: dict[int, int] = {}
            for index in range(count):
                entry = 6 + index * 16
                if entry + 16 > len(icon):
                    errors.append("src/fxfile/res/fxfile.ico: truncated icon directory")
                    break

                width = icon[entry] or 256
                height = icon[entry + 1] or 256
                bpp = read_u16(icon, entry + 6)
                if width == height:
                    frames[width] = max(frames.get(width, 0), bpp)

            for size in (16, 32, 48, 256):
                if size not in frames:
                    errors.append(f"src/fxfile/res/fxfile.ico: missing {size}x{size} frame")
            if frames.get(256, 0) < 32:
                errors.append("src/fxfile/res/fxfile.ico: 256x256 frame must be 32-bit")

    try:
        rc = rc_path.read_text(encoding="utf-8", errors="replace")
        gyp = gyp_path.read_text(encoding="utf-8", errors="replace")
        main_toolbar = main_toolbar_path.read_text(encoding="utf-8", errors="replace")
        scrap_toolbar = scrap_toolbar_path.read_text(encoding="utf-8", errors="replace")
        cfg_main = cfg_main_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        errors.append(f"UI resource wiring source cannot be read: {exc}")
        return errors

    rc_tokens = (
        'IDR_MAINFRAME           ICON                    "res\\\\fxfile.ico"',
        'IDB_TB_MAIN_HOT_LARGE   BITMAP                  "res\\\\tb_main_hot_large.bmp"',
        'IDB_TB_MAIN_COLD_LARGE  BITMAP                  "res\\\\tb_main_cold_large.bmp"',
        'IDB_TB_MAIN_HOT_SMALL   BITMAP                  "res\\\\tb_main_hot_small.bmp"',
        'IDB_TB_MAIN_COLD_SMALL  BITMAP                  "res\\\\tb_main_cold_small.bmp"',
        'IDB_CONFIG_TREE         BITMAP                  "res\\\\config_tree.bmp"',
    )
    for token in rc_tokens:
        if token not in rc:
            errors.append(f"src/fxfile/fxfile.rc: missing resource mapping {token}")

    for asset in (
        "fxfile.ico",
        "config_tree.bmp",
        "tb_main_cold_large.bmp",
        "tb_main_cold_small.bmp",
        "tb_main_hot_large.bmp",
        "tb_main_hot_small.bmp",
        "tb_drive.bmp",
        "tb_rename.bmp",
        "sync_images.bmp",
    ):
        if f"'./res/{asset}'" not in gyp:
            errors.append(f"src/fxfile/fxfile.gyp: missing UI asset registration ./res/{asset}")

    toolbar_contract = (
        "SetIconSize(CSize(22, 22), CSize(16, 16));",
        "IDB_TB_MAIN_COLD_SMALL, IDB_TB_MAIN_HOT_SMALL, IDB_TB_MAIN_HOT_SMALL",
        "IDB_TB_MAIN_COLD_LARGE, IDB_TB_MAIN_HOT_LARGE, IDB_TB_MAIN_HOT_LARGE",
    )
    for source_name, source in (
        ("src/fxfile/main_toolbar.cpp", main_toolbar),
        ("src/fxfile/file_scrap_toolbar.cpp", scrap_toolbar),
    ):
        for token in toolbar_contract:
            if token not in source:
                errors.append(f"{source_name}: toolbar image mapping changed near {token}")

    if "sBitmap.LoadBitmap(IDB_CONFIG_TREE);" not in cfg_main:
        errors.append("src/fxfile/cfg/cfg_main_dlg.cpp: config tree bitmap resource changed")
    if "mImgList.Create(16, 16" not in cfg_main:
        errors.append("src/fxfile/cfg/cfg_main_dlg.cpp: config tree 16px frame contract changed")

    return errors


def validate_modern_ui_registration() -> list[str]:
    errors: list[str] = []
    gyp_path = ROOT / "src" / "fxfile" / "fxfile.gyp"
    manifest_path = ROOT / "src" / "fxfile" / "res" / "fxfile.exe.manifest"

    try:
        gyp = gyp_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{gyp_path.relative_to(ROOT)}: cannot read: {exc}"]

    for entry in ("./gui/ModernUI.cpp", "./gui/ModernUI.h"):
        if entry not in gyp:
            errors.append(f"src/fxfile/fxfile.gyp: missing source registration {entry}")

    if "AdditionalManifestFiles" not in gyp or "./res/fxfile.exe.manifest" not in gyp:
        errors.append(
            "src/fxfile/fxfile.gyp: Modern UI manifest is not registered with VCManifestTool"
        )

    try:
        manifest = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{manifest_path.relative_to(ROOT)}: cannot read: {exc}")
    else:
        if "PerMonitorV2, PerMonitor" not in manifest:
            errors.append(
                "src/fxfile/res/fxfile.exe.manifest: Per-Monitor V2 DPI awareness is missing"
            )

    return errors


def main() -> int:
    errors = validate_translation_units()
    errors.extend(validate_window_frame_theme_integration())
    errors.extend(validate_common_control_theme_integration())
    errors.extend(validate_modern_dialog_migration())
    errors.extend(validate_toolbar_custom_draw_regression())
    errors.extend(validate_ui_resource_contracts())
    errors.extend(validate_modern_ui_registration())

    if errors:
        print("Source invariant/regression preflight: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Source invariant/regression preflight: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
