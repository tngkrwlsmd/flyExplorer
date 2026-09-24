//
// Copyright (c) 2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "about_tab_info_dlg.h"

#include "user_env.h"
#include "winapi_ex.h"

#include "app_ver.h"
#include "option.h"
#include "resource.h"

#include "gfl/libgfl.h"

#include <atlbase.h>


#ifdef _DEBUG
#define new DEBUG_NEW
#endif

using namespace fxfile;
using namespace fxfile::base;

namespace fxfile
{
namespace cmd
{
AboutTabInfoDlg::AboutTabInfoDlg(void)
    : super(IDD_ABOUT_TAB_ABOUT)
{
}

void AboutTabInfoDlg::DoDataExchange(CDataExchange* pDX)
{
    super::DoDataExchange(pDX);
}

BEGIN_MESSAGE_MAP(AboutTabInfoDlg, super)
    ON_BN_CLICKED(IDC_ABOUT_REPORT,   OnReport)
    ON_BN_CLICKED(IDC_ABOUT_SYSTEM,   OnSystem)
END_MESSAGE_MAP()

xpr_bool_t AboutTabInfoDlg::OnInitDialog(void) 
{
    super::OnInitDialog();

    UserEnv &sUserEnv = UserEnv::instance();

    // set program name and version
    xpr::string sProgram;
    xpr_tchar_t sVersion[0xff] = {0};

    getFullAppVer(sVersion);
    sProgram.format(XPR_STRING_LITERAL("fxfile %s"), sVersion);

    SetDlgItemText(IDC_ABOUT_PROGRAM, sProgram.c_str());

    // set windows version
    xpr::string sWindows;
    sWindows.format(XPR_STRING_LITERAL("Microsoft (R) Windows %d.%d build %d"), 
        LOWORD(sUserEnv.mOSVerInfo.dwMajorVersion),
        LOWORD(sUserEnv.mOSVerInfo.dwMinorVersion),
        LOWORD(sUserEnv.mOSVerInfo.dwBuildNumber));
    SetDlgItemText(IDC_ABOUT_WINDOWS, sWindows.c_str());

    SetWindowText(gApp.loadString(XPR_STRING_LITERAL("popup.about.tab.info.title")));
    SetDlgItemText(IDC_ABOUT_LABEL_ACCEPT, gApp.loadString(XPR_STRING_LITERAL("popup.about.tab.info.label.accept")));
    SetDlgItemText(IDOK,                   gApp.loadString(XPR_STRING_LITERAL("popup.common.button.ok")));
    SetDlgItemText(IDC_ABOUT_SYSTEM,       gApp.loadString(XPR_STRING_LITERAL("popup.about.tab.info.button.system_info")));
    SetDlgItemText(IDC_ABOUT_REPORT,       gApp.loadString(XPR_STRING_LITERAL("popup.about.tab.info.button.report")));
    return XPR_TRUE;
}

void AboutTabInfoDlg::OnReport(void) 
{
    xpr_tchar_t sPath[XPR_MAX_PATH + 1] = {0};
    GetModulePath(sPath, XPR_MAX_PATH);

    xpr_bool_t sResult = XPR_FALSE;
    xpr_tchar_t sVersion[0xff];
    void *sBlock = new xpr_char_t[5120];
    if (GetFileVersionInfo(sPath, 0, 5120, sBlock))
    {
        struct LangAndCodePage
        {
            WORD wLanguage;
            WORD wCodePage;
        } *sTranslate;

        xpr_uint_t sTranslateLength = 0;
        if (VerQueryValue(sBlock,
                          XPR_STRING_LITERAL("\\VarFileInfo\\Translation"),
                          (LPVOID*)&sTranslate,
                          &sTranslateLength))
        {
            xpr_tchar_t sSubBlock[0xff] = {0};
            void *sBuffer = XPR_NULL;
            xpr_uint_t sBytes = 0;
            xpr_sint_t i, sCount;

            sCount = sTranslateLength / sizeof(LangAndCodePage);
            for (i = 0; i < sCount; ++i)
            {
                _stprintf(sSubBlock, XPR_STRING_LITERAL("\\StringFileInfo\\%04x%04x\\FileVersion"),
                    sTranslate[i].wLanguage, sTranslate[i].wCodePage);

                if (VerQueryValue(sBlock, sSubBlock, &sBuffer, &sBytes))
                {
                    _tcscpy(sVersion, (xpr_tchar_t *)sBuffer);
                    sResult = XPR_TRUE;
                    break;
                }
            }
        }
    }

    XPR_SAFE_DELETE_ARRAY(sBlock);

    if (sResult == XPR_FALSE)
    {
        getAppVer(sVersion);
    }

    xpr_tchar_t sUrl[XPR_MAX_URL_LENGTH+50] = {0};
    _stprintf(sUrl, XPR_STRING_LITERAL("mailto:flychk@flychk.com?subject=fxfile v%s - report an issue"), sVersion);
    ShellExecute(XPR_NULL, XPR_STRING_LITERAL("open"), sUrl, XPR_NULL, XPR_NULL, 0);
}

void AboutTabInfoDlg::OnSystem(void)
{
    ShellExecute(XPR_NULL, XPR_STRING_LITERAL("open"), XPR_STRING_LITERAL("msinfo32.exe"), XPR_NULL, XPR_NULL, 0);
}

} // namespace cmd
} // namespace fxfile
