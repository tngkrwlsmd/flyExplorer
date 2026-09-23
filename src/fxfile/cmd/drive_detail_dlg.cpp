//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "drive_detail_dlg.h"

#include "size_format.h"
#include "option.h"
#include "resource.h"
#include "gui/ModernUI.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace cmd
{
DriveDetailDlg::DriveDetailDlg(void)
    : super(IDD_DRIVE_DETAIL, XPR_NULL)
    , mDriveIconHandle(XPR_NULL)
{
}

void DriveDetailDlg::DoDataExchange(CDataExchange* pDX)
{
    super::DoDataExchange(pDX);
    DDX_Control(pDX, IDC_DRIVE_INFO,     mDrivePieCtrl);
    DDX_Control(pDX, IDC_DRIVE_PROGRESS, mProgressCtrl);
}

BEGIN_MESSAGE_MAP(DriveDetailDlg, super)
    ON_WM_DESTROY()
    ON_WM_ERASEBKGND()
    ON_WM_CTLCOLOR()
    ON_WM_SETTINGCHANGE()
    ON_MESSAGE(WM_DPICHANGED, OnDpiChanged)
    ON_MESSAGE(WM_DPICHANGED_AFTERPARENT, OnDpiChangedAfterParent)
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
END_MESSAGE_MAP()

xpr_bool_t DriveDetailDlg::OnInitDialog(void) 
{
    super::OnInitDialog();

    createUIFont();
    applyUIFont();
    applyAppearance();

    SetDlgItemText(IDC_DRIVE_LABEL_LABEL,      gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.label.label")));
    SetDlgItemText(IDC_DRIVE_LABEL_TYPE,       gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.label.type")));
    SetDlgItemText(IDC_DRIVE_LABEL_FILESYSTEM, gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.label.file_system")));
    SetDlgItemText(IDC_DRIVE_LABEL_FREE,       gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.label.free_size")));
    SetDlgItemText(IDC_DRIVE_LABEL_USED,       gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.label.used_size")));
    SetDlgItemText(IDC_DRIVE_LABEL_TOTAL,      gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.label.total_size")));

    mDrivePieCtrl.setString(
        gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.pie.total_size")),
        gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.pie.used_size")),
        gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.pie.free_size")));

    return XPR_TRUE;
}

void DriveDetailDlg::createUIFont(void)
{
    LOGFONT sLogFont = {0};
    if (XPR_IS_TRUE(ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())))
    {
        if (XPR_IS_TRUE(
                ui::ModernUI::isSameFont(
                    reinterpret_cast<HFONT>(mUIFont.GetSafeHandle()),
                    sLogFont)))
        {
            return;
        }

        if (XPR_IS_NOT_NULL(mUIFont.m_hObject))
            mUIFont.DeleteObject();

        if (mUIFont.CreateFontIndirect(&sLogFont) == XPR_FALSE)
            mUIFont.CreateStockObject(DEFAULT_GUI_FONT);
    }
    else if (XPR_IS_NULL(mUIFont.m_hObject))
    {
        mUIFont.CreateStockObject(DEFAULT_GUI_FONT);
    }
}

void DriveDetailDlg::applyUIFont(void)
{
    if (XPR_IS_NULL(mUIFont.m_hObject))
        return;

    SetFont(&mUIFont, XPR_FALSE);

    const xpr_uint_t sControlIds[] =
    {
        IDC_DRIVE_DRIVE,
        IDC_DRIVE_LABEL_LABEL,
        IDC_DRIVE_LABEL_TYPE,
        IDC_DRIVE_LABEL_FILESYSTEM,
        IDC_DRIVE_LABEL_FREE,
        IDC_DRIVE_LABEL_USED,
        IDC_DRIVE_LABEL_TOTAL,
        IDC_DRIVE_LABEL,
        IDC_DRIVE_TYPE,
        IDC_DRIVE_FILESYSTEM,
        IDC_DRIVE_FREE_BYTE,
        IDC_DRIVE_FREE_UNIT,
        IDC_DRIVE_USED_BYTE,
        IDC_DRIVE_USED_UNIT,
        IDC_DRIVE_TOTAL_BYTE,
        IDC_DRIVE_TOTAL_UNIT,
    };

    for (xpr_size_t i = 0; i < XPR_COUNT_OF(sControlIds); ++i)
    {
        CWnd *sControl = GetDlgItem(sControlIds[i]);
        if (XPR_IS_NOT_NULL(sControl))
        {
            sControl->SetFont(&mUIFont, XPR_FALSE);
            ui::ModernUI::applyDialogControlTheme(sControl->GetSafeHwnd());
        }
    }

    if (::IsWindow(mDrivePieCtrl.GetSafeHwnd()) == XPR_TRUE)
        mDrivePieCtrl.SetFont(&mUIFont, XPR_FALSE);

    // TextProgressCtrl owns its ModernUI font because it is a shared control.
    // Preserve this dialog's existing bold percentage contract.
    if (::IsWindow(mProgressCtrl.GetSafeHwnd()) == XPR_TRUE)
        mProgressCtrl.setBoldFont(XPR_TRUE);
}

void DriveDetailDlg::applyAppearance(void)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    const COLORREF sTrackColor =
        XPR_IS_TRUE(sPalette.mHighContrast) ? sPalette.mWindow : sPalette.mSurface;

    if (::IsWindow(mProgressCtrl.GetSafeHwnd()) == XPR_TRUE)
    {
        mProgressCtrl.setProgressColor(sPalette.mSelection);
        mProgressCtrl.setBackColor(sTrackColor);
        mProgressCtrl.setTextBackColor(sPalette.mSelectionText);
        mProgressCtrl.setTextProgressColor(sPalette.mText);
        mProgressCtrl.Invalidate(XPR_FALSE);
    }

    if (::IsWindow(mDrivePieCtrl.GetSafeHwnd()) == XPR_TRUE)
        mDrivePieCtrl.Invalidate(XPR_FALSE);
}

void DriveDetailDlg::refreshAppearance(void)
{
    createUIFont();
    applyUIFont();
    applyAppearance();
    Invalidate(XPR_FALSE);
}

void DriveDetailDlg::OnDestroy(void) 
{
    super::OnDestroy();

    DESTROY_ICON(mDriveIconHandle);

    if (XPR_IS_NOT_NULL(mUIFont.m_hObject))
        mUIFont.DeleteObject();
}

xpr_bool_t DriveDetailDlg::OnEraseBkgnd(CDC *aDC)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mHighContrast))
    {
        CRect sClientRect;
        GetClientRect(&sClientRect);
        aDC->FillSolidRect(&sClientRect, sPalette.mCard);
        return XPR_TRUE;
    }

    return super::OnEraseBkgnd(aDC);
}

HBRUSH DriveDetailDlg::OnCtlColor(
    CDC *aDC,
    CWnd *aWnd,
    xpr_uint_t aCtlColor)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mHighContrast))
        return super::OnCtlColor(aDC, aWnd, aCtlColor);

    aDC->SetTextColor(
        XPR_IS_NOT_NULL(aWnd) && XPR_IS_FALSE(aWnd->IsWindowEnabled()) ?
        sPalette.mSecondaryText :
        sPalette.mText);

    const COLORREF sBackground =
        (aCtlColor == CTLCOLOR_EDIT || aCtlColor == CTLCOLOR_LISTBOX) ?
        sPalette.mElevated :
        sPalette.mCard;

    aDC->SetBkColor(sBackground);
    aDC->SetBkMode(
        (aCtlColor == CTLCOLOR_EDIT || aCtlColor == CTLCOLOR_LISTBOX) ?
        OPAQUE :
        TRANSPARENT);
    ::SetDCBrushColor(aDC->GetSafeHdc(), sBackground);
    return static_cast<HBRUSH>(::GetStockObject(DC_BRUSH));
}

void DriveDetailDlg::OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection)
{
    refreshAppearance();
    super::OnSettingChange(aFlags, aSection);
}

LRESULT DriveDetailDlg::OnDpiChanged(WPARAM aWParam, LPARAM aLParam)
{
    refreshAppearance();
    return 0;
}

LRESULT DriveDetailDlg::OnDpiChangedAfterParent(WPARAM aWParam, LPARAM aLParam)
{
    // DriveDetailDlg is a DS_CONTROL child window. Per-Monitor V2 notifies
    // child windows after their parent has processed the monitor DPI change.
    refreshAppearance();
    return 0;
}

LRESULT DriveDetailDlg::OnThemeChanged(WPARAM aWParam, LPARAM aLParam)
{
    applyAppearance();
    Invalidate(XPR_FALSE);
    return 0;
}

void DriveDetailDlg::setDrive(xpr_tchar_t aDrive)
{
    xpr_tchar_t sDrivePath[XPR_MAX_PATH + 1] = {0};
    _stprintf(sDrivePath, XPR_STRING_LITERAL("%c:\\"), aDrive);

    xpr_tchar_t sText[XPR_MAX_PATH + 1] = {0};
    _stprintf(sText, XPR_STRING_LITERAL("%c %s"), aDrive, gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.drive")));
    GetDlgItem(IDC_DRIVE_DRIVE)->SetWindowText(sText);

    SHFILEINFO sShFileInfo = {0};
    HICON sOldDriveIcon = mDriveIconHandle;
    mDriveIconHandle = XPR_NULL;

    if (SHGetFileInfo(
            sDrivePath,
            0,
            &sShFileInfo,
            sizeof(SHFILEINFO),
            SHGFI_ICON) != 0)
    {
        mDriveIconHandle = sShFileInfo.hIcon;
    }

    CStatic *sDriveIcon = (CStatic *)GetDlgItem(IDC_DRIVE_ICON);
    if (XPR_IS_NOT_NULL(sDriveIcon))
        sDriveIcon->SetIcon(mDriveIconHandle);

    DESTROY_ICON(sOldDriveIcon);

    xpr_sint_t sDriveType = GetRootDriveType(aDrive);
    switch (sDriveType)
    {
    case DriveType8InchFloppyDisk:   _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("common.drive.type.8_inch_floppy")));    break;
    case DriveType35InchFloppyDisk:  _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("common.drive.type.3.5_inch_floppy")));  break;
    case DriveType525InchFloppyDisk: _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("common.drive.type.5.25_inch_floppy"))); break;
    case DriveTypeRemovableDisk:     _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("common.drive.type.removable")));        break;
    case DriveTypeLocal:             _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("common.drive.type.local")));            break;
    case DriveTypeNetwork:           _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("common.drive.type.network")));          break;
    case DriveTypeCdRom:             _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("common.drive.type.cdrom")));            break;
    case DriveTypeRam:               _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("common.drive.type.ram")));              break;

    case DriveTypeUnknown:
    default:                         _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("common.drive.type.unknown")));          break;
    }

    GetDlgItem(IDC_DRIVE_TYPE)->SetWindowText(sText);

    xpr_tchar_t sFileSystem[XPR_MAX_PATH + 1] = {0};
    if (GetVolumeInformation(sDrivePath, sText, XPR_MAX_PATH, XPR_NULL, XPR_NULL, XPR_NULL, sFileSystem, XPR_MAX_PATH) == XPR_FALSE)
    {
        _tcscpy(sText, gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.unknown_label")));
        _tcscpy(sFileSystem, gApp.loadString(XPR_STRING_LITERAL("popup.drive_info.unknown_file_system")));
    }
    GetDlgItem(IDC_DRIVE_FILESYSTEM)->SetWindowText(sFileSystem);
    GetDlgItem(IDC_DRIVE_LABEL)->SetWindowText(sText);

    mProgressCtrl.setBoldFont(XPR_TRUE);
    mProgressCtrl.setRange(0, 100);
    mProgressCtrl.setPos(0);

    // [2009/11/15] bug patched
    // Crash Occurrence in Windows NT 4.0 below
    ULARGE_INTEGER sTemp  = {0};
    ULARGE_INTEGER sTotal = {0};
    ULARGE_INTEGER sFree  = {0};
    ULARGE_INTEGER sUsed  = {0};
    if (::GetDiskFreeSpaceEx(sDrivePath, &sTemp, &sTotal, &sFree) == XPR_FALSE)
        return;

    sUsed.QuadPart = sTotal.QuadPart - sFree.QuadPart;

    xpr_tchar_t sFormatedSize[0xff] = {0};
    SizeFormat::getSizeUnitFormat(sFree.QuadPart, SIZE_UNIT_BYTE, sFormatedSize, 0xfe);
    GetDlgItem(IDC_DRIVE_FREE_BYTE)->SetWindowText(sFormatedSize);
    SizeFormat::getSizeUnitFormat(sFree.QuadPart, SIZE_UNIT_AUTO, sFormatedSize, 0xfe);
    GetDlgItem(IDC_DRIVE_FREE_UNIT)->SetWindowText(sFormatedSize);

    SizeFormat::getSizeUnitFormat(sTotal.QuadPart, SIZE_UNIT_BYTE, sFormatedSize, 0xfe);
    GetDlgItem(IDC_DRIVE_TOTAL_BYTE)->SetWindowText(sFormatedSize);
    SizeFormat::getSizeUnitFormat(sTotal.QuadPart, SIZE_UNIT_AUTO, sFormatedSize, 0xfe);
    GetDlgItem(IDC_DRIVE_TOTAL_UNIT)->SetWindowText(sFormatedSize);

    SizeFormat::getSizeUnitFormat(sUsed.QuadPart, SIZE_UNIT_BYTE, sFormatedSize, 0xfe);
    GetDlgItem(IDC_DRIVE_USED_BYTE)->SetWindowText(sFormatedSize);
    SizeFormat::getSizeUnitFormat(sUsed.QuadPart, SIZE_UNIT_AUTO, sFormatedSize, 0xfe);
    GetDlgItem(IDC_DRIVE_USED_UNIT)->SetWindowText(sFormatedSize);

    xpr_sint_t sUsedPercent = 0;
    if (sTotal.QuadPart > 0)
    {
        sUsedPercent = (xpr_sint_t)(
            ((xpr_double_t)(xpr_sint64_t)sUsed.QuadPart /
             (xpr_double_t)(xpr_sint64_t)sTotal.QuadPart) * 100.0);
    }

    mProgressCtrl.setPos(sUsedPercent);
    mDrivePieCtrl.setDrive(sDrivePath);
}
} // namespace cmd
} // namespace fxfile
