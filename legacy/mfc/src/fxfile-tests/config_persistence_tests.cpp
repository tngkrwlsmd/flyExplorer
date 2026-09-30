//
// Copyright (c) 2026 flyExplorer contributors.
//

#include "functional_test_groups.h"

#include <windows.h>
#include <tchar.h>

#include "xpr.h"
#include "conf_file_ex.h"

namespace fxfile
{
namespace tests
{
namespace
{
xpr::string makeTempConfigPath(const xpr_tchar_t *aSuffix)
{
    xpr::string sTempDir;
    if (XPR_RCODE_IS_ERROR(xpr::FileSys::getTempDir(sTempDir)))
        return xpr::string();

    xpr_tchar_t sName[128] = {0};
    _stprintf_s(
        sName,
        sizeof(sName) / sizeof(sName[0]),
        XPR_STRING_LITERAL("flyExplorer-config-%lu-%lu-%s.ini"),
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

bool writeCorruptFile(const xpr::string &aPath)
{
    xpr::FileIo sFile;
    const xpr_sint_t sMode =
        xpr::FileIo::OpenModeCreate |
        xpr::FileIo::OpenModeTruncate |
        xpr::FileIo::OpenModeWriteOnly;

    if (XPR_RCODE_IS_ERROR(sFile.open(aPath, sMode)))
        return false;

    const xpr_uchar_t sBytes[] = {0x01, 0x02, 0x03};
    xpr_ssize_t sWritten = 0;
    const xpr_rcode_t sRcode = sFile.write(
        sBytes,
        sizeof(sBytes),
        &sWritten);
    sFile.close();

    return XPR_RCODE_IS_SUCCESS(sRcode) &&
           sWritten == static_cast<xpr_ssize_t>(sizeof(sBytes));
}
} // namespace

bool testConfigPersistenceContracts(void)
{
    const xpr::string sPath =
        makeTempConfigPath(XPR_STRING_LITERAL("roundtrip"));
    const xpr::string sMissingPath =
        makeTempConfigPath(XPR_STRING_LITERAL("missing"));
    const xpr::string sCorruptPath =
        makeTempConfigPath(XPR_STRING_LITERAL("corrupt"));

    if (sPath.empty() == XPR_TRUE ||
        sMissingPath.empty() == XPR_TRUE ||
        sCorruptPath.empty() == XPR_TRUE)
    {
        return false;
    }

    xpr::FileSys::remove(sPath);
    xpr::FileSys::remove(sMissingPath);
    xpr::FileSys::remove(sCorruptPath);

    base::ConfFileEx sWrite(sPath);
    sWrite.setComment(XPR_STRING_LITERAL("functional regression"));
    if (XPR_IS_FALSE(sWrite.setValueS(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("Empty"),
            XPR_STRING_LITERAL(""))) ||
        XPR_IS_FALSE(sWrite.setValueI(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("Integer"),
            -2147483647)) ||
        XPR_IS_FALSE(sWrite.setValueB(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("Enabled"),
            XPR_TRUE)) ||
        XPR_IS_FALSE(sWrite.setValueI64(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("Large"),
            static_cast<xpr_sint64_t>(9223372036854770000LL))))
    {
        return false;
    }

#if defined(XPR_CFG_UNICODE)
    if (XPR_IS_FALSE(sWrite.setValueS(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("Unicode"),
            L"\xD55C\xAE00 \xC124\xC815 \xAC12")))
    {
        return false;
    }
#else
    if (XPR_IS_FALSE(sWrite.setValueS(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("Unicode"),
            XPR_STRING_LITERAL("multibyte-value"))))
    {
        return false;
    }
#endif

    if (XPR_IS_FALSE(sWrite.setValueS(
            XPR_STRING_LITERAL("Second"),
            XPR_STRING_LITERAL("Order"),
            XPR_STRING_LITERAL("2"))) ||
        XPR_IS_FALSE(sWrite.save(xpr::CharSetUtf8)))
    {
        xpr::FileSys::remove(sPath);
        return false;
    }

    base::ConfFileEx sRead(sPath);
    if (XPR_IS_FALSE(sRead.load()))
    {
        xpr::FileSys::remove(sPath);
        return false;
    }

    if (_tcscmp(
            sRead.getValueS(
                XPR_STRING_LITERAL("General"),
                XPR_STRING_LITERAL("Empty"),
                XPR_STRING_LITERAL("fallback")),
            XPR_STRING_LITERAL("")) != 0 ||
        sRead.getValueI(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("Integer"),
            0) != -2147483647 ||
        XPR_IS_FALSE(sRead.getValueB(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("Enabled"),
            XPR_FALSE)) ||
        sRead.getValueI64(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("Large"),
            0) != XPR_SINT64_LITERAL(9223372036854770000))
    {
        xpr::FileSys::remove(sPath);
        return false;
    }

#if defined(XPR_CFG_UNICODE)
    if (_tcscmp(
            sRead.getValueS(
                XPR_STRING_LITERAL("General"),
                XPR_STRING_LITERAL("Unicode"),
                XPR_STRING_LITERAL("")),
            L"\xD55C\xAE00 \xC124\xC815 \xAC12") != 0)
    {
        xpr::FileSys::remove(sPath);
        return false;
    }
#endif

    if (_tcscmp(
            sRead.getValueS(
                XPR_STRING_LITERAL("General"),
                XPR_STRING_LITERAL("Missing"),
                XPR_STRING_LITERAL("fallback")),
            XPR_STRING_LITERAL("fallback")) != 0 ||
        sRead.getValueI(
            XPR_STRING_LITERAL("General"),
            XPR_STRING_LITERAL("MissingInt"),
            77) != 77 ||
        sRead.getSectionCount() != 2)
    {
        xpr::FileSys::remove(sPath);
        return false;
    }

    base::ConfFile::SectionIterator sSection = sRead.beginSection();
    if (sSection == sRead.endSection() ||
        _tcscmp(
            sRead.getSectionName(*sSection),
            XPR_STRING_LITERAL("General")) != 0)
    {
        xpr::FileSys::remove(sPath);
        return false;
    }
    ++sSection;
    if (sSection == sRead.endSection() ||
        _tcscmp(
            sRead.getSectionName(*sSection),
            XPR_STRING_LITERAL("Second")) != 0)
    {
        xpr::FileSys::remove(sPath);
        return false;
    }

    base::ConfFileEx sMissing(sMissingPath);
    if (XPR_IS_TRUE(sMissing.load()) ||
        sMissing.getValueI(
            XPR_STRING_LITERAL("Missing"),
            XPR_STRING_LITERAL("Value"),
            123) != 123)
    {
        xpr::FileSys::remove(sPath);
        return false;
    }

    if (!writeCorruptFile(sCorruptPath))
    {
        xpr::FileSys::remove(sPath);
        return false;
    }

    base::ConfFileEx sCorrupt(sCorruptPath);
    const bool sCorruptRejected = XPR_IS_FALSE(sCorrupt.load());

    const bool sCleanup =
        XPR_RCODE_IS_SUCCESS(xpr::FileSys::remove(sPath)) &&
        XPR_RCODE_IS_SUCCESS(xpr::FileSys::remove(sCorruptPath));

    return sCorruptRejected && sCleanup;
}
} // namespace tests
} // namespace fxfile
