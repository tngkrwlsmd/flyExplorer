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

    for token in (
        "DwmSetWindowAttribute",
        "DWMWA_USE_IMMERSIVE_DARK_MODE",
        "DWMWA_WINDOW_CORNER_PREFERENCE",
        "DWMWCP_ROUND",
        "dwmapi.dll",
    ):
        if token not in modern_ui_source:
            errors.append(f"src/fxfile/gui/ModernUI.cpp: missing title-bar integration token {token}")

    if main_frame.count("ui::ModernUI::applyWindowFrameTheme(m_hWnd);") < 3:
        errors.append(
            "src/fxfile/main_frame.cpp: window-frame theme must be applied on create, settings change, and theme change"
        )

    return errors


def validate_theme_mode_contract() -> list[str]:
    errors: list[str] = []
    paths = {
        "modern_h": FXFILE_SRC / "gui" / "ModernUI.h",
        "modern_cpp": FXFILE_SRC / "gui" / "ModernUI.cpp",
        "option_h": FXFILE_SRC / "option.h",
        "option_cpp": FXFILE_SRC / "option.cpp",
        "cfg_cpp": FXFILE_SRC / "cfg" / "cfg_appearance_dlg.cpp",
        "main_frame": FXFILE_SRC / "main_frame.cpp",
        "resource_h": FXFILE_SRC / "resource.h",
        "rc": FXFILE_SRC / "fxfile.rc",
    }

    contents: dict[str, str] = {}
    for name, path in paths.items():
        try:
            contents[name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read theme-mode contract: {exc}")

    if errors:
        return errors

    for token in ("ThemeModeSystem", "ThemeModeLight", "ThemeModeDark", "setThemeMode", "getThemeMode"):
        if token not in contents["modern_h"]:
            errors.append(f"src/fxfile/gui/ModernUI.h: missing theme-mode token {token}")

    for token in ("ThemeModeLight", "ThemeModeDark", "gThemeMode"):
        if token not in contents["modern_cpp"]:
            errors.append(f"src/fxfile/gui/ModernUI.cpp: missing explicit theme-mode implementation token {token}")

    if "mThemeMode" not in contents["option_h"]:
        errors.append("src/fxfile/option.h: missing persisted theme-mode field")
    if 'XPR_STRING_LITERAL("config.theme_mode")' not in contents["option_cpp"]:
        errors.append("src/fxfile/option.cpp: missing config.theme_mode persistence key")

    for token in (
        "IDC_CFG_APPEARANCE_THEME_MODE",
        "popup.cfg.body.appearance.theme_mode.system",
        "popup.cfg.body.appearance.theme_mode.light",
        "popup.cfg.body.appearance.theme_mode.dark",
    ):
        if token not in contents["cfg_cpp"]:
            errors.append(f"src/fxfile/cfg/cfg_appearance_dlg.cpp: missing theme selector token {token}")

    for token in (
        "ON_COMMAND_RANGE(ID_VIEW_THEME_SYSTEM, ID_VIEW_THEME_DARK, OnViewThemeMode)",
        "ON_UPDATE_COMMAND_UI_RANGE(ID_VIEW_THEME_SYSTEM, ID_VIEW_THEME_DARK, OnUpdateViewThemeMode)",
        "ui::ModernUI::setThemeMode(aOption.mConfig.mThemeMode);",
        "OptionManager::instance().saveConfigOption();",
    ):
        if token not in contents["main_frame"]:
            errors.append(f"src/fxfile/main_frame.cpp: missing runtime theme-mode token {token}")

    for token in ("ID_VIEW_THEME_SYSTEM", "ID_VIEW_THEME_LIGHT", "ID_VIEW_THEME_DARK"):
        if token not in contents["resource_h"] or token not in contents["rc"]:
            errors.append(f"theme command/resource wiring is missing token {token}")

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


def validate_custom_dialog_paint_regressions() -> list[str]:
    """Keep migrated custom-paint dialogs on ThemePalette/DPI-aware paths."""

    errors: list[str] = []
    contracts = {
        "cmd/about_dlg.cpp": {
            "required": (
                "ModernUI::getPalette",
                "ModernUI::loadIconResource",
                "ModernUI::scale",
                "sPalette.mSurface",
                "sPalette.mSeparator",
                "sPalette.mText",
            ),
            "forbidden": (
                "FillSolidRect(sRect, RGB(255,255,255))",
                "LoadIcon(IDR_MAINFRAME)",
            ),
        },
        "cmd/tip_dlg.cpp": {
            "required": (
                "ModernUI::getPalette",
                "ModernUI::loadIconResource",
                "ModernUI::scale",
                "sPalette.mSurface",
                "sPalette.mSeparator",
                "sPalette.mText",
            ),
            "forbidden": (
                "FillSolidRect(sRect, RGB(255,255,255))",
                "LoadIcon(IDI_TIP)",
            ),
        },
        "picture_viewer.cpp": {
            "required": (
                "ModernUI::getPalette",
                "sPalette.mWindow",
            ),
            "forbidden": (
                "FillSolidRect(sRect, RGB(255,255,255))",
                "FillSolidRect(0, 0, sClientRect.Width(), sClientRect.Height(), RGB(255,255,255))",
            ),
        },
    }

    for rel_path, contract in contracts.items():
        path = FXFILE_SRC / rel_path
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read: {exc}")
            continue

        for token in contract["required"]:
            if token not in source:
                errors.append(f"{path.relative_to(ROOT)}: missing custom-paint token {token}")

        for token in contract["forbidden"]:
            if token in source:
                errors.append(f"{path.relative_to(ROOT)}: legacy custom-paint token returned: {token}")

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


def validate_command_surface_contract() -> list[str]:
    """Keep the Win11-style toolbar/menu/rebar presentation contract intact."""

    errors: list[str] = []
    paths = {
        "toolbar": FXFILE_SRC / "gui" / "rebar" / "ToolBarEx.cpp",
        "menubar": FXFILE_SRC / "gui" / "rebar" / "MenuBar.cpp",
        "rebar_h": FXFILE_SRC / "gui" / "rebar" / "SizableReBar.h",
        "rebar_cpp": FXFILE_SRC / "gui" / "rebar" / "SizableReBar.cpp",
    }

    contents: dict[str, str] = {}
    for name, path in paths.items():
        try:
            contents[name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read command-surface contract: {exc}")

    if errors:
        return errors

    for token in (
        "::FillRect(",
        "sPalette.mSurface",
        "TBCDRF_NOEDGES",
        "TBCDRF_NOOFFSET",
    ):
        if token not in contents["toolbar"]:
            errors.append(f"src/fxfile/gui/rebar/ToolBarEx.cpp: missing flat command-surface token {token}")

    for token in (
        "::FillRect(",
        "sPalette.mSurface",
        "TBCDRF_NOEDGES",
        "TBCDRF_NOOFFSET",
    ):
        if token not in contents["menubar"]:
            errors.append(f"src/fxfile/gui/rebar/MenuBar.cpp: missing flat menu-surface token {token}")

    if "afx_msg BOOL OnEraseBkgnd(CDC *pDC);" not in contents["rebar_h"]:
        errors.append("src/fxfile/gui/rebar/SizableReBar.h: missing modern surface erase hook")

    for token in (
        "ON_WM_ERASEBKGND()",
        "BOOL CSizableReBar::OnEraseBkgnd",
        "if ( WinAppEx::GetInstance()->IsWinXP() )",
        "dwReBarStyle |= RBS_BANDBORDERS | WS_BORDER;",
        "sPalette.mSurface",
    ):
        if token not in contents["rebar_cpp"]:
            errors.append(f"src/fxfile/gui/rebar/SizableReBar.cpp: missing modern rebar token {token}")

    return errors


def validate_configuration_shell_contract() -> list[str]:
    """Protect the modern settings-shell layout and palette hierarchy."""

    errors: list[str] = []
    paths = {
        "rc": FXFILE_SRC / "fxfile.rc",
        "cfg_h": FXFILE_SRC / "cfg" / "cfg_main_dlg.h",
        "cfg_cpp": FXFILE_SRC / "cfg" / "cfg_main_dlg.cpp",
        "cfg_page": FXFILE_SRC / "cfg" / "cfg_dlg.cpp",
        "modern_dialog": FXFILE_SRC / "gui" / "ModernDialog.cpp",
        "main_frame": FXFILE_SRC / "main_frame.cpp",
    }

    contents: dict[str, str] = {}
    for name, path in paths.items():
        try:
            contents[name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read configuration-shell contract: {exc}")

    if errors:
        return errors

    rc = contents["rc"]
    cfg_cpp = contents["cfg_cpp"]

    cfg_start = rc.find("IDD_CFG_MAIN DIALOGEX")
    cfg_end = rc.find("\nEND", cfg_start)
    cfg_resource = rc[cfg_start:cfg_end] if cfg_start >= 0 and cfg_end >= 0 else ""
    for token in (
        "IDD_CFG_MAIN DIALOGEX 0, 0, 430, 328",
        "TVS_FULLROWSELECT",
        "IDC_CFG_DESC,138,8,282,20",
        "IDOK,238,302,58,18",
    ):
        if token not in cfg_resource:
            errors.append(f"src/fxfile/fxfile.rc: modern configuration-shell token missing {token}")

    for legacy_token in ("TVS_HASLINES", "TVS_LINESATROOT", "WS_BORDER | WS_HSCROLL"):
        if legacy_token in cfg_resource:
            errors.append(f"src/fxfile/fxfile.rc: legacy configuration navigation token returned {legacy_token}")

    if "mDarkGrayBrush" in contents["cfg_h"] or "mDarkGrayBrush" in cfg_cpp:
        errors.append("configuration shell: legacy fixed gray breadcrumb brush returned")

    for token in (
        "mHeaderFont",
        "FW_SEMIBOLD",
        "scaleForWindow(28",
        "SetIndent(ui::ModernUI::scaleForWindow(20",
        "sDescRect.bottom + ui::ModernUI::scaleForWindow(10",
        "ON_NOTIFY(NM_CUSTOMDRAW, IDC_CFG_TREE, OnTreeCustomDraw)",
        "void CfgMainDlg::OnTreeCustomDraw",
        "sPalette.mSelection",
        "sPalette.mHover",
    ):
        source = contents["cfg_h"] + cfg_cpp
        if token not in source:
            errors.append(f"configuration shell: missing modern navigation token {token}")

    for source_name in ("cfg_page", "modern_dialog"):
        source = contents[source_name]
        if "if (XPR_IS_FALSE(sPalette.mHighContrast))" not in source:
            errors.append(f"{source_name}: light/dark palette surface contract missing")
        if "if (XPR_IS_TRUE(sPalette.mHighContrast))" not in source:
            errors.append(f"{source_name}: High Contrast native fallback missing")

    for token in ("sPalette.mSeparator", "sPalette.mWindow"):
        if token not in contents["main_frame"]:
            errors.append(f"src/fxfile/main_frame.cpp: missing content hierarchy token {token}")

    return errors


def validate_navigation_surface_contract() -> list[str]:
    """Protect Win11 navigation/address/auxiliary-bar presentation without changing input semantics."""

    errors: list[str] = []
    paths = {
        "modern_h": FXFILE_SRC / "gui" / "ModernUI.h",
        "modern_cpp": FXFILE_SRC / "gui" / "ModernUI.cpp",
        "toolbar": FXFILE_SRC / "gui" / "rebar" / "ToolBarEx.cpp",
        "toolbar_h": FXFILE_SRC / "gui" / "rebar" / "ToolBarEx.h",
        "coolbar": FXFILE_SRC / "main_coolbar.cpp",
        "address_h": FXFILE_SRC / "address_bar.h",
        "address_cpp": FXFILE_SRC / "address_bar.cpp",
        "pane": FXFILE_SRC / "explorer_pane.cpp",
        "drive": FXFILE_SRC / "drive_toolbar.cpp",
        "bookmark": FXFILE_SRC / "bookmark_toolbar.cpp",
    }

    contents: dict[str, str] = {}
    for name, path in paths.items():
        try:
            contents[name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read navigation-surface contract: {exc}")

    if errors:
        return errors

    for token in (
        "getCommandBarHeight",
        "getCommandButtonExtent",
        "getCommandHorizontalPadding",
        "getCommandVerticalPadding",
        "getAddressBarHeight",
        "getAddressHorizontalInset",
        "getAddressVerticalInset",
        "getAddressTextMargin",
        "getPopupItemPadding",
    ):
        if token not in contents["modern_h"] or f"ModernUI::{token}" not in contents["modern_cpp"]:
            errors.append(f"ModernUI navigation metric is missing or unimplemented: {token}")

    for token in (
        "getCommandHorizontalPadding",
        "getCommandVerticalPadding",
        "getCommandButtonExtent",
        "TB_SETBUTTONSIZE",
    ):
        if token not in contents["toolbar"]:
            errors.append(f"src/fxfile/gui/rebar/ToolBarEx.cpp: missing navigation hit-target token {token}")

    if "getCommandBarHeight(theToolBar.GetSafeHwnd())" not in contents["coolbar"]:
        errors.append("src/fxfile/main_coolbar.cpp: coolbar band height is not tied to ModernUI")

    address_contract = contents["address_h"] + contents["address_cpp"]
    for token in (
        "EditSubclassProc",
        "mEditHwnd",
        "mBackgroundBrush",
        "ON_WM_NCPAINT()",
        "void AddressBar::OnNcPaint",
        "EM_SETMARGINS",
        "getAddressTextMargin",
        "SetItemHeight(-1, sFieldItemHeight)",
        "SetItemHeight(0, sDropDownItemHeight)",
        "SHAutoComplete",
        "VK_RETURN",
        "VK_TAB",
        "VK_ESCAPE",
        "::DefSubclassProc",
    ):
        if token not in address_contract:
            errors.append(f"AddressBar navigation/input contract is missing token {token}")

    if "mDarkBackgroundBrush" in address_contract:
        errors.append("AddressBar: dark-only background brush returned; Light/Dark should share ThemePalette")

    for token in (
        "getAddressHorizontalInset",
        "getAddressVerticalInset",
        "sAddressWindowRect.Height()",
        "1000",
    ):
        if token not in contents["pane"]:
            errors.append(f"src/fxfile/explorer_pane.cpp: missing native address layout token {token}")

    for source_name in ("drive", "bookmark"):
        source = contents[source_name]
        if "ApplyModernMetrics();" not in source or "UpdateToolbarSize();" not in source:
            errors.append(f"{source_name}: auxiliary toolbar modern metric refresh is missing")

    popup_contract = contents["toolbar_h"] + contents["toolbar"]
    for token in (
        "afx_msg BOOL OnEraseBkgnd(CDC *pDC);",
        "BOOL CToolBarPopup::OnEraseBkgnd",
        "getPopupItemPadding",
        "sPalette.mSurface",
        "ApplyDarkToolBarCustomDraw(lpNMCustomDraw)",
    ):
        if token not in popup_contract:
            errors.append(f"toolbar chevron popup: missing modern surface token {token}")

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

    def bitmap_geometry(name: str):
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

    def icon_frames(name: str) -> dict[int, int]:
        path = resource_dir / name
        try:
            data = path.read_bytes()
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read: {exc}")
            return {}

        if len(data) < 6 or read_u16(data, 0) != 0 or read_u16(data, 2) != 1:
            errors.append(f"{path.relative_to(ROOT)}: invalid ICO header")
            return {}

        count = read_u16(data, 4)
        frames: dict[int, int] = {}
        for index in range(count):
            entry = 6 + index * 16
            if entry + 16 > len(data):
                errors.append(f"{path.relative_to(ROOT)}: truncated icon directory")
                break

            width = data[entry] or 256
            height = data[entry + 1] or 256
            bpp = read_u16(data, entry + 6)
            if width == height:
                frames[width] = max(frames.get(width, 0), bpp)

        return frames

    dpi_icon_contracts = {
        "tip.ico": (32, 40, 48, 64),
        "shortcut.ico": (32, 40, 48, 64),
        "goup.ico": (16, 32, 40, 48, 64),
    }
    for name, required_sizes in dpi_icon_contracts.items():
        frames = icon_frames(name)
        rel = (resource_dir / name).relative_to(ROOT).as_posix()
        for size in required_sizes:
            if size not in frames:
                errors.append(f"{rel}: missing {size}x{size} DPI frame")
        for size in (40, 48, 64):
            if size in required_sizes and frames.get(size, 0) < 32:
                errors.append(f"{rel}: {size}x{size} DPI frame must be 32-bit")

    try:
        rc = rc_path.read_text(encoding="utf-8", errors="replace")
        gyp = gyp_path.read_text(encoding="utf-8", errors="replace")
        main_toolbar = main_toolbar_path.read_text(encoding="utf-8", errors="replace")
        scrap_toolbar = scrap_toolbar_path.read_text(encoding="utf-8", errors="replace")
        cfg_main = cfg_main_path.read_text(encoding="utf-8", errors="replace")
        explorer_ctrl = (FXFILE_SRC / "explorer_ctrl.cpp").read_text(
            encoding="utf-8", errors="replace"
        )
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
        'IDI_TIP                 ICON                    "res\\\\tip.ico"',
        'IDI_SHORTCUT            ICON                    "res\\\\shortcut.ico"',
        'IDI_GO_UP               ICON                    "res\\\\goup.ico"',
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
        "tip.ico",
        "shortcut.ico",
        "goup.ico",
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

    for token in (
        "ModernUI::loadIconResource",
        "IDI_GO_UP",
        "ModernUI::scaleForWindow",
    ):
        if token not in explorer_ctrl:
            errors.append(f"src/fxfile/explorer_ctrl.cpp: missing DPI go-up icon token {token}")

    if "LoadIcon(IDI_GO_UP)" in explorer_ctrl:
        errors.append("src/fxfile/explorer_ctrl.cpp: legacy fixed-size IDI_GO_UP LoadIcon returned")

    return errors


def validate_functional_test_wiring() -> list[str]:
    """Protect the production seam and native functional-test integration."""

    errors: list[str] = []
    root_gyp_path = ROOT / "fxfile.gyp"
    fxfile_gyp_path = FXFILE_SRC / "fxfile.gyp"
    file_op_thread_path = FXFILE_SRC / "file_op_thread.cpp"
    core_header_path = FXFILE_SRC / "file_operation_core.h"
    core_source_path = FXFILE_SRC / "file_operation_core.cpp"
    test_gyp_path = ROOT / "src" / "fxfile-tests" / "fxfile-tests.gyp"
    test_source_path = ROOT / "src" / "fxfile-tests" / "functional_tests.cpp"
    pattern_path_test_path = ROOT / "src" / "fxfile-tests" / "pattern_path_tests.cpp"
    config_test_path = ROOT / "src" / "fxfile-tests" / "config_persistence_tests.cpp"
    updater_test_path = ROOT / "src" / "fxfile-tests" / "updater_contract_tests.cpp"
    app_ver_path = FXFILE_SRC / "app_ver.cpp"
    upchecker_main_path = ROOT / "src" / "fxfile-upchecker" / "main_window.cpp"
    metadata_path = ROOT / "src" / "fxfile-upchecker" / "meta_data_file.cpp"
    metadata_core_path = ROOT / "src" / "base" / "update_metadata.h"
    upchecker_gyp_path = ROOT / "src" / "fxfile-upchecker" / "fxfile-upchecker.gyp"
    conf_file_path = ROOT / "src" / "base" / "conf_file.cpp"

    paths = (
        root_gyp_path,
        fxfile_gyp_path,
        file_op_thread_path,
        core_header_path,
        core_source_path,
        test_gyp_path,
        test_source_path,
        pattern_path_test_path,
        config_test_path,
        conf_file_path,
        updater_test_path,
        app_ver_path,
        upchecker_main_path,
        metadata_path,
        metadata_core_path,
        upchecker_gyp_path,
    )

    contents: dict[Path, str] = {}
    for path in paths:
        try:
            contents[path] = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read: {exc}")

    if errors:
        return errors

    root_gyp = contents[root_gyp_path]
    fxfile_gyp = contents[fxfile_gyp_path]
    file_op_thread = strip_comments(contents[file_op_thread_path])
    core_source = strip_comments(contents[core_source_path])
    test_gyp = contents[test_gyp_path]
    test_source = contents[test_source_path]
    pattern_path_test = contents[pattern_path_test_path]
    config_test = contents[config_test_path]
    conf_file_source = contents[conf_file_path]
    updater_test = contents[updater_test_path]
    app_ver_source = contents[app_ver_path]
    upchecker_main = contents[upchecker_main_path]
    metadata_source = contents[metadata_path]
    metadata_core = contents[metadata_core_path]
    upchecker_gyp = contents[upchecker_gyp_path]

    if "src/fxfile-tests/fxfile-tests.gyp:*" not in root_gyp:
        errors.append("fxfile.gyp: functional-test target is not in the solution dependency graph")

    for entry in ("./file_operation_core.cpp", "./file_operation_core.h"):
        if entry not in fxfile_gyp:
            errors.append(f"src/fxfile/fxfile.gyp: missing production file-operation seam {entry}")

    for entry in ("./shell_registry_core.cpp", "./shell_registry_core.h"):
        if entry not in fxfile_gyp:
            errors.append(f"src/fxfile/fxfile.gyp: missing shell-registry core {entry}")

    for entry in ("./cmd/rename_transform_core.cpp", "./cmd/rename_transform_core.h"):
        if entry not in fxfile_gyp:
            errors.append(f"src/fxfile/fxfile.gyp: missing rename transform core {entry}")

    if '#include "file_operation_core.h"' not in contents[file_op_thread_path]:
        errors.append("src/fxfile/file_op_thread.cpp: missing direct include for file_operation_core.h")

    if "fileop::execute(mShFileOpStruct);" not in file_op_thread:
        errors.append("src/fxfile/file_op_thread.cpp: production shell operation no longer uses fileop::execute")

    if "::SHFileOperation(mShFileOpStruct)" in file_op_thread:
        errors.append("src/fxfile/file_op_thread.cpp: direct SHFileOperation bypassed the testable production seam")

    rename_production_paths = (
        FXFILE_SRC / "cmd" / "format.h",
        FXFILE_SRC / "cmd" / "format_replace.cpp",
        FXFILE_SRC / "cmd" / "format_insert.cpp",
        FXFILE_SRC / "cmd" / "format_delete.cpp",
        FXFILE_SRC / "cmd" / "format_case.cpp",
        FXFILE_SRC / "cmd" / "format_number.cpp",
    )
    rename_production = ""
    for path in rename_production_paths:
        try:
            rename_production += path.read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read: {exc}")

    for token in (
        "rename_core::splitBaseFileNameAndExt",
        "rename_core::replaceText",
        "rename_core::insertFromLast",
        "rename_core::deleteFromLast",
        "rename_core::toLower",
        "rename_core::appendNumber",
    ):
        if token not in rename_production:
            errors.append(f"rename production wiring is missing token {token}")

    if "return ::SHFileOperation(aOperation);" not in core_source:
        errors.append("src/fxfile/file_operation_core.cpp: production seam no longer delegates to SHFileOperation")

    required_gyp_tokens = (
        "'target_name': 'fxfile-functional-tests'",
        "'../xpr/xpr.gyp:xpr'",
        "'../fxfile-crash/fxfile-crash.gyp:fxfile-crash'",
        "'../fxfile-crash'",
        "'functional_tests.cpp'",
        "'../fxfile/file_operation_core.cpp'",
        "'../fxfile/shell_registry_core.cpp'",
        "'../fxfile/cmd/rename_transform_core.cpp'",
        "'../base/crc32.c'",
        "'../base/md5.c'",
        "'../base/fnmatch.cpp'",
        "'pattern_path_tests.cpp'",
        "'config_persistence_tests.cpp'",
        "'../base/conf_file.cpp'",
        "'updater_contract_tests.cpp'",
        "'../base/version_compare.cpp'",
        "'../base/upchecker_command.cpp'",
        "'../base/update_metadata.h'",
        "'SubSystem': 1",
    )
    for token in required_gyp_tokens:
        if token not in test_gyp:
            errors.append(f"src/fxfile-tests/fxfile-tests.gyp: missing functional-test token {token}")

    required_test_tokens = (
        "xpr::FileSys::mkdir_recursive",
        "xpr::FileSys::rename",
        "xpr::FileSys::remove",
        "xpr::FileIo",
        "FO_COPY",
        "FO_MOVE",
        "FO_DELETE",
        "FOF_RENAMEONCOLLISION",
        "getTempDir",
        "fixture cleanup",
        "testShellRegistryCommandContract",
        "shellreg::buildOpenCommand",
        "shellreg::buildCommandKey",
        "testRenameTransformCore",
        "testPatternAndPathContracts",
        "testConfigPersistenceContracts",
        "testUpdaterContracts",
        "rename_core::splitBaseFileNameAndExt",
        "replaceText(",
        "insertFromLast(",
        "deleteFromLast(",
        "appendNumber(",
        "testHashKnownVectors",
        "CRC32(kVector, 9, sCrc)",
        "MD5(kVector, 9, sMd5)",
    )
    for token in required_test_tokens:
        if token not in test_source:
            errors.append(f"src/fxfile-tests/functional_tests.cpp: missing regression token {token}")

    for token in (
        "fnmatch(",
        "FNM_CASEFOLD",
        "xpr::FilePath",
        "normalize()",
        "getParentDir",
        "getFileName",
        "getExt",
        "isNetwork",
    ):
        if token not in pattern_path_test:
            errors.append(
                f"src/fxfile-tests/pattern_path_tests.cpp: missing path/filter token {token}"
            )

    for token in (
        "base::ConfFileEx",
        "CharSetUtf8",
        "setValueS",
        "setValueI",
        "setValueB",
        "load()",
        "getSectionCount",
        "writeCorruptFile",
    ):
        if token not in config_test:
            errors.append(
                f"src/fxfile-tests/config_persistence_tests.cpp: missing config token {token}"
            )

    for token in (
        "ConfFile::ConfFile(void)\n    : mFlags(0)",
        ", mFlags(0)",
    ):
        if token not in conf_file_source:
            errors.append(
                f"src/base/conf_file.cpp: ConfFile flag initialization regressed near {token}"
            )

    for token in (
        "parseVersion",
        "compareVersion",
        "1, 99, 0",
        "2, 0, 999",
        "2.0.4-beta",
        "buildUpcheckerConfDirArgument",
        "buildUpcheckerStartupCommand",
        "--conf_dir=",
        "parseUpdateMetadataFile",
        "2.0.4-beta",
    ):
        if token not in updater_test:
            errors.append(
                f"src/fxfile-tests/updater_contract_tests.cpp: missing updater token {token}"
            )

    if "base::compareVersion(sCurrent, sRemote)" not in app_ver_source:
        errors.append("src/fxfile/app_ver.cpp: version comparison no longer uses shared version core")

    for token in ("base::parseVersion", "sCheckSucceeded = XPR_FALSE"):
        if token not in upchecker_main:
            errors.append(f"src/fxfile-upchecker/main_window.cpp: missing updater safety token {token}")

    if "base::parseUpdateMetadataFile" not in metadata_source:
        errors.append(
            "src/fxfile-upchecker/meta_data_file.cpp: production metadata parser no longer delegates to shared core"
        )

    for token in (
        "ConfFileEx",
        "kFlagLock",
        "mProgram.empty()",
        "mNewUrl.empty()",
        "parseVersion",
    ):
        if token not in metadata_core:
            errors.append(
                f"src/base/update_metadata.h: missing metadata parser token {token}"
            )

    if "'../base/update_metadata.h'" not in upchecker_gyp:
        errors.append(
            "src/fxfile-upchecker/fxfile-upchecker.gyp: shared update metadata contract is not registered"
        )

    upchecker_manager_path = FXFILE_SRC / "upchecker_manager.cpp"
    command_core_path = ROOT / "src" / "base" / "upchecker_command.cpp"
    try:
        upchecker_manager = upchecker_manager_path.read_text(
            encoding="utf-8", errors="replace"
        )
        command_core = command_core_path.read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError as exc:
        errors.append(f"updater command wiring cannot be read: {exc}")
    else:
        for token in (
            '#include "upchecker_command.h"',
            "base::buildUpcheckerConfDirArgument",
            "base::buildUpcheckerStartupCommand",
        ):
            if token not in upchecker_manager:
                errors.append(
                    f"src/fxfile/upchecker_manager.cpp: missing updater command token {token}"
                )
        if 'XPR_STRING_LITERAL("--conf_dir=\\\"")' not in command_core:
            errors.append(
                "src/base/upchecker_command.cpp: quoted conf-dir argument contract changed"
            )

    return errors


def validate_installer_smoke_wiring() -> list[str]:
    """Protect the non-destructive installer/shell smoke contract."""

    errors: list[str] = []
    setup_path = ROOT / "dist" / "setup.nsi"
    smoke_path = ROOT / "build" / "installer_smoke.ps1"
    local_ci_path = ROOT / "local_ci.bat"

    try:
        setup = setup_path.read_text(encoding="utf-8", errors="replace")
        smoke = smoke_path.read_text(encoding="utf-8", errors="replace")
        local_ci = local_ci_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"installer smoke source cannot be read: {exc}"]

    setup_tokens = (
        '!include                  "FileFunc.nsh"',
        "Var SMOKE_MODE",
        "/FXFILE_SMOKE=",
        'StrCmp $SMOKE_MODE "1" SkipInstallProcessKill',
        'StrCmp $SMOKE_MODE "1" CreateUninstaller',
        'StrCmp $SMOKE_MODE "1" DesktopShortcutDone',
        'StrCmp $SMOKE_MODE "1" QuickLaunchShortcutDone',
        'StrCmp $SMOKE_MODE "1" OnInstSuccessDone',
        'StrCmp $SMOKE_MODE "1" unSkipProcessKill',
        'StrCmp $SMOKE_MODE "1" unSmokeCleanup',
    )
    for token in setup_tokens:
        if token not in setup:
            errors.append(f"dist/setup.nsi: missing isolated installer token {token}")

    smoke_tokens = (
        "[switch]$ExecuteInstall",
        "Installer smoke contract inspection PASS.",
        "FXFILE_INSTALLER_SMOKE=1",
        "Assert-SnapshotUnchanged",
        "/FXFILE_SMOKE=$installDir",
        "/FXFILE_SMOKE=1",
        "runtime_smoke.ps1",
    )
    for token in smoke_tokens:
        if token not in smoke:
            errors.append(f"build/installer_smoke.ps1: missing smoke contract token {token}")

    local_ci_tokens = (
        'if /I "%PROFILE%"=="install" goto :profile_install',
        ":run_installer_smoke",
        'if /I "%FXFILE_INSTALLER_SMOKE%"=="1"',
        '"build\\installer_smoke.ps1"',
    )
    for token in local_ci_tokens:
        if token not in local_ci:
            errors.append(f"local_ci.bat: missing installer-smoke integration token {token}")

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
    errors.extend(validate_theme_mode_contract())
    errors.extend(validate_common_control_theme_integration())
    errors.extend(validate_modern_dialog_migration())
    errors.extend(validate_custom_dialog_paint_regressions())
    errors.extend(validate_toolbar_custom_draw_regression())
    errors.extend(validate_command_surface_contract())
    errors.extend(validate_configuration_shell_contract())
    errors.extend(validate_navigation_surface_contract())
    errors.extend(validate_ui_resource_contracts())
    errors.extend(validate_functional_test_wiring())
    errors.extend(validate_installer_smoke_wiring())
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
