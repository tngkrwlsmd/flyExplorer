//
// Copyright (c) 2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "shell_registry.h"
#include "shell_registry_core.h"

#include "winapi_ex.h"

#include <atlbase.h> // for CRegKey

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace
{
static const xpr_tchar_t kKeyName[] = XPR_STRING_LITERAL("Folder\\Shell");
} // namespace anonymous

void ShellRegistry::registerShell(void)
{
    CRegKey sRegKey;
    if (sRegKey.Open(HKEY_CLASSES_ROOT, kKeyName) == ERROR_SUCCESS)
    {
        // HKEY_CLASSES_ROOT\Folder\shell\open with fxfile\command
        // (default) : "C:\Program Files\fxfile\fxfile.exe" "%1"

        xpr::string sModuleDir;
        GetModuleDir(sModuleDir);

        xpr::string sCmd;
        shellreg::buildOpenCommand(sModuleDir, sCmd);

        xpr::string sKey;
        shellreg::buildCommandKey(
            gApp.loadString(XPR_STRING_LITERAL("shell_menu.open_with_fxfile.prefix")),
            gApp.loadString(XPR_STRING_LITERAL("shell_menu.open_with_fxfile.suffix")),
            sKey);

        sRegKey.SetKeyValue(sKey.c_str(), sCmd.c_str());
    }

    sRegKey.Close();
}

void ShellRegistry::unregisterShell(void)
{
    CRegKey sRegKey;
    if (sRegKey.Open(HKEY_CLASSES_ROOT, kKeyName) == ERROR_SUCCESS)
    {
        xpr::string sKey;
        shellreg::buildMenuKey(
            gApp.loadString(XPR_STRING_LITERAL("shell_menu.open_with_fxfile.prefix")),
            gApp.loadString(XPR_STRING_LITERAL("shell_menu.open_with_fxfile.suffix")),
            sKey);

        sRegKey.RecurseDeleteKey(sKey.c_str());
    }

    sRegKey.Close();
}
} // namespace fxfile
