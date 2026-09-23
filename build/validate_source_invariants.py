#!/usr/bin/env python3
"""Fast source-level invariant and regression preflight checks for flyExplorer.

This guard intentionally covers cheap, deterministic invariants and known
regressions that should fail before GYP generation or a Visual Studio build.
It does not replace compilation.
"""

from __future__ import annotations

import json
import re
import subprocess
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


def validate_modern_subclass_forwarding() -> list[str]:
    """Keep ModernUI subclass callbacks forwarding the Win32 message parameters they use."""

    errors: list[str] = []
    contracts = (
        (
            FXFILE_SRC / "cfg" / "cfg_dlg.cpp",
            "ModernGroupBoxSubclassProc",
        ),
        (
            FXFILE_SRC / "cfg" / "cfg_main_dlg.cpp",
            "ModernCfgButtonSubclassProc",
        ),
    )

    for path, proc_name in contracts:
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read subclass forwarding contract: {exc}")
            continue

        signature = (
            f"LRESULT CALLBACK {proc_name}(\n"
            "    HWND aHwnd,\n"
            "    UINT aMessage,\n"
            "    WPARAM aWParam,\n"
            "    LPARAM aLParam,\n"
        )
        if signature not in source:
            errors.append(
                f"{path.relative_to(ROOT)}: {proc_name} must name WPARAM/LPARAM before forwarding them"
            )

        if "return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);" not in source:
            errors.append(
                f"{path.relative_to(ROOT)}: {proc_name} no longer forwards the original message parameters"
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

    for token in (
        "SetWindowTheme",
        "uxtheme.dll",
        'L"Explorer"',
        'sSetWindowTheme(aHwnd, L"", L"")',
    ):
        if token not in modern_ui_source:
            errors.append(f"src/fxfile/gui/ModernUI.cpp: missing control-theme integration token {token}")

    if "sSetWindowTheme(aHwnd, XPR_NULL, XPR_NULL)" in modern_ui_source:
        errors.append(
            "src/fxfile/gui/ModernUI.cpp: resetControlTheme must disable themed painting "
            "with empty strings instead of restoring the default association"
        )

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

        for token in (
            "sPalette.mDark",
            "sPalette.mHighContrast",
            "ModernUI::resetControlTheme",
        ):
            if token not in control_source:
                errors.append(
                    f"{control_path.relative_to(ROOT)}: dark palette-owned theme contract missing {token}"
                )

    list_source = (FXFILE_SRC / "gui" / "ListCtrlEx.cpp").read_text(
        encoding="utf-8", errors="replace"
    )
    if "refreshModernAppearance(XPR_FALSE);" not in list_source:
        errors.append(
            "src/fxfile/gui/ListCtrlEx.cpp: WM_THEMECHANGED must repaint without retheming"
        )

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
        "ApplyDarkToolBarCustomDraw(sCustomDraw)",
        "ApplyDarkToolBarCustomDraw(lpNMCustomDraw, XPR_TRUE)",
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
        "sPalette.mChrome",
        "TBCDRF_NOEDGES",
        "TBCDRF_NOOFFSET",
    ):
        if token not in contents["toolbar"]:
            errors.append(f"src/fxfile/gui/rebar/ToolBarEx.cpp: missing flat command-surface token {token}")

    for token in (
        "::FillRect(",
        "sPalette.mChrome",
        "TBCDRF_NOEDGES",
        "TBCDRF_NOOFFSET",
        "::SetTextColor(nmcd.hdc, sDrawTextColor)",
        "::DrawText(",
        "CDRF_SKIPDEFAULT",
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
        "sPalette.mChrome",
        "resetControlTheme(m_rbCtrl.m_hWnd)",
        "return CControlBar::OnNotify( wParam, lParam, pResult );",
    ):
        if token not in contents["rebar_cpp"]:
            errors.append(f"src/fxfile/gui/rebar/SizableReBar.cpp: missing modern rebar token {token}")

    notify_start = contents["rebar_cpp"].find("BOOL CSizableReBar::OnNotify")
    notify_end = contents["rebar_cpp"].find(
        "\nvoid CSizableReBar::OnUpdateCmdUI",
        notify_start,
    )
    notify_block = (
        contents["rebar_cpp"][notify_start:notify_end]
        if notify_start >= 0 and notify_end > notify_start
        else ""
    )
    if "if ( wParam != 1 )" not in notify_block:
        errors.append(
            "src/fxfile/gui/rebar/SizableReBar.cpp: child-notification routing guard is missing"
        )
    if "return FALSE;" in notify_block:
        errors.append(
            "src/fxfile/gui/rebar/SizableReBar.cpp: child band notifications must not bypass MFC reflection"
        )

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
        "getSettingsNavRowHeight",
        "SetIndent(ui::ModernUI::scaleForWindow(20",
        "getDialogSectionSpacing",
        "getDialogControlHeight",
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


def validate_soft_surface_contract() -> list[str]:
    """Protect the Win11 layered/rounded visual language and accessibility fallback."""

    errors: list[str] = []
    paths = {
        "modern_h": FXFILE_SRC / "gui" / "ModernUI.h",
        "modern_cpp": FXFILE_SRC / "gui" / "ModernUI.cpp",
        "toolbar": FXFILE_SRC / "gui" / "rebar" / "ToolBarEx.cpp",
        "menubar": FXFILE_SRC / "gui" / "rebar" / "MenuBar.cpp",
        "rebar": FXFILE_SRC / "gui" / "rebar" / "SizableReBar.cpp",
        "address": FXFILE_SRC / "address_bar.cpp",
        "cfg_main": FXFILE_SRC / "cfg" / "cfg_main_dlg.cpp",
        "cfg_page": FXFILE_SRC / "cfg" / "cfg_dlg.cpp",
        "modern_dialog": FXFILE_SRC / "gui" / "ModernDialog.cpp",
        "tab": FXFILE_SRC / "gui" / "TabCtrl.cpp",
        "header": FXFILE_SRC / "gui" / "FlatHeaderCtrl.cpp",
        "folder": FXFILE_SRC / "folder_ctrl.cpp",
        "status": FXFILE_SRC / "gui" / "StatusBar.cpp",
    }

    contents: dict[str, str] = {}
    for name, source_path in paths.items():
        try:
            contents[name] = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(
                f"{source_path.relative_to(ROOT)}: cannot read soft-surface contract: {exc}"
            )

    if errors:
        return errors

    palette_fields = (
        "mChrome",
        "mElevated",
        "mCard",
        "mPressed",
        "mInactiveSelection",
        "mFocus",
    )
    for field in palette_fields:
        if field not in contents["modern_h"]:
            errors.append(f"src/fxfile/gui/ModernUI.h: missing layered palette field {field}")
        if f"sPalette.{field}" not in contents["modern_cpp"]:
            errors.append(f"src/fxfile/gui/ModernUI.cpp: layered palette field is not initialized {field}")

    softness_metrics = (
        "getControlCornerRadius",
        "getCardCornerRadius",
        "getPopupCornerRadius",
        "getMenuBarItemHeight",
        "getSettingsNavRowHeight",
        "getSettingsPanelPadding",
        "getDialogControlHeight",
        "getDialogSectionSpacing",
    )
    for metric in softness_metrics:
        if metric not in contents["modern_h"] or f"ModernUI::{metric}" not in contents["modern_cpp"]:
            errors.append(f"ModernUI softness metric is missing or unimplemented: {metric}")

    for token in (
        "applyRoundedWindowRegion",
        "CreateRoundRectRgn",
        "SetWindowRgn",
        "isHighContrast()",
    ):
        if token not in contents["modern_cpp"]:
            errors.append(f"ModernUI rounded-region contract is missing token {token}")

    for source_name, required in {
        "toolbar": (
            "TBCDRF_NOBACKGROUND",
            "DrawRoundedToolbarState",
            "sPalette.mChrome",
            "sPalette.mElevated",
            "sPalette.mPressed",
            "resetControlTheme(m_hWnd)",
        ),
        "menubar": (
            "TBCDRF_NOBACKGROUND",
            "DrawRoundedMenuBarState",
            "getMenuBarItemHeight",
            "sPalette.mChrome",
            "sPalette.mPressed",
        ),
        "rebar": ("sPalette.mChrome",),
        "address": (
            "sPalette.mElevated",
            "PaintFlatAddressEdge",
        ),
        "cfg_main": (
            "ModernCfgButtonSubclassProc",
            "getSettingsNavRowHeight",
            "getDialogControlHeight",
            "getDialogSectionSpacing",
            "getCardCornerRadius",
            "applyRoundedWindowRegion",
            "RefreshCfgTreeImageList",
            "kCfgTreeFluentIcons",
            "FluentCommandIcons::createIcon",
            "ImageList_ReplaceIcon",
            "sPalette.mCard",
            "sPalette.mElevated",
            "sPalette.mInactiveSelection",
        ),
        "cfg_page": (
            "ModernGroupBoxSubclassProc",
            "ModernCfgComboSubclassProc",
            "DrawModernCfgCombo",
            "ModernCfgToggleSubclassProc",
            "DrawModernCfgToggle",
            "IsModernCfgToggleType",
            "ModernCfgPushButtonSubclassProc",
            "DrawModernCfgPushButton",
            "IsModernCfgPushButtonType",
            "ModernCfgEditSubclassProc",
            "DrawModernCfgEditFrame",
            "WM_NCPAINT",
            "RDW_FRAME",
            "WS_EX_TRANSPARENT",
            "HWND_BOTTOM",
            "SnapshotChildWindows",
            "std::vector<HWND> sChildHwnds",
            "SnapshotChildWindows(GetSafeHwnd(), sChildHwnds)",
            "BM_GETCHECK",
            "CBS_DROPDOWNLIST",
            "CB_GETDROPPEDSTATE",
            "resetControlTheme(sComboInfo.hwndList)",
            "resetControlTheme(aWnd->GetSafeHwnd())",
            "SetWindowRgn(GetSafeHwnd(), XPR_NULL, TRUE)",
            "sPalette.mCard",
            "sPalette.mElevated",
            "sPalette.mSeparator",
            "sPalette.mText",
        ),
        "modern_dialog": ("sPalette.mCard", "sPalette.mElevated"),
        "tab": (
            "getControlCornerRadius",
            "sPalette.mChrome",
            "sPalette.mElevated",
            "sPalette.mInactiveSelection",
        ),
        "header": ("sPalette.mChrome", "sPalette.mPressed"),
        "folder": ("sPalette.mCard",),
        "status": ("sPalette.mChrome",),
    }.items():
        source = contents[source_name]
        for token in required:
            if token not in source:
                errors.append(f"{source_name}: missing Win11 soft-surface token {token}")

    for source_name in ("cfg_main", "cfg_page", "modern_dialog"):
        source = contents[source_name]
        if "mHighContrast" not in source:
            errors.append(f"{source_name}: High Contrast fallback token is missing")

    bookmark_path = FXFILE_SRC / "bookmark_wnd.cpp"
    try:
        bookmark_source = bookmark_path.read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError as exc:
        errors.append(
            f"{bookmark_path.relative_to(ROOT)}: cannot read bookmark visual contract: {exc}"
        )
    else:
        for token in (
            "mBookmarkColor == DEF_INFO_BAR_BOOKMARK_COLOR",
            "XPR_IS_TRUE(sPalette.mDark)",
            "sBookmarkTextColor = sPalette.mText",
        ):
            if token not in bookmark_source:
                errors.append(
                    f"src/fxfile/bookmark_wnd.cpp: missing dark bookmark readability token {token}"
                )

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
        "drawModernComboButton",
        "GetComboBoxInfo",
        "STATE_SYSTEM_PRESSED",
        "CB_GETDROPPEDSTATE",
        "TME_LEAVE",
        "sAddressBar->drawModernComboButton(aHwnd);",
        "sOwnDarkChrome",
        "resetControlTheme(m_hWnd)",
        "resetControlTheme(sComboBox->m_hWnd)",
        "resetControlTheme(sEdit->m_hWnd)",
        "resetControlTheme(sComboBoxInfo.hwndList)",
        "::DefSubclassProc",
    ):
        if token not in address_contract:
            errors.append(f"AddressBar navigation/input contract is missing token {token}")

    if "mDarkBackgroundBrush" in address_contract:
        errors.append("AddressBar: dark-only background brush returned; Light/Dark should share ThemePalette")

    for token in ("DarkMode_Explorer", "DarkMode_CFD"):
        if token in address_contract:
            errors.append(
                f"AddressBar: undocumented dark theme association returned: {token}"
            )

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
        "sPalette.mElevated",
        "applyRoundedWindowRegion",
        "ApplyDarkToolBarCustomDraw(lpNMCustomDraw, XPR_TRUE)",
    ):
        if token not in popup_contract:
            errors.append(f"toolbar chevron popup: missing modern surface token {token}")

    return errors


def validate_content_surface_contract() -> list[str]:
    """Protect the Win11 list/tree/tab/pane hierarchy without changing control semantics."""

    errors: list[str] = []
    paths = {
        "modern_h": FXFILE_SRC / "gui" / "ModernUI.h",
        "modern_cpp": FXFILE_SRC / "gui" / "ModernUI.cpp",
        "list_h": FXFILE_SRC / "gui" / "ListCtrlEx.h",
        "list_cpp": FXFILE_SRC / "gui" / "ListCtrlEx.cpp",
        "header": FXFILE_SRC / "gui" / "FlatHeaderCtrl.cpp",
        "folder_h": FXFILE_SRC / "folder_ctrl.h",
        "folder_cpp": FXFILE_SRC / "folder_ctrl.cpp",
        "tab_h": FXFILE_SRC / "gui" / "TabCtrl.h",
        "tab_cpp": FXFILE_SRC / "gui" / "TabCtrl.cpp",
        "view": FXFILE_SRC / "explorer_view.cpp",
        "main_frame": FXFILE_SRC / "main_frame.cpp",
    }

    contents: dict[str, str] = {}
    for name, source_path in paths.items():
        try:
            contents[name] = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(
                f"{source_path.relative_to(ROOT)}: cannot read content-surface contract: {exc}"
            )

    if errors:
        return errors

    metrics = (
        "getContentRowHeight",
        "getTreeRowHeight",
        "getTreeIndent",
        "getListHeaderTextPadding",
        "getTabHeight",
        "getTabHorizontalPadding",
        "getPaneSeparatorThickness",
        "getActivePaneIndicatorThickness",
    )
    for metric in metrics:
        if metric not in contents["modern_h"]:
            errors.append(f"src/fxfile/gui/ModernUI.h: missing content metric {metric}")
        if f"ModernUI::{metric}" not in contents["modern_cpp"]:
            errors.append(f"src/fxfile/gui/ModernUI.cpp: missing content metric implementation {metric}")

    for token in (
        "refreshModernAppearance",
        "ON_WM_SETTINGCHANGE()",
        "ON_WM_SYSCOLORCHANGE()",
        "WM_DPICHANGED",
        "WM_THEMECHANGED",
    ):
        if token not in contents["list_h"] and token not in contents["list_cpp"]:
            errors.append(f"ListCtrlEx: missing content refresh token {token}")

    for token in (
        "ModernUI::applyExplorerControlTheme",
        "mHeaderCtrl->initHeader",
        "mHeaderCtrl->Invalidate",
    ):
        if token not in contents["list_cpp"]:
            errors.append(f"src/fxfile/gui/ListCtrlEx.cpp: missing list refresh token {token}")

    if "getListHeaderTextPadding" not in contents["header"]:
        errors.append("src/fxfile/gui/FlatHeaderCtrl.cpp: shared list-header padding metric is not used")

    activate_bar_source = (FXFILE_SRC / "activate_bar.cpp").read_text(
        encoding="utf-8", errors="replace"
    )
    explorer_view_source = (FXFILE_SRC / "explorer_view.cpp").read_text(
        encoding="utf-8", errors="replace"
    )
    for token in (
        "mBackColor = sPalette.mWindow",
        "mBackColor = sPalette.mSelection",
    ):
        if token not in activate_bar_source:
            errors.append(
                f"src/fxfile/activate_bar.cpp: modern activation stripe removal missing token {token}"
            )
    if "mBackColor = gOpt->mConfig.mActiveViewColor" in activate_bar_source:
        errors.append(
            "src/fxfile/activate_bar.cpp: legacy bright active-pane color must not paint modern Light/Dark surfaces"
        )
    for token in (
        "sActivateBarHeight",
        "sPalette.mHighContrast",
        "sActivateBarHeight =",
        "sRect.top += sActivateBarHeight",
    ):
        if token not in explorer_view_source:
            errors.append(
                f"src/fxfile/explorer_view.cpp: modern active-bar collapse missing token {token}"
            )

    for token in (
        "refreshModernTreeStyle",
        "getTreeRowHeight",
        "getTreeIndent",
        "mClassicThemeStyle",
        "mHighContrast",
        "ModifyStyle(TVS_HASLINES, 0)",
    ):
        if token not in contents["folder_cpp"] and token not in contents["folder_h"]:
            errors.append(f"FolderCtrl: missing modern tree contract token {token}")

    for token in (
        "setPaneActive",
        "mPaneActive",
        "getTabHorizontalPadding",
        "getActivePaneIndicatorThickness",
    ):
        if token not in contents["tab_h"] and token not in contents["tab_cpp"]:
            errors.append(f"TabCtrl: missing pane/tab hierarchy token {token}")

    for token in (
        "getTabHeight",
        "getActivePaneIndicatorThickness",
        "getPaneSeparatorThickness",
        "mTabCtrl->setPaneActive(aActivate)",
    ):
        if token not in contents["view"]:
            errors.append(f"src/fxfile/explorer_view.cpp: missing content hierarchy token {token}")

    if contents["main_frame"].count("getPaneSeparatorThickness") < 2:
        errors.append(
            "src/fxfile/main_frame.cpp: main and single-folder splitters must use shared pane separator metrics"
        )

    return errors


def validate_popup_menu_contract() -> list[str]:
    """Protect the Win11 popup/menu presentation while preserving shell routing."""

    errors: list[str] = []
    paths = {
        "modern_h": FXFILE_SRC / "gui" / "ModernUI.h",
        "modern_cpp": FXFILE_SRC / "gui" / "ModernUI.cpp",
        "bc_menu": FXFILE_SRC / "gui" / "BCMenu.cpp",
        "context_menu": FXFILE_SRC / "context_menu.cpp",
        "toolbar": FXFILE_SRC / "gui" / "rebar" / "ToolBarEx.cpp",
    }

    contents: dict[str, str] = {}
    for name, path in paths.items():
        try:
            contents[name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read popup-menu contract: {exc}")

    if errors:
        return errors

    popup_metrics = (
        "getPopupItemPadding",
        "getPopupItemHeight",
        "getPopupIconGutter",
        "getPopupSeparatorHeight",
        "getPopupSeparatorInset",
        "getPopupShortcutGap",
        "getPopupBorderThickness",
    )
    for token in popup_metrics:
        if token not in contents["modern_h"] or f"ModernUI::{token}" not in contents["modern_cpp"]:
            errors.append(f"ModernUI popup metric is missing or unimplemented: {token}")

    bc_menu = contents["bc_menu"]
    modern_start = bc_menu.find("void BCMenu::DrawItemWindows8Style")
    modern_end = bc_menu.find("\nvoid BCMenu::DrawItem(", modern_start)
    modern_draw = (
        bc_menu[modern_start:modern_end]
        if modern_start >= 0 and modern_end > modern_start
        else ""
    )

    for token in (
        "sPalette.mElevated",
        "sPalette.mHover",
        "sPalette.mSeparator",
        "getControlCornerRadius",
        "RoundRect",
        "DrawItemStandardStyle(aDrawItemStruct)",
        "getPopupIconGutter",
        "getPopupSeparatorInset",
        "getPopupShortcutGap",
        "MFT_RADIOCHECK",
        "drawSubmenuChevron",
        "Segoe Fluent Icons",
        "HasSegoeFluentIcons",
        "0xE970",
        "CPen sPen",
        "DrawState(",
        "DST_ICON | DSS_MONO",
        "sPalette.mSecondaryText",
    ):
        if token not in modern_draw:
            errors.append(f"src/fxfile/gui/BCMenu.cpp: missing modern popup rendering token {token}")

    for legacy_token in ("DrawHorzGradient(", "DrawVertGradient(", "DrawEdge("):
        if legacy_token in modern_draw:
            errors.append(
                f"src/fxfile/gui/BCMenu.cpp: legacy popup rendering returned in default modern path: {legacy_token}"
            )

    for token in (
        "getPopupSeparatorHeight",
        "getPopupItemHeight",
        "getPopupIconGutter",
        "getPopupShortcutGap",
    ):
        if token not in bc_menu:
            errors.append(f"src/fxfile/gui/BCMenu.cpp: popup measurement token missing {token}")

    checkmark_start = bc_menu.find("BOOL BCMenu::Draw3DCheckmark")
    checkmark_end = bc_menu.find("\n}", checkmark_start)
    checkmark_block = (
        bc_menu[checkmark_start:checkmark_end]
        if checkmark_start >= 0 and checkmark_end > checkmark_start
        else ""
    )
    for token in (
        "sPalette.mHighContrast",
        "COLOR_HIGHLIGHTTEXT",
        "sPalette.mSelectionText",
        "sPalette.mText",
        "sMarkColor",
    ):
        if token not in checkmark_block:
            errors.append(
                f"src/fxfile/gui/BCMenu.cpp: palette-aware menu checkmark missing token {token}"
            )

    draw_state_signature = re.compile(
        r"::DrawState\s*\(\s*"
        r"aDC->m_hDC\s*,\s*"
        r"sBrush\s*,\s*"
        r"XPR_NULL\s*,\s*"
        r"reinterpret_cast<LPARAM>\(sIcon\)\s*,\s*"
        r"0\s*,\s*sX\s*,\s*sY\s*,\s*"
        r"m_nIconX\s*,\s*m_nIconY\s*,\s*"
        r"DST_ICON\s*\|\s*DSS_MONO\s*\)"
    )
    if draw_state_signature.search(strip_comments(bc_menu)) is None:
        errors.append(
            "src/fxfile/gui/BCMenu.cpp: popup icon DrawState must use the "
            "10-argument Win32 signature (HDC, HBRUSH, callback, icon, ...)"
        )

    if re.search(
        r"::DrawState\s*\(\s*aDC->m_hDC\s*,\s*XPR_NULL\s*,\s*sBrush",
        strip_comments(bc_menu),
    ):
        errors.append(
            "src/fxfile/gui/BCMenu.cpp: obsolete 11-argument DrawState ordering returned"
        )

    context_menu = contents["context_menu"]
    for token in (
        "IID_IContextMenu3",
        "IID_IContextMenu2",
        "HandleMenuMsg2",
        "HandleMenuMsg",
        "WM_DRAWITEM",
        "WM_MEASUREITEM",
        "::TrackPopupMenuEx",
    ):
        if token not in context_menu:
            errors.append(f"src/fxfile/context_menu.cpp: shell context-menu routing token missing {token}")

    if "BCMenu sMenu" in context_menu:
        errors.append(
            "src/fxfile/context_menu.cpp: shell-owned context menu must not be converted to BCMenu owner-draw"
        )

    toolbar = contents["toolbar"]
    for token in (
        "sLegacyPopup",
        "GetStockObject(NULL_BRUSH)",
        "getPopupItemHeight",
        "getPopupItemPadding",
        "getPopupBorderThickness",
        "BOOL CToolBarPopup::OnEraseBkgnd",
        "ApplyDarkToolBarCustomDraw(lpNMCustomDraw, XPR_TRUE)",
        "applyRoundedWindowRegion",
        "SetBkColor(CLR_NONE)",
    ):
        if token not in toolbar:
            errors.append(f"src/fxfile/gui/rebar/ToolBarEx.cpp: modern popup/artwork token missing {token}")

    for unsupported in ("TB_SETBKCOLOR", "TB_SETTEXTCOLOR"):
        if unsupported in toolbar:
            errors.append(f"src/fxfile/gui/rebar/ToolBarEx.cpp: unsupported toolbar color message returned: {unsupported}")

    return errors


def validate_fluent_asset_contract() -> list[str]:
    """Protect Fluent provenance, generated masks, and runtime frame wiring."""

    errors: list[str] = []
    fluent_dir = FXFILE_SRC / "res" / "fluent"
    license_path = fluent_dir / "LICENSE"
    readme_path = fluent_dir / "README.md"
    mapping_path = fluent_dir / "COMMAND_ICON_MAP.md"
    manifest_path = fluent_dir / "toolbar_manifest.json"
    generator_path = ROOT / "build" / "generate_fluent_toolbar_assets.py"
    gyp_path = FXFILE_SRC / "fxfile.gyp"
    main_toolbar_path = FXFILE_SRC / "main_toolbar.cpp"
    main_toolbar_header_path = FXFILE_SRC / "main_toolbar.h"
    toolbar_cpp_path = FXFILE_SRC / "gui" / "rebar" / "ToolBarEx.cpp"
    toolbar_header_path = FXFILE_SRC / "gui" / "rebar" / "ToolBarEx.h"
    fluent_icon_cpp_path = FXFILE_SRC / "gui" / "FluentCommandIcons.cpp"
    fluent_icon_header_path = FXFILE_SRC / "gui" / "FluentCommandIcons.h"
    bc_menu_path = FXFILE_SRC / "gui" / "BCMenu.cpp"

    generated_assets = (
        "generated_toolbar_masks_small.inc",
        "generated_toolbar_masks_large.inc",
    )

    try:
        license_text = license_path.read_text(encoding="utf-8", errors="replace")
        readme = readme_path.read_text(encoding="utf-8", errors="replace")
        mapping = mapping_path.read_text(encoding="utf-8", errors="replace")
        manifest = manifest_path.read_text(encoding="utf-8", errors="replace")
        generator = generator_path.read_text(encoding="utf-8", errors="replace")
        gyp = gyp_path.read_text(encoding="utf-8", errors="replace")
        main_toolbar = main_toolbar_path.read_text(encoding="utf-8", errors="replace")
        main_toolbar_header = main_toolbar_header_path.read_text(
            encoding="utf-8", errors="replace"
        )
        toolbar_cpp = toolbar_cpp_path.read_text(encoding="utf-8", errors="replace")
        toolbar_header = toolbar_header_path.read_text(
            encoding="utf-8", errors="replace"
        )
        fluent_icon_cpp = fluent_icon_cpp_path.read_text(
            encoding="utf-8", errors="replace"
        )
        fluent_icon_header = fluent_icon_header_path.read_text(
            encoding="utf-8", errors="replace"
        )
        bc_menu = bc_menu_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"Fluent toolbar contract cannot be read: {exc}"]

    try:
        manifest_data = json.loads(manifest)
    except json.JSONDecodeError as exc:
        return [f"src/fxfile/res/fluent/toolbar_manifest.json: invalid JSON: {exc}"]

    manifest_commands = manifest_data.get("commands", [])
    if not isinstance(manifest_commands, list):
        return ["src/fxfile/res/fluent/toolbar_manifest.json: commands must be a list"]

    runtime_assets = sorted(
        {
            item[key]
            for item in manifest_commands
            if isinstance(item, dict)
            for key in ("small_svg", "large_svg")
            if isinstance(item.get(key), str)
        }
    )

    for token in (
        "MIT License",
        "Copyright (c) 2020 Microsoft Corporation",
    ):
        if token not in license_text:
            errors.append(
                f"src/fxfile/res/fluent/LICENSE: missing upstream license token {token}"
            )

    for token in (
        "https://github.com/microsoft/fluentui-system-icons",
        "toolbar_manifest.json",
        "ThemePalette.mText",
        "Do not replace Windows Shell file/folder icons",
        "Do not make normal builds download assets from the network",
        "generated_toolbar_masks_*.inc",
    ):
        if token not in readme:
            errors.append(
                f"src/fxfile/res/fluent/README.md: missing runtime pipeline token {token}"
            )

    for asset_name in runtime_assets:
        asset_path = fluent_dir / asset_name
        try:
            svg = asset_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(
                f"{asset_path.relative_to(ROOT)}: cannot read Fluent SVG: {exc}"
            )
            continue

        # Microsoft Fluent upstream SVGs are not uniform about explicit
        # path fill attributes: many rely on the SVG default black fill while
        # others write fill="#212121". The generator consumes path geometry,
        # so validate structural provenance tokens instead of one paint literal.
        for token in ("<svg ", "viewBox=", "<path "):
            if token not in svg:
                errors.append(
                    f"{asset_path.relative_to(ROOT)}: "
                    f"missing canonical Fluent SVG token {token}"
                )

        gyp_token = f"./res/fluent/{asset_name}"
        if gyp_token not in gyp:
            errors.append(
                f"src/fxfile/fxfile.gyp: missing Fluent source registration {gyp_token}"
            )

    for asset_name in generated_assets:
        asset_path = fluent_dir / asset_name
        if not asset_path.is_file():
            errors.append(f"{asset_path.relative_to(ROOT)}: generated mask is missing")
        if f"./res/fluent/{asset_name}" not in gyp:
            errors.append(
                f"src/fxfile/fxfile.gyp: missing generated Fluent mask {asset_name}"
            )

    for token in (
        "./res/fluent/toolbar_manifest.json",
        "./res/fluent/generated_toolbar_masks_small.inc",
        "./res/fluent/generated_toolbar_masks_large.inc",
    ):
        if token not in gyp:
            errors.append(f"src/fxfile/fxfile.gyp: missing Fluent runtime token {token}")

    for token in (
        '"version": 1',
        '"frame_count": 51',
        '"small": "generated_toolbar_masks_small.inc"',
        '"large": "generated_toolbar_masks_large.inc"',
        '"frame": 0',
        '"frame": 43',
    ):
        if token not in manifest:
            errors.append(
                f"src/fxfile/res/fluent/toolbar_manifest.json: missing token {token}"
            )

    if len(manifest_commands) != 23:
        errors.append(
            "src/fxfile/res/fluent/toolbar_manifest.json: "
            f"expected 23 runtime Fluent commands, found {len(manifest_commands)}"
        )

    default_visible_commands = (
        "ID_GO_BACK",
        "ID_GO_FORWARD",
        "ID_GO_UP",
        "ID_VIEW_FOLDER_TREE_SHOW",
        "ID_TOOL_FILE_SEARCH",
        "ID_GO_BOOKMARK",
        "ID_GO_DRIVE",
        "ID_GO_WORKING_FOLDER",
        "ID_EDIT_CUT",
        "ID_EDIT_COPY",
        "ID_EDIT_PASTE",
        "ID_FILE_RENAME",
        "ID_FILE_DELETE",
        "ID_EDIT_UNDO",
        "ID_FILE_PROPERTY",
        "ID_VIEW_STYLE",
        "ID_WINDOW_SPLIT",
        "ID_FILE_NEW_FOLDER",
        "ID_TOOL_CMD",
        "ID_TOOL_EMPTY_RECYCLEBIN",
        "ID_APP_ABOUT",
    )
    manifest_command_names = {
        item.get("command")
        for item in manifest_commands
        if isinstance(item, dict)
    }
    for command in default_visible_commands:
        if command not in manifest_command_names:
            errors.append(
                "src/fxfile/res/fluent/toolbar_manifest.json: "
                f"default-visible toolbar command is not Fluent-mapped: {command}"
            )

    for token in (
        "_SUPPORTED_COMMANDS = frozenset(\"MLHVCZ\")",
        "_CUBIC_STEPS = 32",
        "_SUPERSAMPLE = 4",
        "toolbar frame_count must remain 51",
        "duplicate frame index",
        "duplicate command",
        "--check",
        "--write",
    ):
        if token not in generator:
            errors.append(
                f"build/generate_fluent_toolbar_assets.py: missing deterministic token {token}"
            )
    for forbidden in ("import requests", "import urllib", "http://", "https://"):
        if forbidden in generator:
            errors.append(
                "build/generate_fluent_toolbar_assets.py: "
                f"network dependency is forbidden ({forbidden})"
            )

    mapping_lines = mapping.splitlines()
    for item in manifest_commands:
        if not isinstance(item, dict):
            errors.append("src/fxfile/res/fluent/toolbar_manifest.json: invalid command entry")
            continue
        frame = item.get("frame")
        command = item.get("command")
        expected_tokens = (
            f"| {frame} |",
            str(command),
            "runtime Fluent mask",
        )
        if not any(
            all(token in line for token in expected_tokens)
            for line in mapping_lines
        ):
            errors.append(
                "src/fxfile/res/fluent/COMMAND_ICON_MAP.md: "
                f"missing runtime mapping {frame}/{command}"
            )

    for token in (
        "Preserve the existing command IDs and image indexes",
        "Do not replace Shell-owned file/folder icons",
        "No network download is allowed during normal builds",
    ):
        if token not in mapping:
            errors.append(
                f"src/fxfile/res/fluent/COMMAND_ICON_MAP.md: "
                f"missing migration rule {token}"
            )

    for token in (
        '#include "gui/ModernUI.h"',
        '#include "gui/FluentCommandIcons.h"',
        "kFluentToolbarFrames[] =",
        "ui::FluentCommandIcons::createIcon",
        "m_imageListCold",
        "m_imageListHot",
        "sPalette.mText",
    ):
        if token not in main_toolbar:
            errors.append(f"src/fxfile/main_toolbar.cpp: missing Fluent runtime token {token}")

    for item in manifest_commands:
        if not isinstance(item, dict):
            continue
        frame = item.get("frame")
        command = item.get("command")
        frame_token = f"{{ {int(frame):2d}, {command} }}" if isinstance(frame, int) else ""
        compact_token = f"{{ {frame}, {command} }}"
        if frame_token not in main_toolbar and compact_token not in main_toolbar:
            errors.append(
                "src/fxfile/main_toolbar.cpp: "
                f"missing Fluent frame wiring {frame}/{command}"
            )
        if str(command) not in fluent_icon_cpp:
            errors.append(
                "src/fxfile/gui/FluentCommandIcons.cpp: "
                f"missing command registry entry {command}"
            )

    for token in (
        "generated_toolbar_masks_small.inc",
        "generated_toolbar_masks_large.inc",
        "FluentCommandIcons::hasCommand",
        "FluentCommandIcons::createIcon",
        "kCommandIds[]",
    ):
        if token not in fluent_icon_cpp:
            errors.append(
                f"src/fxfile/gui/FluentCommandIcons.cpp: missing shared icon token {token}"
            )

    for token in (
        "class FluentCommandIcons",
        "static xpr_bool_t hasCommand",
        "static HICON createIcon",
    ):
        if token not in fluent_icon_header:
            errors.append(
                f"src/fxfile/gui/FluentCommandIcons.h: missing shared icon contract {token}"
            )

    for token in (
        "FluentCommandIcons::hasCommand",
        "FluentCommandIcons::createIcon",
        "drawIcon(sDC, sItemRect, sItemState, sMenuItemId, XPR_NULL)",
    ):
        if token not in bc_menu:
            errors.append(
                f"src/fxfile/gui/BCMenu.cpp: missing Fluent menu icon preference {token}"
            )

    for token in (
        "./gui/FluentCommandIcons.cpp",
        "./gui/FluentCommandIcons.h",
    ):
        if token not in gyp:
            errors.append(f"src/fxfile/fxfile.gyp: missing shared Fluent icon source {token}")

    if "virtual void OnImageListsReloaded();" not in main_toolbar_header:
        errors.append(
            "src/fxfile/main_toolbar.h: MainToolBar image-list reload hook is missing"
        )

    for token in (
        "virtual void OnImageListsReloaded();",
    ):
        if token not in toolbar_header:
            errors.append(f"ToolBarEx.h: missing toolbar artwork hook {token}")

    for token in (
        "void CToolBarEx::OnImageListsReloaded()",
        "OnImageListsReloaded();",
        "SetIconType(m_nIconType, false);",
        "m_nIDSmallCold = (UINT)-1;",
        "m_nIDLargeCold = (UINT)-1;",
    ):
        if token not in toolbar_cpp:
            errors.append(f"ToolBarEx.cpp: missing toolbar artwork refresh token {token}")

    if fluent_dir.exists():
        for asset in fluent_dir.iterdir():
            if asset.suffix.lower() in (".ttf", ".otf", ".woff", ".woff2"):
                errors.append(
                    f"{asset.relative_to(ROOT)}: system/font binary must not be vendored "
                    "for Fluent glyph rendering"
                )

    try:
        result = subprocess.run(
            [sys.executable, str(generator_path), "--check"],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError as exc:
        errors.append(f"Fluent toolbar generator could not run: {exc}")
    else:
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            errors.append(
                "Fluent toolbar generated masks are stale or invalid"
                + (f": {detail}" if detail else "")
            )

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

        pixel_offset = read_u32(data, 10)
        dib_size = read_u32(data, 14)
        width = int.from_bytes(data[18:22], "little", signed=True)
        height = int.from_bytes(data[22:26], "little", signed=True)
        planes = read_u16(data, 26)
        bpp = read_u16(data, 28)
        compression = read_u32(data, 30)
        return width, abs(height), bpp, planes, compression, pixel_offset, dib_size, data

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

        width, height, bpp, planes, compression, pixel_offset, dib_size, data = geometry
        rel = (resource_dir / name).relative_to(ROOT).as_posix()
        if bpp != 16:
            errors.append(f"{rel}: expected legacy mask-strip 16bpp contract, got {bpp}bpp")
        if planes != 1 or compression != 0:
            errors.append(
                f"{rel}: expected BI_RGB/1-plane bitmap contract, "
                f"got planes={planes}, compression={compression}"
            )
        if pixel_offset != 54 or dib_size != 40:
            errors.append(
                f"{rel}: BMP header layout changed; expected 54-byte pixel offset "
                f"and 40-byte BITMAPINFOHEADER"
            )

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

        # RGB(255,0,255) is 0x7C1F in the 5-5-5 BI_RGB pixels used by the
        # legacy ImageList_LoadImage mask contract. Require at least one mask
        # pixel so a future artwork replacement cannot silently become opaque.
        mask_word = b"\x1f\x7c"
        if mask_word not in data[pixel_offset:]:
            errors.append(f"{rel}: RGB(255,0,255) transparent-mask pixels are missing")

    modern_toolbar_frames = (
        0, 1, 2, 3, 5, 7, 8, 10, 11, 12, 13, 14,
        18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29, 30,
        31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
        43, 44, 45, 46, 47, 48, 49, 50,
    )
    toolbar_strip_names = (
        "tb_main_cold_small.bmp",
        "tb_main_hot_small.bmp",
        "tb_main_cold_large.bmp",
        "tb_main_hot_large.bmp",
    )
    toolbar_strip_pixels: dict[str, tuple[set[tuple[int, int]], set[int]]] = {}

    for name in toolbar_strip_names:
        geometry = bitmap_geometry(name)
        if geometry is None:
            continue

        width, height, bpp, planes, compression, pixel_offset, dib_size, data = geometry
        cell_width = height
        stride = ((width * 2 + 3) // 4) * 4
        mask_value = 0x7C1F
        occupied: set[tuple[int, int]] = set()
        ink_values: set[int] = set()

        for frame in modern_toolbar_frames:
            colors: set[int] = set()
            min_x = cell_width
            min_y = height
            max_x = -1
            max_y = -1

            for y in range(height):
                source_row = height - 1 - y
                for x in range(cell_width):
                    pixel = (
                        pixel_offset
                        + source_row * stride
                        + (frame * cell_width + x) * 2
                    )
                    value = read_u16(data, pixel)
                    colors.add(value)
                    if value != mask_value:
                        occupied.add((frame, y * cell_width + x))
                        ink_values.add(value)
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)

            rel = (resource_dir / name).relative_to(ROOT).as_posix()
            if len(colors) != 2 or mask_value not in colors:
                errors.append(
                    f"{rel}: modern frame {frame} must contain exactly "
                    "transparent mask + one flat glyph color"
                )
            if max_x < min_x or max_y < min_y:
                errors.append(f"{rel}: modern frame {frame} is unexpectedly blank")
            else:
                margin = min(
                    min_x,
                    min_y,
                    cell_width - 1 - max_x,
                    height - 1 - max_y,
                )
                if margin < 1:
                    errors.append(
                        f"{rel}: modern frame {frame} touches the bitmap cell edge"
                    )

        toolbar_strip_pixels[name] = (occupied, ink_values)

    for size in ("small", "large"):
        cold_name = f"tb_main_cold_{size}.bmp"
        hot_name = f"tb_main_hot_{size}.bmp"
        if cold_name not in toolbar_strip_pixels or hot_name not in toolbar_strip_pixels:
            continue

        cold_shape, cold_inks = toolbar_strip_pixels[cold_name]
        hot_shape, hot_inks = toolbar_strip_pixels[hot_name]
        if cold_shape != hot_shape:
            errors.append(
                f"toolbar {size}: COLD/HOT glyph geometry diverged; "
                "state changes must not move command artwork"
            )
        if cold_inks == hot_inks:
            errors.append(
                f"toolbar {size}: COLD/HOT glyph colors are identical; "
                "hover state must remain visually distinct"
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
        "(UINT)-1, IDB_TB_MAIN_COLD_SMALL, IDB_TB_MAIN_HOT_SMALL",
        "(UINT)-1, IDB_TB_MAIN_COLD_LARGE, IDB_TB_MAIN_HOT_LARGE",
    )

    for source_name, source in (
        ("src/fxfile/main_toolbar.cpp", main_toolbar),
        ("src/fxfile/file_scrap_toolbar.cpp", scrap_toolbar),
    ):
        if "const COLORREF IL_COLOR_MASK = RGB(255,0,255);" not in source:
            errors.append(f"{source_name}: toolbar RGB(255,0,255) mask contract changed")
    for source_name, source in (
        ("src/fxfile/main_toolbar.cpp", main_toolbar),
        ("src/fxfile/file_scrap_toolbar.cpp", scrap_toolbar),
    ):
        for token in toolbar_contract:
            if token not in source:
                errors.append(f"{source_name}: toolbar image mapping changed near {token}")

    expected_main_toolbar_frames = (
        (0, "ID_GO_BACK"),
        (1, "ID_GO_FORWARD"),
        (2, "ID_GO_UP"),
        (3, "ID_GO_HISTORY"),
        (0, "0"),
        (7, "ID_VIEW_FOLDER_TREE_SHOW"),
        (8, "ID_TOOL_FILE_SEARCH"),
        (0, "0"),
        (10, "ID_GO_BOOKMARK"),
        (11, "ID_GO_DRIVE"),
        (43, "ID_GO_WORKING_FOLDER"),
        (44, "ID_GO_WORKING_FOLDER_0"),
        (45, "ID_GO_WORKING_FOLDER_1"),
        (46, "ID_GO_WORKING_FOLDER_2"),
        (47, "ID_GO_WORKING_FOLDER_3"),
        (48, "ID_GO_WORKING_FOLDER_4"),
        (0, "0"),
        (12, "ID_EDIT_CUT"),
        (13, "ID_EDIT_COPY"),
        (14, "ID_EDIT_PASTE"),
        (34, "ID_EDIT_FOLDER_MOVE"),
        (35, "ID_EDIT_FOLDER_COPY"),
        (0, "0"),
        (18, "ID_FILE_RENAME"),
        (19, "ID_FILE_DELETE"),
        (29, "ID_EDIT_UNDO"),
        (33, "ID_FILE_ATTRTIME"),
        (20, "ID_FILE_PROPERTY"),
        (0, "0"),
        (26, "ID_VIEW_STYLE"),
        (21, "ID_WINDOW_SPLIT"),
        (22, "ID_WINDOW_SPLIT_SINGLE"),
        (23, "ID_WINDOW_SPLIT_1x2"),
        (24, "ID_WINDOW_SPLIT_2x1"),
        (39, "ID_WINDOW_SPLIT_EQUAL"),
        (40, "ID_WINDOW_SPLIT_SWAP"),
        (0, "0"),
        (37, "ID_FILE_NEW_FOLDER"),
        (30, "ID_EDIT_FILE_SCRAP_VIEW"),
        (31, "ID_TOOL_CMD"),
        (27, "ID_TOOL_EMPTY_RECYCLEBIN"),
        (32, "ID_FILE_PRINT"),
        (36, "ID_VIEW_PICVIEWER"),
        (41, "ID_FILE_VIEW"),
        (42, "ID_FILE_EDIT"),
        (0, "0"),
        (38, "ID_TOOL_OPTION"),
        (28, "ID_APP_ABOUT"),
    )
    toolbar_block_match = re.search(
        r"TBBUTTONEX\s+kTbButtons\[\]\s*=\s*\{(?P<body>.*?)\n\};",
        main_toolbar,
        re.DOTALL,
    )
    if toolbar_block_match is None:
        errors.append("src/fxfile/main_toolbar.cpp: kTbButtons table not found")
    else:
        actual_main_toolbar_frames = tuple(
            (int(frame), command)
            for frame, command in re.findall(
                r"\{\s*\{\s*(\d+)\s*,\s*(ID_[A-Za-z0-9_]+|0)\s*,",
                toolbar_block_match.group("body"),
            )
        )
        if actual_main_toolbar_frames != expected_main_toolbar_frames:
            errors.append(
                "src/fxfile/main_toolbar.cpp: toolbar frame/command order changed; "
                "update artwork and invariant together only after reviewing the bitmap-frame contract"
            )

    expected_scrap_toolbar_frames = (
        (30, "ID_EDIT_FILE_SCRAP_GROUP_ADD"),
        (0, "0"),
        (35, "ID_EDIT_FILE_SCRAP_COPY_TO"),
        (34, "ID_EDIT_FILE_SCRAP_MOVE_TO"),
        (19, "ID_EDIT_FILE_SCRAP_DELETE"),
        (0, "0"),
        (5, "ID_EDIT_FILE_SCRAP_REFRESH"),
        (0, "0"),
        (50, "ID_EDIT_FILE_SCRAP_VALIDATE"),
        (49, "ID_EDIT_FILE_SCRAP_REMOVE_LIST"),
        (49, "ID_EDIT_FILE_SCRAP_REMOVE_ALL_LIST"),
    )
    scrap_toolbar_block_match = re.search(
        r"TBBUTTONEX\s+kTbButtons\[\]\s*=\s*\{(?P<body>.*?)\n\};",
        scrap_toolbar,
        re.DOTALL,
    )
    if scrap_toolbar_block_match is None:
        errors.append("src/fxfile/file_scrap_toolbar.cpp: kTbButtons table not found")
    else:
        actual_scrap_toolbar_frames = tuple(
            (int(frame), command)
            for frame, command in re.findall(
                r"\{\s*\{\s*(\d+)\s*,\s*(ID_[A-Za-z0-9_]+|0)\s*,",
                scrap_toolbar_block_match.group("body"),
            )
        )
        if actual_scrap_toolbar_frames != expected_scrap_toolbar_frames:
            errors.append(
                "src/fxfile/file_scrap_toolbar.cpp: toolbar frame/command order changed"
            )

    for token in (
        "RefreshCfgTreeImageList",
        "sBitmap.LoadBitmap(IDB_CONFIG_TREE)",
        "aImageList.Create(16, 16",
        "kCfgTreeFluentIcons",
        "FluentCommandIcons::createIcon",
        "ImageList_ReplaceIcon",
        "mTreeCtrl.SetImageList(&mImgList, TVSIL_NORMAL)",
    ):
        if token not in cfg_main:
            errors.append(
                "src/fxfile/cfg/cfg_main_dlg.cpp: "
                f"config-tree base/Fluent overlay contract missing {token}"
            )

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
        "xpr::initialize()",
        "xpr::finalize()",
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


def validate_local_ci_warning_policy_wiring() -> list[str]:
    """Protect local-CI diagnostics, output-lock preflight, and staging semantics."""

    errors: list[str] = []
    local_ci_path = ROOT / "local_ci.bat"
    lock_check_path = ROOT / "build" / "check_build_output_locks.ps1"
    copy_lib_path = ROOT / "copy_lib.bat"
    copy_languages_path = ROOT / "copy_languages.bat"

    try:
        local_ci = local_ci_path.read_text(encoding="utf-8", errors="replace")
        lock_check = lock_check_path.read_text(encoding="utf-8", errors="replace")
        copy_lib = copy_lib_path.read_text(encoding="utf-8", errors="replace")
        copy_languages = copy_languages_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"local CI/build staging source cannot be read: {exc}"]

    required_tokens = (
        '"/consoleloggerparameters:NoSummary"',
        '"/flp1:logfile=%MSBUILD_ERROR_LOG%;errorsonly"',
        '"/flp2:logfile=%MSBUILD_RAW_LOG%;verbosity=normal"',
        "'ERROR: warning policy violation: ' + $_.Trim()",
        "[System.IO.File]::WriteAllLines($env:MSBUILD_ERROR_LOG, $warnings, $utf8)",
    )
    for token in required_tokens:
        if token not in local_ci:
            errors.append(f"local_ci.bat: missing warning-policy logging token {token}")

    if "$lines ^| Where-Object" in local_ci or "} ^| ForEach-Object" in local_ci:
        errors.append(
            "local_ci.bat: PowerShell warning extractor contains cmd caret-escaped pipes "
            "inside a quoted -Command; use raw '|' so diagnostics can be extracted"
        )

    if "$lines | Where-Object" not in local_ci or "} | ForEach-Object" not in local_ci:
        errors.append(
            "local_ci.bat: warning-policy diagnostic pipeline is not wired with PowerShell pipes"
        )

    build_start = local_ci.find(":build_configuration")
    build_end = local_ci.find("\n:require_file", build_start)
    build_section = (
        local_ci[build_start:build_end]
        if build_start >= 0 and build_end > build_start
        else ""
    )
    lock_call = '-File "build\\check_build_output_locks.ps1" -Configuration "%CI_CONFIGURATION%"'
    msbuild_call = '"%MSBUILD_EXE%" "%CI_PROJECT%"'
    for token in (lock_call, "OUTPUT_LOCK_RESULT", "Build output lock preflight: %CI_TITLE%"):
        if token not in build_section:
            errors.append(f"local_ci.bat: missing build-output lock preflight token {token}")
    if lock_call in build_section and msbuild_call in build_section:
        if build_section.find(lock_call) > build_section.find(msbuild_call):
            errors.append("local_ci.bat: output-lock preflight must run before MSBuild Rebuild")

    for token in (
        "[System.IO.FileShare]::None",
        "libxprw.dll",
        "fxfile-crash.dll",
        "Local CI will not terminate user processes automatically.",
        "exit 2",
    ):
        if token not in lock_check:
            errors.append(
                f"build/check_build_output_locks.ps1: missing lock-contract token {token}"
            )

    for source_name, source in (
        ("copy_lib.bat", copy_lib),
        ("copy_languages.bat", copy_languages),
    ):
        for token in (
            'call :copy_newer',
            'if not exist "%~1"',
            '/d /e /r /y /i',
            'if errorlevel 2',
        ):
            if token not in source:
                errors.append(f"{source_name}: missing idempotent staging token {token}")
        if " /c " in source.lower():
            errors.append(
                f"{source_name}: xcopy /c returned; required staging copy failures must not be ignored"
            )

    return errors


def validate_active_ci_scope_documentation() -> list[str]:
    """Keep active CI guidance aligned with the user-selected Release x64 scope."""

    errors: list[str] = []
    paths = {
        "agents": ROOT / "AGENTS.md",
        "project": ROOT / ".agent-policy" / "PROJECT.md",
        "readme": ROOT / "README",
        "manual": ROOT / "LOCAL_CI_MANUAL.txt",
        "local_ci": ROOT / "local_ci.bat",
        "workflow": ROOT / ".github" / "workflows" / "windows-build.yml",
    }

    contents: dict[str, str] = {}
    for name, path in paths.items():
        try:
            contents[name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: cannot read active CI scope contract: {exc}")

    if errors:
        return errors

    required = {
        "agents": (
            "현재 개발/CI의 단일 build command는 `local_ci.bat x64`",
            "`Release-x64-Unicode | x64`만 Rebuild",
            "`run_x86_compat`는 현재 정책상 켜지 않는다",
        ),
        "project": (
            "현재 활성 CI build 범위는 `Release-x64-Unicode | x64` 하나뿐이다",
            "기본 검증은 `local_ci.bat x64`만 실행한다",
            "`local_ci.bat full` 및 Actions `run_x86_compat`는 현재 비활성 범위",
        ),
        "readme": (
            "Release-x64-Unicode | x64\nonly",
            "Do not run them for normal development unless the user",
            "Debug-x64, x86 Unicode/Multibyte, `release`, `full`",
        ),
        "manual": (
            "Release-x64-Unicode | x64 한정입니다.",
            ".\\local_ci.bat x64",
            "사용자가 검증 범위를 다시 넓히라고 명시하기 전에는 실행하지 않습니다.",
        ),
        "local_ci": (
            "Active project CI scope (2026-09-23): Release-x64-Unicode | x64 only.",
            'if /I "%PROFILE%"=="x64" goto :profile_x64',
            'call :run_x64_release',
            'call :build_configuration "Release-x64-Unicode" "x64" "Release x64"',
        ),
        "workflow": (
            "Active project CI scope (2026-09-23) is Release-x64-Unicode | x64 only.",
            "INACTIVE by current policy; enable only after explicit user scope expansion",
            "jobs:\n  release-x64:",
        ),
    }

    for name, tokens in required.items():
        source = contents[name]
        for token in tokens:
            if token not in source:
                errors.append(
                    f"{paths[name].relative_to(ROOT)}: missing active CI scope token {token}"
                )

    local_ci = contents["local_ci"]
    profile_start = local_ci.find(":profile_x64")
    profile_end = local_ci.find("\n:profile_x86", profile_start)
    profile_x64 = (
        local_ci[profile_start:profile_end]
        if profile_start >= 0 and profile_end > profile_start
        else ""
    )
    if not profile_x64:
        errors.append("local_ci.bat: x64 profile block cannot be located")
    else:
        if "call :run_x64_release" not in profile_x64:
            errors.append("local_ci.bat: active x64 profile no longer calls Release x64")
        for forbidden in ("run_x64_debug", "run_x86_release", "run_package_validation"):
            if forbidden in profile_x64:
                errors.append(
                    f"local_ci.bat: active x64 profile unexpectedly expands CI scope via {forbidden}"
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
        'StrCmp $SMOKE_MODE "1" unSkipProcessKill',
        'StrCmp $SMOKE_MODE "1" unSmokeCleanup',
    )
    for token in setup_tokens:
        if token not in setup:
            errors.append(f"dist/setup.nsi: missing isolated installer token {token}")

    for token in (
        "!define MUI_FINISHPAGE_RUN",
        "Function .onInstSuccess",
        'ExecShell "" "$INSTDIR\\fxfile-launcher.exe"',
    ):
        if token in setup:
            errors.append(
                "dist/setup.nsi: elevated installer must not auto-launch "
                f"fxfile/launcher via {token}"
            )

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



def validate_win11_stability_regressions() -> list[str]:
    """Protect the Win11 startup/settings stability and readability fixes."""

    errors: list[str] = []
    paths = {
        "manifest": FXFILE_SRC / "res" / "fxfile.exe.manifest",
        "modern_ui": FXFILE_SRC / "gui" / "ModernUI.cpp",
        "bookmark_set": FXFILE_SRC / "bookmark_set_wnd.cpp",
        "address": FXFILE_SRC / "address_bar.cpp",
        "main_toolbar": FXFILE_SRC / "main_toolbar.cpp",
        "menubar": FXFILE_SRC / "gui" / "rebar" / "MenuBar.cpp",
        "contents": FXFILE_SRC / "contents_wnd.cpp",
        "conf_dir": FXFILE_SRC / "conf_dir.cpp",
        "toolbar_cpp": FXFILE_SRC / "gui" / "rebar" / "ToolBarEx.cpp",
        "cfg_main_h": FXFILE_SRC / "cfg" / "cfg_main_dlg.h",
        "cfg_main_cpp": FXFILE_SRC / "cfg" / "cfg_main_dlg.cpp",
        "cfg_page_h": FXFILE_SRC / "cfg" / "cfg_dlg.h",
        "cfg_page_cpp": FXFILE_SRC / "cfg" / "cfg_dlg.cpp",
        "modern_dialog": FXFILE_SRC / "gui" / "ModernDialog.cpp",
        "resizing_dialog": FXFILE_SRC / "gui" / "ResizingDialog.cpp",
        "title_dialog": FXFILE_SRC / "cmd" / "title_dlg.cpp",
        "shell_registry": FXFILE_SRC / "shell_registry.cpp",
        "single_process": FXFILE_SRC / "single_process.cpp",
        "main_coolbar": FXFILE_SRC / "main_coolbar.cpp",
        "main_frame": FXFILE_SRC / "main_frame.cpp",
        "file_scrap": FXFILE_SRC / "file_scrap_pane.cpp",
        "bookmark_wnd": FXFILE_SRC / "bookmark_wnd.cpp",
        "search_loc": FXFILE_SRC / "cmd" / "search_loc_dlg.cpp",
        "drop_menu_button_h": FXFILE_SRC / "gui" / "DropMenuButton.h",
        "drop_menu_button_cpp": FXFILE_SRC / "gui" / "DropMenuButton.cpp",
        "button_st_h": FXFILE_SRC / "gui" / "BtnST.h",
        "button_st_cpp": FXFILE_SRC / "gui" / "BtnST.cpp",
        "colour_picker": FXFILE_SRC / "gui" / "ColourPickerXP.cpp",
        "explorer_ctrl": FXFILE_SRC / "explorer_ctrl.cpp",
        "cfg_filter": FXFILE_SRC / "cfg" / "cfg_appearance_filtering_dlg.cpp",
        "cfg_filter_h": FXFILE_SRC / "cfg" / "cfg_appearance_filtering_dlg.h",
        "header": FXFILE_SRC / "gui" / "FlatHeaderCtrl.cpp",
    }

    class ContractContents(dict[str, str]):
        def __missing__(self, key: str) -> str:
            errors.append(
                "validate_win11_stability_regressions: "
                f"missing source registration for contents[{key!r}]"
            )
            return ""

    contents: ContractContents = ContractContents()
    for name, path in paths.items():
        try:
            contents[name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(
                f"{path.relative_to(ROOT)}: cannot read Win11 stability contract: {exc}"
            )

    if errors:
        return errors

    manifest = contents["manifest"]
    if '<requestedExecutionLevel level="asInvoker" uiAccess="false"/>' not in manifest:
        errors.append(
            "src/fxfile/res/fxfile.exe.manifest: requestedExecutionLevel must remain asInvoker"
        )

    conf_dir = contents["conf_dir"]
    for token in (
        'XPR_STRING_LITERAL("%AppData%\\\\fxfile\\\\")CFG_PATH_FILENAME',
        'XPR_STRING_LITERAL("%AppData%\\\\fxfile\\\\conf")',
    ):
        if token not in conf_dir:
            errors.append(
                "src/fxfile/conf_dir.cpp: default writable configuration must remain under per-user AppData"
            )

    for token in (
        "IsWritableConfDir",
        "CreateFile(",
        "CreateDirectoryLevel(sConfiguredDir)",
        "IsWritableConfDir(sConfiguredDir)",
        "IsWritableConfDir(sDefaultDir)",
        "sPersistedConfHome",
        "save();",
    ):
        if token not in conf_dir:
            errors.append(
                f"src/fxfile/conf_dir.cpp: missing standard-user config fallback token {token}"
            )

    main_frame = contents["main_frame"]
    for token in (
        'XPR_STRING_LITERAL("\\\\accel.fac")',
        "ConfDir::instance().getSavePath(",
        "::CopyFile(sOldPath, sSavePath, TRUE)",
    ):
        if token not in main_frame:
            errors.append(
                f"src/fxfile/main_frame.cpp: missing standard-user accel migration token {token}"
            )
    accel_pos = main_frame.find('XPR_STRING_LITERAL("\\\\accel.fac")')
    if accel_pos >= 0:
        accel_block = main_frame[accel_pos:accel_pos + 1800]
        if "::MoveFile(sOldPath, sPath)" in accel_block:
            errors.append(
                "src/fxfile/main_frame.cpp: legacy accel migration must not rename from the install directory"
            )

    for token in (
        "ChangeWindowMessageFilterExFunc",
        '::GetModuleHandle(XPR_STRING_LITERAL("user32.dll"))',
        '::GetProcAddress(sUser32, "ChangeWindowMessageFilterEx")',
        "WM_SINGLE_PROCESS",
        "kMessageFilterAllow = 1",
    ):
        if token not in main_frame:
            errors.append(
                f"src/fxfile/main_frame.cpp: missing cross-integrity single-instance handoff token {token}"
            )
    if "CHANGEFILTERSTRUCT sMessageFilter" in main_frame:
        errors.append(
            "src/fxfile/main_frame.cpp: single-instance handoff must remain compatible with legacy target headers"
        )

    for token in (
        "::CopyFile(sOldPath, sNewPath, FALSE)",
        "if (::CopyFile(sOldPath, sNewPath, FALSE) == FALSE)",
        "xpr::FileSys::remove(sOldPath);",
    ):
        if token not in conf_dir:
            errors.append(
                f"src/fxfile/conf_dir.cpp: missing protected-source config migration token {token}"
            )
    if "xpr::FileSys::rename(sOldPath, sNewPath);" in conf_dir:
        errors.append(
            "src/fxfile/conf_dir.cpp: config migration must not require rename/delete access to the old directory"
        )

    shell_registry = contents["shell_registry"]
    for token in (
        'XPR_STRING_LITERAL("Software\\\\Classes\\\\Folder\\\\Shell")',
        "sRegKey.Create(HKEY_CURRENT_USER, kUserKeyName)",
        "HKEY_CURRENT_USER,",
        "KEY_READ | KEY_WRITE",
    ):
        if token not in shell_registry:
            errors.append(
                f"src/fxfile/shell_registry.cpp: missing per-user shell registration token {token}"
            )
    if "HKEY_CLASSES_ROOT" in shell_registry:
        errors.append(
            "src/fxfile/shell_registry.cpp: shell registration must not write through HKCR"
        )

    single_process = contents["single_process"]
    for token in (
        "OpenMutex(SYNCHRONIZE",
        "GetLastError() == ERROR_ACCESS_DENIED",
        "::CloseHandle(sSingleProcessMutex)",
    ):
        if token not in single_process:
            errors.append(
                f"src/fxfile/single_process.cpp: missing standard-user mutex token {token}"
            )
    if "OpenMutex(MUTEX_ALL_ACCESS" in single_process:
        errors.append(
            "src/fxfile/single_process.cpp: presence check must not require MUTEX_ALL_ACCESS"
        )

    main_coolbar = contents["main_coolbar"]
    toolbar_restore_pos = main_coolbar.find("if (mMainToolBar.load(sPath) == XPR_FALSE)")
    for token in (
        "mMainToolBar.UpdateToolbarSize();",
        "mDriveToolBar.UpdateToolbarSize();",
        "mBookmarkToolBar.UpdateToolbarSize();",
    ):
        token_pos = main_coolbar.find(token, toolbar_restore_pos)
        if toolbar_restore_pos < 0 or token_pos < toolbar_restore_pos:
            errors.append(
                f"src/fxfile/main_coolbar.cpp: missing post-restore command-bar metric token {token}"
            )

    file_scrap = contents["file_scrap"]
    for token in (
        '#include "gui/ModernUI.h"',
        "ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())",
        "const ui::ThemePalette sPalette = ui::ModernUI::getPalette();",
        "sPalette.mText",
        "sPalette.mChrome",
        "ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)",
    ):
        if token not in file_scrap:
            errors.append(
                f"src/fxfile/file_scrap_pane.cpp: missing modern file-scrap surface token {token}"
            )
    if "COLORREF sTextColor = ::GetSysColor(COLOR_BTNTEXT);" in file_scrap:
        errors.append(
            "src/fxfile/file_scrap_pane.cpp: legacy fixed button-text color returned"
        )

    bookmark_wnd = contents["bookmark_wnd"]
    for token in (
        "void BookmarkWnd::updateFont(void)",
        "ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())",
        "sLogFont.lfUnderline = XPR_TRUE;",
        "updateFont();\n    updateAppearance();",
    ):
        if token not in bookmark_wnd:
            errors.append(
                f"src/fxfile/bookmark_wnd.cpp: missing system UI bookmark-font token {token}"
            )

    search_loc = contents["search_loc"]
    for token in (
        "const ui::ThemePalette sPalette = ui::ModernUI::getPalette();",
        "sPalette.mElevated",
        "sPalette.mSeparator",
        "if (XPR_IS_FALSE(sPalette.mHighContrast))\n        return sBrush;",
    ):
        if token not in search_loc:
            errors.append(
                f"src/fxfile/cmd/search_loc_dlg.cpp: missing palette-aware search-location token {token}"
            )

    drop_menu_button_h = contents["drop_menu_button_h"]
    drop_menu_button_cpp = contents["drop_menu_button_cpp"]
    if "DrawArrow(CDC* pDC, CPoint aArrowTip, COLORREF aColor);" not in drop_menu_button_h:
        errors.append(
            "src/fxfile/gui/DropMenuButton.h: palette-aware arrow declaration is missing"
        )
    for token in (
        '#include "ModernUI.h"',
        "fxfile::ui::ModernUI::getPalette()",
        "fxfile::ui::ModernUI::getUIFont(",
        "m_xpTheme.IsAppThemed() && !bModernDark",
        "bModernDark ? sPalette.mText",
        "bDisabled ? sPalette.mSecondaryText : sPalette.mText",
        "DrawArrow(pDC, pt, sArrowColor)",
        "COLORREF aColor)",
        "pDC->SetPixel(ArrowTip, aColor)",
    ):
        if token not in drop_menu_button_cpp:
            errors.append(
                f"src/fxfile/gui/DropMenuButton.cpp: missing dark split-button token {token}"
            )
    if "DrawArrow(pDC,pt)" in drop_menu_button_cpp:
        errors.append(
            "src/fxfile/gui/DropMenuButton.cpp: legacy black-arrow call returned"
        )

    button_st_h = contents["button_st_h"]
    button_st_cpp = contents["button_st_cpp"]
    if "afx_msg LRESULT OnThemeChanged(WPARAM wParam, LPARAM lParam);" not in button_st_h:
        errors.append(
            "src/fxfile/gui/BtnST.h: modern button theme-change handler declaration is missing"
        )
    for token in (
        '#include "ModernUI.h"',
        "fxfile::ui::ModernUI::getPalette()",
        "fxfile::ui::ModernUI::getUIFont(",
        "m_xpTheme.IsAppThemed() && !bModernDark",
        "m_crColors[BTNST_COLOR_BK_IN]  = sPalette.mHover",
        "m_crColors[BTNST_COLOR_FG_OUT] = sPalette.mText",
        "pDC->SetTextColor(sPalette.mSecondaryText)",
        "CBrush sBorderBrush(sPalette.mBorder);",
        "ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)",
        "SetDefaultColors(FALSE);",
    ):
        if token not in button_st_cpp:
            errors.append(
                f"src/fxfile/gui/BtnST.cpp: missing palette-aware owner-draw button token {token}"
            )

    colour_picker = contents["colour_picker"]
    for token in (
        '#include "ModernUI.h"',
        "const bool bModernDark =",
        "m_xpButton.IsAppThemed() && !bModernDark",
        "m_xpCombo.IsAppThemed() && !bModernDark",
        "sPalette.mSecondaryText",
        "sPalette.mSeparator",
        "m_clrBackground = sPalette.mElevated",
        "m_clrText = sPalette.mText",
        "fxfile::ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())",
        "fxfile::ui::ModernUI::getUIFont(\n                sPopupLogFont,\n                GetSafeHwnd())",
    ):
        if token not in colour_picker:
            errors.append(
                f"src/fxfile/gui/ColourPickerXP.cpp: missing palette-aware colour-picker token {token}"
            )
    draw_item_pos = colour_picker.find("void CColourPickerXP::DrawItem")
    popup_init_pos = colour_picker.find("void CColourPopupXP::Initialise")
    if draw_item_pos < 0 or popup_init_pos < draw_item_pos:
        errors.append(
            "src/fxfile/gui/ColourPickerXP.cpp: colour-picker draw/popup contracts are missing"
        )

    explorer_ctrl = contents["explorer_ctrl"]
    drag_title_pos = explorer_ctrl.find(
        'XPR_STRING_LITERAL("explorer_window.drag_drop.title")'
    )
    if drag_title_pos < 0:
        errors.append(
            "src/fxfile/explorer_ctrl.cpp: drag feedback title block is missing"
        )
    else:
        drag_font_block = explorer_ctrl[drag_title_pos:drag_title_pos + 1500]
        if "ui::ModernUI::getUIFont(" not in drag_font_block:
            errors.append(
                "src/fxfile/explorer_ctrl.cpp: drag feedback must use the current Windows UI font"
            )

    cfg_filter = contents["cfg_filter"]
    cfg_filter_h = contents["cfg_filter_h"]
    for token in (
        '#include "../gui/ModernUI.h"',
        "mListCtrl.SetBkColor(sListBackground)",
        "mListCtrl.SetTextBkColor(sListBackground)",
        "sFilterTextColor == RGB(0, 0, 0)",
        "sFilterTextColor = sPalette.mText;",
        "FlatHeaderCtrl mHeaderCtrl",
        "mHeaderCtrl.SubclassWindow(sHeaderHwnd)",
    ):
        source = cfg_filter_h if token == "FlatHeaderCtrl mHeaderCtrl" else cfg_filter
        if token not in source:
            errors.append(
                f"settings filter list Dark surface contract missing token {token}"
            )

    filtering_pos = explorer_ctrl.find(
        "if (mOption.mTextColorType == COLOR_TYPE_FILTERING)"
    )
    filtering_block = (
        explorer_ctrl[filtering_pos:filtering_pos + 3200]
        if filtering_pos >= 0
        else ""
    )
    for token in (
        'sFilterItem->mExts == XPR_STRING_LITERAL("*.*")',
        "sFilterTextColor == RGB(0, 0, 0)",
        "XPR_IS_FALSE(sPalette.mHighContrast)",
        "sFilterTextColor = sPalette.mText;",
        "mOption.mBkgndColorType == COLOR_TYPE_FILTERING",
    ):
        if token not in filtering_block:
            errors.append(
                f"src/fxfile/explorer_ctrl.cpp: dark filtering readability contract missing token {token}"
            )

    modern_ui = contents["modern_ui"]
    for token in (
        "kThemeAssociationProp",
        "ControlThemeAssociationExplorer",
        "ControlThemeAssociationDefault",
        "ControlThemeAssociationDisabled",
        "hasControlThemeAssociation",
        "rememberControlThemeAssociation",
        "hasControlThemeAssociation(aHwnd, sDesiredAssociation)",
        "ControlThemeAssociationDisabled)))",
    ):
        if token not in modern_ui:
            errors.append(
                f"src/fxfile/gui/ModernUI.cpp: missing idempotent theme-association token {token}"
            )

    for token in (
        "kThemeApplyGuardProp",
        "beginControlThemeChange",
        "endControlThemeChange",
        "::GetProp(aHwnd, kThemeApplyGuardProp)",
        "::SetProp(",
        "::RemoveProp(",
    ):
        if token not in modern_ui:
            errors.append(
                f"src/fxfile/gui/ModernUI.cpp: missing theme reentrancy guard token {token}"
            )

    if modern_ui.count("beginControlThemeChange(aHwnd)") < 2:
        errors.append(
            "src/fxfile/gui/ModernUI.cpp: both apply/reset control-theme paths must use the reentrancy guard"
        )
    if modern_ui.count("endControlThemeChange(aHwnd)") < 2:
        errors.append(
            "src/fxfile/gui/ModernUI.cpp: both apply/reset control-theme paths must release the reentrancy guard"
        )

    bookmark = contents["bookmark_set"]
    bookmark_start = bookmark.find("LRESULT BookmarkSetWnd::OnThemeChanged")
    bookmark_end = bookmark.find("\n}", bookmark_start)
    bookmark_block = (
        bookmark[bookmark_start:bookmark_end]
        if bookmark_start >= 0 and bookmark_end > bookmark_start
        else ""
    )
    if not bookmark_block:
        errors.append(
            "src/fxfile/bookmark_set_wnd.cpp: BookmarkSetWnd::OnThemeChanged block not found"
        )
    elif "applyExplorerControlTheme" in bookmark_block:
        errors.append(
            "src/fxfile/bookmark_set_wnd.cpp: WM_THEMECHANGED must not synchronously reapply SetWindowTheme"
        )

    address = contents["address"]
    address_start = address.find("void AddressBar::OnNcPaint(void)")
    address_end = address.find("\n}", address_start)
    address_block = (
        address[address_start:address_end]
        if address_start >= 0 and address_end > address_start
        else ""
    )
    if not address_block:
        errors.append("src/fxfile/address_bar.cpp: AddressBar::OnNcPaint block not found")
    else:
        if "if (XPR_IS_TRUE(sPalette.mHighContrast))" not in address_block:
            errors.append(
                "src/fxfile/address_bar.cpp: address non-client paint must preserve High Contrast fallback"
            )
        if "Default();\n        return;" not in address_block:
            errors.append(
                "src/fxfile/address_bar.cpp: native non-client painting must be limited to High Contrast"
            )
        if "PaintFlatAddressEdge(m_hWnd, sPalette.mElevated)" not in address_block:
            errors.append(
                "src/fxfile/address_bar.cpp: palette-owned address frame painting is missing"
            )
        for token in (
            "PaintFlatAddressEdge(m_hWnd, sPalette.mElevated)",
            "sPalette.mElevated",
        ):
            if token not in address_block:
                errors.append(
                    f"src/fxfile/address_bar.cpp: flat outer address edge missing token {token}"
                )
        for forbidden in (
            "sPalette.mFocus",
            "sPalette.mBorder",
            "sFocused",
        ):
            if forbidden in address_block:
                errors.append(
                    f"src/fxfile/address_bar.cpp: persistent/focus address outline returned: {forbidden}"
                )
        if "void AddressBar::OnNcPaint(void)\n{\n    Default();" in address:
            errors.append(
                "src/fxfile/address_bar.cpp: legacy native address frame is painting before the custom frame"
            )

    if "CBS_OWNERDRAWFIXED" in address:
        errors.append(
            "src/fxfile/address_bar.cpp: legacy owner-draw address style must not return without a DrawItem owner"
        )
    for token in (
        "void PaintFlatAddressEdge(HWND aHwnd, COLORREF aColor)",
        "case WM_NCPAINT:",
        "PaintFlatAddressEdge(aHwnd, sPalette.mElevated)",
        "ON_WM_CTLCOLOR()",
        "HBRUSH AddressBar::OnCtlColor",
        "handleComboCtlColor(",
        "kAddressBarOuterBorderProp",
        "kAddressBarOuterClientEdgeProp",
        "kAddressBarComboBorderProp",
        "kAddressBarComboClientEdgeProp",
        "kAddressBarEditBorderProp",
        "kAddressBarEditClientEdgeProp",
        "sNewOuterStyle &= ~static_cast<LONG_PTR>(WS_BORDER)",
        "sNewOuterExStyle &= ~static_cast<LONG_PTR>(WS_EX_CLIENTEDGE)",
        "sNewComboStyle &= ~static_cast<LONG_PTR>(WS_BORDER)",
        "sNewComboExStyle &= ~static_cast<LONG_PTR>(WS_EX_CLIENTEDGE)",
        "sNewEditStyle &= ~static_cast<LONG_PTR>(WS_BORDER)",
        "sNewEditExStyle &= ~static_cast<LONG_PTR>(WS_EX_CLIENTEDGE)",
        "SWP_FRAMECHANGED",
        "case WM_ERASEBKGND:",
    ):
        if token not in address:
            errors.append(
                f"src/fxfile/address_bar.cpp: missing single-frame dark address token {token}"
            )

    for token in (
        "ImageList_Duplicate(m_imageListCold.m_hImageList)",
        "SetDisabledImageList(&m_imageListDisabled)",
    ):
        if token not in contents["toolbar_cpp"]:
            errors.append(
                f"src/fxfile/gui/rebar/ToolBarEx.cpp: missing Dark disabled-icon fallback token {token}"
            )

    for token in (
        "sPalette.mSecondaryText",
        "m_imageListDisabled.m_hImageList",
        "ImageList_ReplaceIcon(",
    ):
        if token not in contents["main_toolbar"]:
            errors.append(
                f"src/fxfile/main_toolbar.cpp: missing disabled Fluent icon token {token}"
            )

    if "TBI_LARGE, IL_COLOR_MASK);" not in contents["main_toolbar"]:
        errors.append(
            "src/fxfile/main_toolbar.cpp: default toolbar icon mode must remain the readable large Fluent size"
        )
    for token in (
        "kModernToolbarStateMarker",
        "sModernToolbarState = XPR_FALSE",
        "sId == kModernToolbarStateMarker",
        "XPR_IS_FALSE(sModernToolbarState) && sIconType == TBI_SMALL",
        "sId = kModernToolbarStateMarker;",
    ):
        if token not in contents["main_toolbar"]:
            errors.append(
                f"src/fxfile/main_toolbar.cpp: one-time legacy icon migration missing token {token}"
            )

    for token in (
        "TB_GETBUTTONTEXT",
        "nmcd.dwItemSpec > IDBUTTON_SYSMENU",
        "nmcd.dwItemSpec <= IDBUTTON_LAST",
        "*pResult = CDRF_SKIPDEFAULT",
    ):
        if token not in contents["menubar"]:
            errors.append(
                f"src/fxfile/gui/rebar/MenuBar.cpp: missing final Dark text ownership token {token}"
            )
    if "CommandToIndex(static_cast<UINT>(nmcd.dwItemSpec))" in contents["menubar"]:
        errors.append(
            "src/fxfile/gui/rebar/MenuBar.cpp: Dark text ownership must not depend on ambiguous custom-draw item indexing"
        )

    for source_name in ("toolbar_cpp", "menubar"):
        for token in (
            "TBCDRF_USECDCOLORS",
            "clrTextHighlight",
            "nStringBkMode = TRANSPARENT",
            "nHLStringBkMode = TRANSPARENT",
        ):
            if token not in contents[source_name]:
                errors.append(
                    f"{source_name}: ToolbarWindow32 palette text contract missing token {token}"
                )

    horizontal_start = modern_ui.find(
        "xpr_sint_t ModernUI::getCommandHorizontalPadding(HWND aHwnd)"
    )
    horizontal_end = modern_ui.find("\n}", horizontal_start)
    horizontal_block = (
        modern_ui[horizontal_start:horizontal_end]
        if horizontal_start >= 0 and horizontal_end > horizontal_start
        else ""
    )
    if "scaleForWindow(7, aHwnd)" not in horizontal_block:
        errors.append(
            "src/fxfile/gui/ModernUI.cpp: command horizontal padding regressed from the Win11 compact metric"
        )

    vertical_start = modern_ui.find(
        "xpr_sint_t ModernUI::getCommandVerticalPadding(HWND aHwnd)"
    )
    vertical_end = modern_ui.find("\n}", vertical_start)
    vertical_block = (
        modern_ui[vertical_start:vertical_end]
        if vertical_start >= 0 and vertical_end > vertical_start
        else ""
    )
    if "scaleForWindow(6, aHwnd)" not in vertical_block:
        errors.append(
            "src/fxfile/gui/ModernUI.cpp: command vertical padding regressed from the Win11 compact metric"
        )

    if "ModernUI::getUIFont(sMenuFont, m_hWnd)" not in contents["menubar"]:
        errors.append(
            "src/fxfile/gui/rebar/MenuBar.cpp: menu bar must use the shared DPI-aware system UI font"
        )

    for token in (
        "EnumThreadWindows(",
        "RefreshThemeTopLevelWindow",
        "SendMessageToDescendants(",
        "WM_SETTINGCHANGE",
    ):
        if token not in contents["main_frame"]:
            errors.append(
                f"src/fxfile/main_frame.cpp: app theme switch must refresh every UI-thread top-level window; missing {token}"
            )

    for token in (
        "GetTextMetrics(&sTextMetric)",
        "sTextMetric.tmHeight",
        "sTextMetric.tmExternalLeading",
        "ModernUI::scale(24, sDpi)",
        "ModernUI::scale(8, sDpi)",
    ):
        if token not in contents["header"]:
            errors.append(
                f"src/fxfile/gui/FlatHeaderCtrl.cpp: font/DPI-derived header height missing token {token}"
            )

    if "ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())" not in contents["contents"]:
        errors.append(
            "src/fxfile/contents_wnd.cpp: contents pane must use the shared DPI-aware system UI font"
        )
    if "ui::ModernUI::getDpi(GetSafeHwnd())" not in contents["contents"]:
        errors.append(
            "src/fxfile/contents_wnd.cpp: contents title font size must follow the current monitor DPI"
        )
    if "GetDeviceCaps(GetDC()->m_hDC, LOGPIXELSY)" in contents["contents"]:
        errors.append(
            "src/fxfile/contents_wnd.cpp: legacy screen-DC title font DPI path returned"
        )

    for source_name, source_path in (
        ("modern_dialog", "src/fxfile/gui/ModernDialog.cpp"),
        ("resizing_dialog", "src/fxfile/gui/ResizingDialog.cpp"),
        ("title_dialog", "src/fxfile/cmd/title_dlg.cpp"),
    ):
        source = contents[source_name]
        for token in (
            "sPalette.mDark",
            "sPalette.mHighContrast",
            "resetControlTheme(aWnd->GetSafeHwnd())",
            "applyExplorerControlTheme",
        ):
            if token not in source:
                errors.append(
                    f"{source_path}: common dialog Dark theme ownership missing token {token}"
                )

    cfg_page = contents["cfg_page_cpp"]
    for token in (
        "SnapshotChildWindows",
        "SnapshotChildWindows(aWnd->GetSafeHwnd(), sChildHwnds)",
        "SnapshotChildWindows(GetSafeHwnd(), sChildHwnds)",
    ):
        if token not in cfg_page:
            errors.append(
                f"src/fxfile/cfg/cfg_dlg.cpp: stable child traversal missing token {token}"
            )
    if "CWnd *sNextChild = sChild->GetNextWindow()" in cfg_page:
        errors.append(
            "src/fxfile/cfg/cfg_dlg.cpp: live sibling traversal cannot be used while GROUPBOX z-order changes"
        )

    for source_name in ("cfg_main_h", "cfg_page_h"):
        if "mRefreshingModernAppearance" not in contents[source_name]:
            errors.append(
                f"{source_name}: settings theme refresh reentrancy guard field is missing"
            )
    for source_name in ("cfg_main_cpp", "cfg_page_cpp"):
        source = contents[source_name]
        for token in (
            "XPR_IS_TRUE(mRefreshingModernAppearance)",
            "mRefreshingModernAppearance = XPR_TRUE;",
            "mRefreshingModernAppearance = XPR_FALSE;",
            "refreshModernAppearance(XPR_FALSE);",
            "if (XPR_IS_TRUE(aRethemeControls))",
        ):
            if token not in source:
                errors.append(
                    f"{source_name}: settings theme refresh guard missing token {token}"
                )

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
    errors.extend(validate_modern_subclass_forwarding())
    errors.extend(validate_window_frame_theme_integration())
    errors.extend(validate_theme_mode_contract())
    errors.extend(validate_common_control_theme_integration())
    errors.extend(validate_modern_dialog_migration())
    errors.extend(validate_custom_dialog_paint_regressions())
    errors.extend(validate_toolbar_custom_draw_regression())
    errors.extend(validate_command_surface_contract())
    errors.extend(validate_configuration_shell_contract())
    errors.extend(validate_soft_surface_contract())
    errors.extend(validate_navigation_surface_contract())
    errors.extend(validate_content_surface_contract())
    errors.extend(validate_popup_menu_contract())
    errors.extend(validate_fluent_asset_contract())
    errors.extend(validate_ui_resource_contracts())
    errors.extend(validate_functional_test_wiring())
    errors.extend(validate_local_ci_warning_policy_wiring())
    errors.extend(validate_active_ci_scope_documentation())
    errors.extend(validate_installer_smoke_wiring())
    errors.extend(validate_win11_stability_regressions())
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
