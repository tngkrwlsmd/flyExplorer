//
// Copyright (c) 2026 flyExplorer contributors.
//

#include "functional_test_groups.h"

#include "xpr.h"
#include "version_compare.h"

namespace fxfile
{
namespace tests
{
bool testUpdaterContracts(void)
{
    base::Version sVersion;

    if (XPR_IS_FALSE(
            base::parseVersion(
                XPR_STRING_LITERAL("2.0.4"),
                sVersion)) ||
        sVersion.mMajor != 2 ||
        sVersion.mMinor != 0 ||
        sVersion.mPatch != 4)
    {
        return false;
    }

    if (XPR_IS_TRUE(
            base::parseVersion(
                XPR_STRING_LITERAL(""),
                sVersion)) ||
        XPR_IS_TRUE(
            base::parseVersion(
                XPR_STRING_LITERAL("2.0"),
                sVersion)) ||
        XPR_IS_TRUE(
            base::parseVersion(
                XPR_STRING_LITERAL("2.0.4-beta"),
                sVersion)) ||
        XPR_IS_TRUE(
            base::parseVersion(
                XPR_STRING_LITERAL("2.0.4.1"),
                sVersion)) ||
        XPR_IS_TRUE(
            base::parseVersion(
                XPR_STRING_LITERAL("-1.0.0"),
                sVersion)) ||
        XPR_IS_TRUE(
            base::parseVersion(
                XPR_STRING_LITERAL("2.-1.0"),
                sVersion)))
    {
        return false;
    }

    const base::Version sCurrent(2, 0, 4);

    if (base::compareVersion(
            sCurrent,
            base::Version(2, 0, 4)) != 0)
    {
        return false;
    }

    if (base::compareVersion(
            sCurrent,
            base::Version(1, 99, 0)) <= 0)
    {
        return false;
    }

    if (base::compareVersion(
            sCurrent,
            base::Version(2, 0, 3)) <= 0)
    {
        return false;
    }

    if (base::compareVersion(
            sCurrent,
            base::Version(2, 0, 999)) >= 0)
    {
        return false;
    }

    if (base::compareVersion(
            sCurrent,
            base::Version(2, 1, 0)) >= 0)
    {
        return false;
    }

    if (base::compareVersion(
            base::Version(3, 0, 0),
            sCurrent) <= 0)
    {
        return false;
    }

    return true;
}
} // namespace tests
} // namespace fxfile
