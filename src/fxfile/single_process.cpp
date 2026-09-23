//
// Copyright (c) 2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "single_process.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace
{
const xpr_tchar_t kSingleProcessMutexName[] = XPR_STRING_LITERAL("fxfile - single process");
const xpr_uint_t  WM_SINGLE_PROCESS         = ::RegisterWindowMessage(XPR_STRING_LITERAL("fxfile - single process"));
} // anonymous namespace

HANDLE SingleProcess::mSingleProcessMutex = XPR_NULL;

xpr_bool_t SingleProcess::check(void)
{
    // Presence detection does not need MUTEX_ALL_ACCESS. Requesting all access
    // can fail when an existing fxfile instance has a different integrity
    // level, which made the result depend on whether the new process was
    // elevated. SYNCHRONIZE is sufficient to open an existing mutex.
    ::SetLastError(ERROR_SUCCESS);
    HANDLE sSingleProcessMutex =
        ::OpenMutex(SYNCHRONIZE, XPR_FALSE, kSingleProcessMutexName);
    if (XPR_IS_NOT_NULL(sSingleProcessMutex))
    {
        ::CloseHandle(sSingleProcessMutex);
        return XPR_FALSE;
    }

    // If Windows denies even the minimal open, the named object still exists.
    // Treat it as an existing instance instead of incorrectly creating a
    // second process solely because the integrity levels differ.
    if (::GetLastError() == ERROR_ACCESS_DENIED)
        return XPR_FALSE;

    return XPR_TRUE;
}

void SingleProcess::lock(void)
{
    if (XPR_IS_NULL(mSingleProcessMutex))
    {
        mSingleProcessMutex = ::CreateMutex(XPR_NULL, XPR_FALSE, kSingleProcessMutexName);
    }
}

void SingleProcess::unlock(void)
{
    CLOSE_HANDLE(mSingleProcessMutex);
}

xpr_uint_t SingleProcess::getMsg(void)
{
    return WM_SINGLE_PROCESS;
}

void SingleProcess::postMsg(void)
{
    ::PostMessage(HWND_BROADCAST, WM_SINGLE_PROCESS, 0, 0);
}
} // namespace fxfile
