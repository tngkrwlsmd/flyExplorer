//
// Copyright (c) 2026 flyExplorer contributors.
//
// Shared ModernUI foundation for non-resizing MFC dialogs.
//

#ifndef __FXFILE_GUI_MODERN_DIALOG_H__
#define __FXFILE_GUI_MODERN_DIALOG_H__ 1
#pragma once

class CModernDialog : public CDialog
{
    typedef CDialog super;

public:
    CModernDialog(void);
    CModernDialog(UINT aResourceId, CWnd *aParentWnd = XPR_NULL);
    virtual ~CModernDialog(void);

protected:
    void refreshModernAppearance(void);
    void applyModernAppearanceToChildren(HFONT aPreviousFont);
    void applyModernAppearanceToChild(CWnd *aWnd, HFONT aPreviousFont);

protected:
    CFont    mModernUIFont;
    CBrush   mModernSurfaceBrush;
    CBrush   mModernWindowBrush;
    COLORREF mModernSurfaceColor;
    COLORREF mModernWindowColor;

protected:
    DECLARE_MESSAGE_MAP()
    virtual BOOL OnInitDialog(void);
    afx_msg BOOL OnEraseBkgnd(CDC *aDC);
    afx_msg HBRUSH OnCtlColor(CDC *aDC, CWnd *aWnd, UINT aCtlColor);
    afx_msg void OnSettingChange(UINT aFlags, LPCTSTR aSection);
    afx_msg void OnSysColorChange(void);
    afx_msg LRESULT OnThemeChanged(WPARAM aWParam, LPARAM aLParam);
    afx_msg LRESULT OnDpiChanged(WPARAM aWParam, LPARAM aLParam);
    afx_msg LRESULT OnDpiChangedAfterParent(WPARAM aWParam, LPARAM aLParam);
};

#endif // __FXFILE_GUI_MODERN_DIALOG_H__
