//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#ifndef __FXFILE_ADDRESS_BAR_H__
#define __FXFILE_ADDRESS_BAR_H__ 1
#pragma once

#include "shell_change_notify.h"

namespace fxfile
{
class AddressBarObserver;

class AddressBar : public CComboBoxEx
{
public:
    AddressBar(void);
    virtual ~AddressBar(void);

public:
    void setObserver(AddressBarObserver *aObserver);

    xpr_bool_t explore(const xpr_tchar_t *aFullPath, xpr_bool_t aNotifyBuddy = XPR_FALSE);
    xpr_bool_t explore(LPITEMIDLIST aFullPidl, xpr_bool_t aNotifyBuddy = XPR_FALSE);

    void getFullPath(xpr_sint_t aIndex, xpr::string &aFullPath) const;

    xpr_bool_t execute(const xpr_tchar_t *aPath);
    void setSystemImageList(CImageList *aSmallImgList);

    void setAutoComplete(void);

    void setCustomFont(CFont *aFont);
    void setCustomFont(xpr_tchar_t *aFontText);

protected:
    void setDisplayFont(const LOGFONT *aLogFont);
    void applyDisplayFont(CFont *aFont);
    void updateMetrics(void);

    void applyModernAppearance(void);
    void installComboSubclass(void);
    void removeComboSubclass(void);
    void installEditSubclass(void);
    void removeEditSubclass(void);
    void applyChildThemes(void);
    void redrawModernFrame(void);
    void drawModernComboButton(HWND aComboHwnd);
    LRESULT handleComboCtlColor(xpr_uint_t aMessage, HDC aDC, HWND aControlHwnd);
    static LRESULT CALLBACK ComboSubclassProc(
        HWND aHwnd,
        UINT aMessage,
        WPARAM aWParam,
        LPARAM aLParam,
        UINT_PTR aSubclassId,
        DWORD_PTR aRefData);
    static LRESULT CALLBACK EditSubclassProc(
        HWND aHwnd,
        UINT aMessage,
        WPARAM aWParam,
        LPARAM aLParam,
        UINT_PTR aSubclassId,
        DWORD_PTR aRefData);

    typedef std::deque<LPABITEMDATA> CbItemDataDeque;

    xpr_bool_t exploreItem(LPITEMIDLIST aFullPidl, xpr_bool_t aNotifyBuddy = XPR_FALSE);

    xpr_bool_t getItemAttributes(LPSHELLFOLDER aShellFolder, LPCITEMIDLIST aPidl, xpr_ulong_t &aShellAttributes, DWORD &aFileAttributes);

    void doBaseItems(void);
    void doBaseItems(xpr_uint_t aType);
    void doBaseItemsInDesktop(void);
    void doBaseItemsInComputer(void);

    void sortItems(CbItemDataDeque &aCbItemDataDeque);
    void sortTreeItems(CbItemDataDeque &aCbItemDataDeque);
    void insertItems(CbItemDataDeque &aCbItemDataDeque, xpr_uint_t aInsert, xpr_bool_t aForParsing = XPR_FALSE);

    xpr_bool_t fillItem(
        LPSHELLFOLDER aShellFolder,
        LPITEMIDLIST  aFullPidl,
        xpr_uint_t    aLevel,
        xpr_uint_t    aInsert,
        xpr_tchar_t  *aName,
        xpr_uint_t    aType);

    xpr_sint_t searchName(const xpr_tchar_t *aName);
    xpr_sint_t searchFullPath(const xpr_tchar_t *aFullPath);

    void OnShcnRenameItem(xpr_uint_t aType, Shcn *aShcn);
    void OnShcnDeleteItem(xpr_uint_t aType, LPITEMIDLIST aFullPidl);
    void OnShcnUpdateDir(xpr_uint_t aType, LPITEMIDLIST aFullPidl);

protected:
    AddressBarObserver *mObserver;

    CImageList   *mSmallImgList;

    xpr_bool_t    mInit;
    xpr_sint_t    mCurSel;
    LPITEMIDLIST  mOldSelFullPidl;
    xpr_sint_t    mAutoComplete;

    CFont        *mDisplayFont;

    CBrush         mBackgroundBrush;
    HWND           mComboBoxHwnd;
    HWND           mEditHwnd;

    xpr_uint_t    mShcnDesktopId;
    xpr_uint_t    mShcnComputerId;

public:
    virtual xpr_bool_t Create(CWnd *aParentWnd, xpr_uint_t aId, const RECT &aRect);
    virtual xpr_bool_t PreTranslateMessage(MSG *aMsg);
    virtual xpr_bool_t DestroyWindow(void);

protected:
    DECLARE_MESSAGE_MAP()
    afx_msg void OnDeleteItem(NMHDR *aNmHdr, LRESULT *aResult);
    afx_msg xpr_sint_t OnCreate(LPCREATESTRUCT aCreateStruct);
    afx_msg void OnPaint(void);
    afx_msg void OnNcPaint(void);
    afx_msg HBRUSH OnCtlColor(CDC *aDC, CWnd *aWnd, xpr_uint_t aCtlColor);
    afx_msg void OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection);
    afx_msg void OnSysColorChange(void);
    afx_msg LRESULT OnThemeChanged(WPARAM aWParam, LPARAM aLParam);
    afx_msg LRESULT OnDpiChanged(WPARAM aWParam, LPARAM aLParam);
    afx_msg void OnSelEndOK(void);
    afx_msg void OnSelChange(void);
    afx_msg void OnDropdown(void);
    afx_msg LRESULT OnShcnDesktop(WPARAM wParam, LPARAM lParam);
    afx_msg LRESULT OnShcnComputer(WPARAM wParam, LPARAM lParam);
};
} // namespace fxfile

#endif // __FXFILE_ADDRESS_BAR_H__
