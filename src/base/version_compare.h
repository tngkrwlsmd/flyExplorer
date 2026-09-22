//
// Copyright (c) 2026 flyExplorer contributors.
//

#ifndef __FXFILE_BASE_VERSION_COMPARE_H__
#define __FXFILE_BASE_VERSION_COMPARE_H__ 1
#pragma once

#include "xpr.h"

namespace fxfile
{
namespace base
{
struct Version
{
    Version(void)
        : mMajor(0), mMinor(0), mPatch(0)
    {
    }

    Version(xpr_sint_t aMajor, xpr_sint_t aMinor, xpr_sint_t aPatch)
        : mMajor(aMajor), mMinor(aMinor), mPatch(aPatch)
    {
    }

    xpr_sint_t mMajor;
    xpr_sint_t mMinor;
    xpr_sint_t mPatch;
};

xpr_bool_t parseVersion(const xpr::string &aVersion, Version &aResult);

// Returns < 0 when aLeft is older, 0 when equal, > 0 when newer.
xpr_sint_t compareVersion(const Version &aLeft, const Version &aRight);
} // namespace base
} // namespace fxfile

#endif // __FXFILE_BASE_VERSION_COMPARE_H__
