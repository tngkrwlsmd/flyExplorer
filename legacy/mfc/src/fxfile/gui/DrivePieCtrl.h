//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#ifndef __FXFILE_DRIVE_PIE_CTRL_H__
#define __FXFILE_DRIVE_PIE_CTRL_H__
#pragma once

class DrivePieCtrl : public CStatic
{
public:
    DrivePieCtrl(void);
    virtual ~DrivePieCtrl(void);

public:
    void setString(const xpr_tchar_t *aTotalSizeText, const xpr_tchar_t *aUsedSizeText, const xpr_tchar_t *aFreeSizeText);
    void setDrive(const xpr_tchar_t *aDrive);

protected:
    void drawLegends(CDC &aDC);
    void getDriveSpace(void);
    void drawDrivePie(CDC &aDC);
    xpr_sint_t scaleMetric(xpr_sint_t aValue) const;

protected:
    xpr::string  mTotalSizeText;
    xpr::string  mUsedSizeText;
    xpr::string  mFreeSizeText;

    xpr_tchar_t  mDrive[XPR_MAX_PATH + 1];
    xpr_uint64_t mUsedSize;
    xpr_uint64_t mTotalSize;
    xpr_uint64_t mFreeSize;

protected:
    DECLARE_MESSAGE_MAP()
    afx_msg void OnPaint(void);
    afx_msg void OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection);
    afx_msg LRESULT OnDpiChanged(WPARAM aWParam, LPARAM aLParam);
    afx_msg LRESULT OnDpiChangedAfterParent(WPARAM aWParam, LPARAM aLParam);
    afx_msg LRESULT OnThemeChanged(WPARAM aWParam, LPARAM aLParam);
};

#endif // __FXFILE_DRIVE_PIE_CTRL_H__
