//
// Copyright (c) 2026 flyExplorer contributors.
//

#include "functional_test_groups.h"

#include "xpr.h"
#include "version_compare.h"
#include "upchecker_command.h"

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

#if defined(XPR_CFG_UNICODE)
    const xpr::string sConfDir =
        L"C:\\Users\\테스트 사용자\\flyExplorer conf";
    const xpr::string sExecutable =
        L"C:\\Program Files\\flyExplorer\\upchecker\\fxfile-upchecker.exe";
#else
    const xpr::string sConfDir =
        "C:\\Users\\test user\\flyExplorer conf";
    const xpr::string sExecutable =
        "C:\\Program Files\\flyExplorer\\upchecker\\fxfile-upchecker.exe";
#endif

    xpr::string sArgument;
    base::buildUpcheckerConfDirArgument(
        sConfDir,
        sArgument);

    xpr::string sExpectedArgument =
        XPR_STRING_LITERAL("--conf_dir=\"");
    sExpectedArgument += sConfDir;
    sExpectedArgument += XPR_STRING_LITERAL("\"");
    if (sArgument != sExpectedArgument)
        return false;

    xpr::string sCommand;
    base::buildUpcheckerStartupCommand(
        sExecutable,
        sConfDir,
        sCommand);

    xpr::string sExpectedCommand =
        XPR_STRING_LITERAL("\"");
    sExpectedCommand += sExecutable;
    sExpectedCommand += XPR_STRING_LITERAL("\" ");
    sExpectedCommand += sExpectedArgument;

    return sCommand == sExpectedCommand;
}
} // namespace tests
} // namespace fxfile
