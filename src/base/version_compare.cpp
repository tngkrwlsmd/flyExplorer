//
// Copyright (c) 2026 flyExplorer contributors.
//

#include "version_compare.h"

namespace fxfile
{
namespace base
{
xpr_bool_t parseVersion(const xpr::string &aVersion, Version &aResult)
{
    xpr_sint_t sMajor = 0;
    xpr_sint_t sMinor = 0;
    xpr_sint_t sPatch = 0;
    xpr_tchar_t sExtra = 0;

    const xpr_sint_t sCount = _stscanf_s(
        aVersion.c_str(),
        XPR_STRING_LITERAL("%d.%d.%d%c"),
        &sMajor,
        &sMinor,
        &sPatch,
        &sExtra,
        1);

    if (sCount != 3 ||
        sMajor < 0 ||
        sMinor < 0 ||
        sPatch < 0)
    {
        return XPR_FALSE;
    }

    aResult.mMajor = sMajor;
    aResult.mMinor = sMinor;
    aResult.mPatch = sPatch;
    return XPR_TRUE;
}

xpr_sint_t compareVersion(const Version &aLeft, const Version &aRight)
{
    if (aLeft.mMajor != aRight.mMajor)
        return (aLeft.mMajor < aRight.mMajor) ? -1 : 1;

    if (aLeft.mMinor != aRight.mMinor)
        return (aLeft.mMinor < aRight.mMinor) ? -1 : 1;

    if (aLeft.mPatch != aRight.mPatch)
        return (aLeft.mPatch < aRight.mPatch) ? -1 : 1;

    return 0;
}
} // namespace base
} // namespace fxfile
