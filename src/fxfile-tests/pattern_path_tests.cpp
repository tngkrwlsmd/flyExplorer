//
// Copyright (c) 2026 flyExplorer contributors.
//

#include "functional_test_groups.h"

#include "xpr.h"
#include "xpr_file_path.h"
#include "fnmatch.h"

namespace fxfile
{
namespace tests
{
bool testPatternAndPathContracts(void)
{
    if (fnmatch(
            XPR_STRING_LITERAL("*"),
            XPR_STRING_LITERAL("anything.txt"),
            0) != FNM_MATCH)
    {
        return false;
    }

    if (fnmatch(
            XPR_STRING_LITERAL("?.txt"),
            XPR_STRING_LITERAL("a.txt"),
            0) != FNM_MATCH)
    {
        return false;
    }

    if (fnmatch(
            XPR_STRING_LITERAL("*.TXT"),
            XPR_STRING_LITERAL("readme.txt"),
            FNM_CASEFOLD) != FNM_MATCH)
    {
        return false;
    }

    if (fnmatch(
            XPR_STRING_LITERAL("*.txt"),
            XPR_STRING_LITERAL("readme.md"),
            FNM_CASEFOLD) != FNM_NOMATCH)
    {
        return false;
    }

    if (fnmatch(
            XPR_STRING_LITERAL("file?.*"),
            XPR_STRING_LITERAL("file10.txt"),
            FNM_CASEFOLD) != FNM_NOMATCH)
    {
        return false;
    }

#if defined(XPR_CFG_UNICODE)
    if (fnmatch(
            L"\xD55C\xAE00*.txt",
            L"\xD55C\xAE00 \xD30C\xC77C.txt",
            FNM_CASEFOLD) != FNM_MATCH)
    {
        return false;
    }
#endif

    xpr::FilePath sPath(
        XPR_STRING_LITERAL("C:\\work\\docs\\file.tar.gz"));

    xpr::string sFileName;
    xpr::string sBaseName;
    xpr::string sExt;
    xpr::string sParent;

    if (XPR_IS_FALSE(sPath.getFileName(sFileName, XPR_TRUE)) ||
        sFileName != XPR_STRING_LITERAL("file.tar.gz"))
    {
        return false;
    }

    if (XPR_IS_FALSE(sPath.getFileName(sBaseName, XPR_FALSE)) ||
        sBaseName != XPR_STRING_LITERAL("file.tar"))
    {
        return false;
    }

    if (XPR_IS_FALSE(sPath.getExt(sExt)) ||
        sExt != XPR_STRING_LITERAL(".gz"))
    {
        return false;
    }

    if (XPR_IS_FALSE(sPath.getParentDir(sParent)) ||
        sParent != XPR_STRING_LITERAL("C:\\work\\docs"))
    {
        return false;
    }

    xpr::FilePath sNormalized(
        XPR_STRING_LITERAL("work\\.\\docs\\..\\file.txt"));
    if (XPR_IS_FALSE(sNormalized.normalize()) ||
        sNormalized.getPath() != XPR_STRING_LITERAL("work\\file.txt"))
    {
        return false;
    }

    xpr::FilePath sTrailing(
        XPR_STRING_LITERAL("C:\\work\\docs\\"));
    if (sTrailing.getPath() != XPR_STRING_LITERAL("C:\\work\\docs"))
        return false;

    xpr::FilePath sUnc(
        XPR_STRING_LITERAL("\\\\server\\share\\folder\\file.txt"));
    if (XPR_IS_FALSE(sUnc.isAbsolute()) ||
        XPR_IS_FALSE(sUnc.isNetwork()))
    {
        return false;
    }

    if (XPR_IS_FALSE(sUnc.getFileName(sFileName, XPR_TRUE)) ||
        sFileName != XPR_STRING_LITERAL("file.txt"))
    {
        return false;
    }

    xpr::FilePath sUri(
        XPR_STRING_LITERAL("file:///C:/Program Files/flyExplorer/fxfile.exe"));
    if (XPR_IS_FALSE(sUri.isAbsolute()) ||
        XPR_IS_FALSE(sUri.getFileName(sFileName, XPR_TRUE)) ||
        sFileName != XPR_STRING_LITERAL("fxfile.exe"))
    {
        return false;
    }

    xpr::string sInvalidChars;
    xpr::FilePath::getInvalidChars(sInvalidChars);
    if (sInvalidChars.find(XPR_STRING_LITERAL('*')) == xpr::string::npos ||
        sInvalidChars.find(XPR_STRING_LITERAL('?')) == xpr::string::npos)
    {
        return false;
    }

#if defined(XPR_CFG_UNICODE)
    xpr::FilePath sUnicode(
        L"C:\\work\\\xD55C\xAE00 \xD30C\xC77C.txt");
    if (XPR_IS_FALSE(sUnicode.getFileName(sFileName, XPR_TRUE)) ||
        sFileName != L"\xD55C\xAE00 \xD30C\xC77C.txt")
    {
        return false;
    }
#endif

    return true;
}
} // namespace tests
} // namespace fxfile
