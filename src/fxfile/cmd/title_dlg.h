//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#ifndef __FXFILE_TITLE_DLG_H__
#define __FXFILE_TITLE_DLG_H__ 1
#pragma once

namespace fxfile
{
namespace cmd
{
class TitleDlg : public CDialog
{
public:
    TitleDlg(const xpr_uint_t aResourceId);

public:
    void setTitle(const xpr_tchar_t *aTitle);
    void setDesc(const xpr_tchar_t *aDesc);
    void setDescIcon(xpr_uint_t aIconId, xpr_bool_t aIconLeft = XPR_FALSE);
    void setDescIcon(HICON aIcon, xpr_bool_t aIconLeft = XPR_FALSE, xpr_bool_t aBold = XPR_FALSE);
    void setCtrlOffset(xpr_sint_t aOffset);

protected:
    xpr_sint_t   mOffset;

    CFont        mUIFont;
    CFont        mTitleFont;
    CBrush       mSurfaceBrush;
    CBrush       mWindowBrush;
    COLORREF     mSurfaceColor;
    COLORREF     mWindowColor;
    xpr_bool_t   mBold;

    xpr_bool_t   mIconLeft;
    HICON        mDescIcon;
    xpr_uint_t   mDescIconResourceId;
    xpr::string  mTitle;
    xpr::string  mDesc;

protected:
    void refreshModernAppearance(void);
    void refreshDescResourceIcon(void);
    void applyModernAppearanceToChildren(HFONT aPreviousFont);
    void applyModernAppearanceToChild(CWnd *aWnd, HFONT aPreviousFont);

protected:
    DECLARE_MESSAGE_MAP()
    virtual xpr_bool_t OnInitDialog(void);
    afx_msg void OnPaint(void);
    afx_msg xpr_bool_t OnEraseBkgnd(CDC *aDC);
    afx_msg HBRUSH OnCtlColor(CDC *aDC, CWnd *aWnd, xpr_uint_t aCtlColor);
    afx_msg void OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection);
    afx_msg void OnSysColorChange(void);
    afx_msg LRESULT OnThemeChanged(WPARAM aWParam, LPARAM aLParam);
    afx_msg LRESULT OnDpiChanged(WPARAM aWParam, LPARAM aLParam);
    afx_msg void OnDestroy(void);
};
} // namespace cmd
} // namespace fxfile

#endif // __FXFILE_TITLE_DLG_H__
