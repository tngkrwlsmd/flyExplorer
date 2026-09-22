//
// Copyright (c) 2026 flyExplorer contributors.
//

#include <windows.h>
#include <tchar.h>

#include "functional_test_groups.h"

#include "xpr.h"
#include "version_compare.h"
#include "upchecker_command.h"
#include "update_metadata.h"
#include "conf_file_ex.h"

namespace fxfile
{
namespace tests
{
namespace
{
xpr::string makeUpdateMetaPath(const xpr_tchar_t *aSuffix)
{
    xpr::string sTempDir;
    if (XPR_RCODE_IS_ERROR(xpr::FileSys::getTempDir(sTempDir)))
        return xpr::string();

    xpr_tchar_t sName[128] = {0};
    _stprintf_s(
        sName,
        sizeof(sName) / sizeof(sName[0]),
        XPR_STRING_LITERAL("flyExplorer-update-%lu-%lu-%s.meta"),
        static_cast<unsigned long>(::GetCurrentProcessId()),
        static_cast<unsigned long>(::GetTickCount()),
        aSuffix);

    if (sTempDir.empty() == XPR_FALSE &&
        sTempDir[sTempDir.length() - 1] != XPR_FILE_SEPARATOR)
    {
        sTempDir += XPR_FILE_SEPARATOR;
    }

    sTempDir += sName;
    return sTempDir;
}

xpr_bool_t writeUpdateMeta(
    const xpr::string &aPath,
    const xpr_tchar_t *aProgram,
    const xpr_tchar_t *aVersion,
    const xpr_tchar_t *aNewUrl)
{
    base::ConfFileEx sConf(aPath);

    if (XPR_IS_NOT_NULL(aProgram) &&
        XPR_IS_FALSE(sConf.setValueS(
            XPR_STRING_LITERAL(""),
            XPR_STRING_LITERAL("program"),
            aProgram)))
    {
        return XPR_FALSE;
    }

    if (XPR_IS_NOT_NULL(aVersion) &&
        XPR_IS_FALSE(sConf.setValueS(
            XPR_STRING_LITERAL(""),
            XPR_STRING_LITERAL("version"),
            aVersion)))
    {
        return XPR_FALSE;
    }

    if (XPR_IS_NOT_NULL(aNewUrl) &&
        XPR_IS_FALSE(sConf.setValueS(
            XPR_STRING_LITERAL(""),
            XPR_STRING_LITERAL("new_url"),
            aNewUrl)))
    {
        return XPR_FALSE;
    }

    return sConf.save(xpr::CharSetUtf8);
}

bool testUpdateMetadataParser(void)
{
    const xpr::string sValid =
        makeUpdateMetaPath(XPR_STRING_LITERAL("valid"));
    const xpr::string sMalformed =
        makeUpdateMetaPath(XPR_STRING_LITERAL("malformed"));
    const xpr::string sMissing =
        makeUpdateMetaPath(XPR_STRING_LITERAL("missing"));
    const xpr::string sAbsent =
        makeUpdateMetaPath(XPR_STRING_LITERAL("absent"));

    if (sValid.empty() == XPR_TRUE ||
        sMalformed.empty() == XPR_TRUE ||
        sMissing.empty() == XPR_TRUE ||
        sAbsent.empty() == XPR_TRUE)
    {
        return false;
    }

    xpr::FileSys::remove(sValid);
    xpr::FileSys::remove(sMalformed);
    xpr::FileSys::remove(sMissing);
    xpr::FileSys::remove(sAbsent);

#if defined(XPR_CFG_UNICODE)
    const xpr_tchar_t *sUrl =
        L"https://example.invalid/\xC5C5\xB370\xC774\xD2B8/\xD30C\xC77C.zip";
#else
    const xpr_tchar_t *sUrl =
        "https://example.invalid/update/file.zip";
#endif

    bool sPassed = false;
    do
    {
        if (XPR_IS_FALSE(writeUpdateMeta(
                sValid,
                XPR_STRING_LITERAL("fxfile"),
                XPR_STRING_LITERAL("2.0.4"),
                sUrl)))
        {
            break;
        }

        base::UpdateMetadata sMetadata;
        if (XPR_IS_FALSE(base::parseUpdateMetadataFile(
                sValid,
                sMetadata)) ||
            sMetadata.mProgram != XPR_STRING_LITERAL("fxfile") ||
            sMetadata.mVersion != XPR_STRING_LITERAL("2.0.4") ||
            sMetadata.mNewUrl != sUrl)
        {
            break;
        }

        if (XPR_IS_FALSE(writeUpdateMeta(
                sMalformed,
                XPR_STRING_LITERAL("fxfile"),
                XPR_STRING_LITERAL("2.0.4-beta"),
                sUrl)) ||
            XPR_IS_TRUE(base::parseUpdateMetadataFile(
                sMalformed,
                sMetadata)))
        {
            break;
        }

        if (XPR_IS_FALSE(writeUpdateMeta(
                sMissing,
                XPR_STRING_LITERAL("fxfile"),
                XPR_STRING_LITERAL("2.0.4"),
                XPR_NULL)) ||
            XPR_IS_TRUE(base::parseUpdateMetadataFile(
                sMissing,
                sMetadata)))
        {
            break;
        }

        if (XPR_IS_TRUE(base::parseUpdateMetadataFile(
                sAbsent,
                sMetadata)))
        {
            break;
        }

        sPassed = true;
    } while (false);

    xpr::FileSys::remove(sValid);
    xpr::FileSys::remove(sMalformed);
    xpr::FileSys::remove(sMissing);

    return sPassed;
}
} // namespace

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

    return sCommand == sExpectedCommand &&
           testUpdateMetadataParser();
}
} // namespace tests
} // namespace fxfile
