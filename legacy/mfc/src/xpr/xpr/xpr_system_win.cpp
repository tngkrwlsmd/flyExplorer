//
// Copyright (c) 2012 Leon Lee author. All rights reserved.
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "xpr_system.h"
#include "xpr_rcode.h"
#include "xpr_char.h"

namespace xpr
{
namespace
{
SystemInfo gSystemInfo;
} // namespace anonymous

XPR_INLINE xpr_rcode_t initOsVer(xpr_uint_t &aOsVer);

XPR_DL_API xpr_rcode_t initSystemInfo(void)
{
    xpr_rcode_t sRcode = initOsVer(gSystemInfo.mOsVer);
    if (sRcode != XPR_RCODE_SUCCESS)
        return sRcode;

    return XPR_RCODE_SUCCESS;
}

// reference:
// http://msdn.microsoft.com/en-us/library/windows/desktop/ms724833(v=vs.85).aspx
XPR_INLINE xpr_rcode_t initOsVer(xpr_uint_t &aOsVer)
{
    // flyExplorer now supports Windows 10/11 only. They are newer than the
    // legacy version buckets represented by this compatibility enum.
    aOsVer = kOsVerWinHigher;
    return XPR_RCODE_SUCCESS;
}

XPR_DL_API SystemInfo *getSystemInfo(void)
{
    return &gSystemInfo;
}

XPR_DL_API xpr_uint_t getOsVer(void)
{
    return gSystemInfo.mOsVer;
}
} // namespace xpr
