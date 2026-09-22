//
// Copyright (c) 2026 flyExplorer contributors.
//
// Native functional regression tests for production filesystem primitives.
// All fixtures live below the OS temporary directory.
//

#include <windows.h>
#include <shellapi.h>
#include <tchar.h>

#include <cstring>
#include <iostream>
#include <vector>

#include "xpr.h"
#include "file_operation_core.h"
#include "shell_registry_core.h"
#include "cmd/rename_transform_core.h"
#include "functional_test_groups.h"
#include "crc32.h"
#include "md5.h"

namespace
{
const FILEOP_FLAGS kSilentFlags =
    FOF_NOCONFIRMATION |
    FOF_SILENT |
    FOF_NOERRORUI |
    FOF_NOCONFIRMMKDIR;

struct TestState
{
    xpr::string mRoot;
    int mPassed;
    int mFailed;

    TestState(void)
        : mPassed(0), mFailed(0)
    {
    }
};

xpr::string joinPath(const xpr::string &aParent, const xpr_tchar_t *aChild)
{
    xpr::string sPath(aParent);

    if (sPath.empty() == XPR_FALSE &&
        sPath[sPath.length() - 1] != XPR_FILE_SEPARATOR)
    {
        sPath += XPR_FILE_SEPARATOR;
    }

    sPath += aChild;
    return sPath;
}

std::vector<xpr_tchar_t> makeMultiString(const std::vector<xpr::string> &aPaths)
{
    std::vector<xpr_tchar_t> sResult;

    for (std::vector<xpr::string>::const_iterator sIt = aPaths.begin();
         sIt != aPaths.end();
         ++sIt)
    {
        const xpr_tchar_t *sPath = sIt->c_str();
        const xpr_size_t sLength = sIt->length();

        sResult.insert(sResult.end(), sPath, sPath + sLength);
        sResult.push_back(0);
    }

    sResult.push_back(0);
    return sResult;
}

bool writeBytes(const xpr::string &aPath, const std::vector<xpr_uchar_t> &aData)
{
    xpr::FileIo sFile;
    const xpr_sint_t sMode =
        xpr::FileIo::OpenModeCreate |
        xpr::FileIo::OpenModeTruncate |
        xpr::FileIo::OpenModeWriteOnly;

    if (XPR_RCODE_IS_ERROR(sFile.open(aPath, sMode)))
        return false;

    xpr_ssize_t sWritten = 0;
    xpr_rcode_t sRcode = XPR_RCODE_SUCCESS;

    if (aData.empty() == false)
    {
        sRcode = sFile.write(
            &aData[0],
            static_cast<xpr_size_t>(aData.size()),
            &sWritten);
    }

    sFile.close();

    return XPR_RCODE_IS_SUCCESS(sRcode) &&
           (aData.empty() ||
            sWritten == static_cast<xpr_ssize_t>(aData.size()));
}

bool readBytes(const xpr::string &aPath, std::vector<xpr_uchar_t> &aData)
{
    aData.clear();

    xpr::FileIo sFile;
    if (XPR_RCODE_IS_ERROR(sFile.open(aPath, xpr::FileIo::OpenModeReadOnly)))
        return false;

    const xpr_sint64_t sFileSize = sFile.getFileSize();
    if (sFileSize < 0)
    {
        sFile.close();
        return false;
    }

    aData.resize(static_cast<xpr_size_t>(sFileSize));

    xpr_ssize_t sRead = 0;
    xpr_rcode_t sRcode = XPR_RCODE_SUCCESS;

    if (aData.empty() == false)
    {
        sRcode = sFile.read(
            &aData[0],
            static_cast<xpr_size_t>(aData.size()),
            &sRead);
    }

    sFile.close();

    return XPR_RCODE_IS_SUCCESS(sRcode) &&
           (aData.empty() ||
            sRead == static_cast<xpr_ssize_t>(aData.size()));
}

bool equalFileContent(const xpr::string &aLeft, const xpr::string &aRight)
{
    std::vector<xpr_uchar_t> sLeft;
    std::vector<xpr_uchar_t> sRight;

    return readBytes(aLeft, sLeft) &&
           readBytes(aRight, sRight) &&
           sLeft == sRight;
}

int executeShellOperation(
    UINT aFunction,
    const std::vector<xpr::string> &aSources,
    const xpr::string *aTarget,
    FILEOP_FLAGS aExtraFlags,
    bool *aAborted)
{
    std::vector<xpr_tchar_t> sFrom = makeMultiString(aSources);
    std::vector<xpr_tchar_t> sTo;

    SHFILEOPSTRUCT sOperation = {};
    sOperation.wFunc = aFunction;
    sOperation.fFlags =
        static_cast<FILEOP_FLAGS>(kSilentFlags | aExtraFlags);
    sOperation.pFrom = &sFrom[0];

    if (aTarget != NULL)
    {
        std::vector<xpr::string> sTargets;
        sTargets.push_back(*aTarget);
        sTo = makeMultiString(sTargets);
        sOperation.pTo = &sTo[0];
    }

    const int sResult = fxfile::fileop::execute(&sOperation);

    if (aAborted != NULL)
        *aAborted = (sOperation.fAnyOperationsAborted != FALSE);

    return sResult;
}

bool removeTree(const xpr::string &aPath)
{
    if (xpr::FileSys::exist(aPath) == XPR_FALSE)
        return true;

    std::vector<xpr::string> sSources;
    sSources.push_back(aPath);

    bool sAborted = false;
    const int sResult = executeShellOperation(
        FO_DELETE,
        sSources,
        NULL,
        0,
        &sAborted);

    return sResult == 0 &&
           sAborted == false &&
           xpr::FileSys::exist(aPath) == XPR_FALSE;
}

void report(TestState &aState, const char *aName, bool aPassed)
{
    if (aPassed)
    {
        ++aState.mPassed;
        std::cout << "[PASS] " << aName << std::endl;
    }
    else
    {
        ++aState.mFailed;
        std::cerr << "[FAIL] " << aName << std::endl;
    }
}

bool prepareRoot(TestState &aState)
{
    xpr::string sTempDir;
    if (XPR_RCODE_IS_ERROR(xpr::FileSys::getTempDir(sTempDir)))
        return false;

    xpr_tchar_t sName[96] = {0};
    _stprintf_s(
        sName,
        sizeof(sName) / sizeof(sName[0]),
        XPR_STRING_LITERAL("flyExplorer-functional-%lu-%lu"),
        static_cast<unsigned long>(::GetCurrentProcessId()),
        static_cast<unsigned long>(::GetTickCount()));

    aState.mRoot = joinPath(sTempDir, sName);

    if (xpr::FileSys::exist(aState.mRoot) == XPR_TRUE &&
        removeTree(aState.mRoot) == false)
    {
        return false;
    }

    return XPR_RCODE_IS_SUCCESS(
        xpr::FileSys::mkdir_recursive(aState.mRoot));
}

bool testFileIoRoundTrip(TestState &aState)
{
    const xpr::string sPath =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("binary.dat"));
    const xpr_uchar_t sRaw[] =
        {0x00, 0x01, 0x7f, 0x80, 0xfe, 0xff, 0x42};
    const std::vector<xpr_uchar_t> sData(
        sRaw,
        sRaw + sizeof(sRaw));

    if (!writeBytes(sPath, sData))
        return false;

    std::vector<xpr_uchar_t> sRead;
    return readBytes(sPath, sRead) &&
           sRead == sData &&
           xpr::FileSys::getFileSize(sPath) == sData.size();
}

bool testEmptyFile(TestState &aState)
{
    const xpr::string sPath =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("empty file.txt"));
    const std::vector<xpr_uchar_t> sEmpty;

    return writeBytes(sPath, sEmpty) &&
           xpr::FileSys::exist(sPath) == XPR_TRUE &&
           xpr::FileSys::getFileSize(sPath) == 0;
}

bool testRecursiveDirectoryAndRename(TestState &aState)
{
    xpr::string sNested =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("one"));
    sNested = joinPath(sNested, XPR_STRING_LITERAL("two"));
    sNested = joinPath(sNested, XPR_STRING_LITERAL("three"));

    if (XPR_RCODE_IS_ERROR(xpr::FileSys::mkdir_recursive(sNested)))
        return false;

    const xpr::string sOldPath =
        joinPath(sNested, XPR_STRING_LITERAL("before.txt"));
    const xpr::string sNewPath =
        joinPath(sNested, XPR_STRING_LITERAL("after.txt"));
    const std::vector<xpr_uchar_t> sData(11, 0x35);

    if (!writeBytes(sOldPath, sData))
        return false;

    if (XPR_RCODE_IS_ERROR(
            xpr::FileSys::rename(sOldPath, sNewPath)))
    {
        return false;
    }

    std::vector<xpr_uchar_t> sRead;
    return xpr::FileSys::exist(sOldPath) == XPR_FALSE &&
           xpr::FileSys::exist(sNewPath) == XPR_TRUE &&
           readBytes(sNewPath, sRead) &&
           sRead == sData;
}

bool testUnicodeAndSpaceCopy(TestState &aState)
{
    const xpr::string sSourceDir =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("unicode source"));
    const xpr::string sTargetDir =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("unicode target"));

    if (XPR_RCODE_IS_ERROR(xpr::FileSys::mkdir(sSourceDir)) ||
        XPR_RCODE_IS_ERROR(xpr::FileSys::mkdir(sTargetDir)))
    {
        return false;
    }

#if defined(XPR_CFG_UNICODE)
    const xpr_tchar_t *sFileName =
        L"\xD55C\xAE00 \xD30C\xC77C \xBCF5\xC0AC.bin";
#else
    const xpr_tchar_t *sFileName =
        "multibyte-copy.bin";
#endif

    const xpr::string sSource = joinPath(sSourceDir, sFileName);
    const xpr::string sTarget = joinPath(sTargetDir, sFileName);
    const std::vector<xpr_uchar_t> sData(4097, 0xa5);

    if (!writeBytes(sSource, sData))
        return false;

    std::vector<xpr::string> sSources;
    sSources.push_back(sSource);

    bool sAborted = false;
    const int sResult = executeShellOperation(
        FO_COPY,
        sSources,
        &sTargetDir,
        0,
        &sAborted);

    return sResult == 0 &&
           sAborted == false &&
           xpr::FileSys::exist(sSource) == XPR_TRUE &&
           xpr::FileSys::exist(sTarget) == XPR_TRUE &&
           equalFileContent(sSource, sTarget);
}

bool testMove(TestState &aState)
{
    const xpr::string sSourceDir =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("move-source"));
    const xpr::string sTargetDir =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("move-target"));

    if (XPR_RCODE_IS_ERROR(xpr::FileSys::mkdir(sSourceDir)) ||
        XPR_RCODE_IS_ERROR(xpr::FileSys::mkdir(sTargetDir)))
    {
        return false;
    }

    const xpr::string sSource =
        joinPath(sSourceDir, XPR_STRING_LITERAL("move.bin"));
    const xpr::string sTarget =
        joinPath(sTargetDir, XPR_STRING_LITERAL("move.bin"));
    const std::vector<xpr_uchar_t> sData(2048, 0x5a);

    if (!writeBytes(sSource, sData))
        return false;

    std::vector<xpr::string> sSources;
    sSources.push_back(sSource);

    bool sAborted = false;
    const int sResult = executeShellOperation(
        FO_MOVE,
        sSources,
        &sTargetDir,
        0,
        &sAborted);

    std::vector<xpr_uchar_t> sMovedData;
    return sResult == 0 &&
           sAborted == false &&
           xpr::FileSys::exist(sSource) == XPR_FALSE &&
           readBytes(sTarget, sMovedData) &&
           sMovedData == sData;
}

bool testMultiFileCopy(TestState &aState)
{
    const xpr::string sSourceDir =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("multi-source"));
    const xpr::string sTargetDir =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("multi-target"));

    if (XPR_RCODE_IS_ERROR(xpr::FileSys::mkdir(sSourceDir)) ||
        XPR_RCODE_IS_ERROR(xpr::FileSys::mkdir(sTargetDir)))
    {
        return false;
    }

    const xpr::string sOne =
        joinPath(sSourceDir, XPR_STRING_LITERAL("one.bin"));
    const xpr::string sTwo =
        joinPath(sSourceDir, XPR_STRING_LITERAL("two.bin"));

    if (!writeBytes(sOne, std::vector<xpr_uchar_t>(17, 0x11)) ||
        !writeBytes(sTwo, std::vector<xpr_uchar_t>(31, 0x22)))
    {
        return false;
    }

    std::vector<xpr::string> sSources;
    sSources.push_back(sOne);
    sSources.push_back(sTwo);

    bool sAborted = false;
    const int sResult = executeShellOperation(
        FO_COPY,
        sSources,
        &sTargetDir,
        0,
        &sAborted);

    return sResult == 0 &&
           sAborted == false &&
           equalFileContent(
               sOne,
               joinPath(sTargetDir, XPR_STRING_LITERAL("one.bin"))) &&
           equalFileContent(
               sTwo,
               joinPath(sTargetDir, XPR_STRING_LITERAL("two.bin")));
}

int countDirectoryEntries(const xpr::string &aDirectory)
{
    xpr::string sPattern =
        joinPath(aDirectory, XPR_STRING_LITERAL("*"));

    WIN32_FIND_DATA sData = {};
    HANDLE sFind = ::FindFirstFile(sPattern.c_str(), &sData);
    if (sFind == INVALID_HANDLE_VALUE)
        return -1;

    int sCount = 0;
    do
    {
        if (_tcscmp(
                sData.cFileName,
                XPR_STRING_LITERAL(".")) != 0 &&
            _tcscmp(
                sData.cFileName,
                XPR_STRING_LITERAL("..")) != 0)
        {
            ++sCount;
        }
    } while (::FindNextFile(sFind, &sData));

    ::FindClose(sFind);
    return sCount;
}

bool testRenameOnCollision(TestState &aState)
{
    const xpr::string sDir =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("collision"));

    if (XPR_RCODE_IS_ERROR(xpr::FileSys::mkdir(sDir)))
        return false;

    const xpr::string sSource =
        joinPath(sDir, XPR_STRING_LITERAL("same.txt"));

    if (!writeBytes(sSource, std::vector<xpr_uchar_t>(9, 0x44)))
        return false;

    const int sBefore = countDirectoryEntries(sDir);

    std::vector<xpr::string> sSources;
    sSources.push_back(sSource);

    bool sAborted = false;
    const int sResult = executeShellOperation(
        FO_COPY,
        sSources,
        &sDir,
        FOF_RENAMEONCOLLISION,
        &sAborted);

    const int sAfter = countDirectoryEntries(sDir);

    return sResult == 0 &&
           sAborted == false &&
           sBefore == 1 &&
           sAfter == 2;
}

bool testReadOnlyFailure(TestState &aState)
{
    const xpr::string sPath =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("read-only.txt"));

    if (!writeBytes(sPath, std::vector<xpr_uchar_t>(5, 0x7a)))
        return false;

    if (::SetFileAttributes(
            sPath.c_str(),
            FILE_ATTRIBUTE_READONLY) == FALSE)
    {
        return false;
    }

    const xpr_rcode_t sRemoveResult =
        xpr::FileSys::remove(sPath);
    const bool sRejected =
        XPR_RCODE_IS_ERROR(sRemoveResult) &&
        xpr::FileSys::exist(sPath) == XPR_TRUE;

    ::SetFileAttributes(
        sPath.c_str(),
        FILE_ATTRIBUTE_NORMAL);

    return sRejected;
}

bool testMissingSourceFailure(TestState &aState)
{
    const xpr::string sMissing =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("missing-source.bin"));
    const xpr::string sTargetDir =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("missing-target"));

    if (XPR_RCODE_IS_ERROR(xpr::FileSys::mkdir(sTargetDir)))
        return false;

    std::vector<xpr::string> sSources;
    sSources.push_back(sMissing);

    bool sAborted = false;
    const int sResult = executeShellOperation(
        FO_COPY,
        sSources,
        &sTargetDir,
        0,
        &sAborted);

    return sResult != 0 || sAborted;
}

bool testLongLegacyPath(TestState &aState)
{
    xpr::string sName;
    for (int i = 0; i < 140; ++i)
        sName += XPR_STRING_LITERAL('a');
    sName += XPR_STRING_LITERAL(".bin");

    const xpr::string sPath =
        joinPath(aState.mRoot, sName.c_str());
    const std::vector<xpr_uchar_t> sData(257, 0x6c);

    std::vector<xpr_uchar_t> sRead;
    return sPath.length() < XPR_MAX_PATH &&
           writeBytes(sPath, sData) &&
           readBytes(sPath, sRead) &&
           sRead == sData;
}

bool testRenameTransformCore(void)
{
    using namespace fxfile::cmd::rename_core;

    xpr::string sBase;
    xpr::string sExt;

    splitBaseFileNameAndExt(
        XPR_FALSE,
        XPR_STRING_LITERAL("archive.tar.gz"),
        sBase,
        sExt);
    if (sBase != XPR_STRING_LITERAL("archive.tar") ||
        sExt != XPR_STRING_LITERAL(".gz"))
    {
        return false;
    }

    splitBaseFileNameAndExt(
        XPR_FALSE,
        XPR_STRING_LITERAL(".gitignore"),
        sBase,
        sExt);
    if (sBase != XPR_STRING_LITERAL("") ||
        sExt != XPR_STRING_LITERAL(".gitignore"))
    {
        return false;
    }

    splitBaseFileNameAndExt(
        XPR_TRUE,
        XPR_STRING_LITERAL("folder.name"),
        sBase,
        sExt);
    if (sBase != XPR_STRING_LITERAL("folder.name") ||
        sExt.empty() == XPR_FALSE)
    {
        return false;
    }

    xpr::string sName = XPR_STRING_LITERAL("One one ONE.txt");
    replaceText(
        sName,
        XPR_STRING_LITERAL("one"),
        XPR_STRING_LITERAL("X"),
        -1,
        XPR_FALSE);
    if (sName != XPR_STRING_LITERAL("X X X.txt"))
        return false;

    sName = XPR_STRING_LITERAL("abcdef");
    replaceText(
        sName,
        XPR_STRING_LITERAL("cd"),
        XPR_STRING_LITERAL("XY"),
        1,
        XPR_TRUE);
    if (sName != XPR_STRING_LITERAL("abXYef"))
        return false;

    sName = XPR_STRING_LITERAL("abc");
    insertAtFirst(sName, XPR_STRING_LITERAL("["));
    insertAtLast(sName, XPR_STRING_LITERAL("]"));
    insertFromFirst(sName, 2, XPR_STRING_LITERAL("-"));
    insertFromLast(sName, 1, XPR_STRING_LITERAL("+"));
    if (sName != XPR_STRING_LITERAL("[a-bc+]"))
        return false;

    sName = XPR_STRING_LITERAL("abcdef");
    deleteAtFirst(sName, 2);
    if (sName != XPR_STRING_LITERAL("cdef"))
        return false;

    sName = XPR_STRING_LITERAL("abcdef");
    deleteAtLast(sName, 2);
    if (sName != XPR_STRING_LITERAL("abcd"))
        return false;

    sName = XPR_STRING_LITERAL("abcdef");
    deleteFromFirst(sName, 2, 2);
    if (sName != XPR_STRING_LITERAL("abef"))
        return false;

    sName = XPR_STRING_LITERAL("abcdef");
    deleteFromLast(sName, 1, 2);
    if (sName != XPR_STRING_LITERAL("abcf"))
        return false;

    sName = XPR_STRING_LITERAL("__hELLo WORLD");
    upperAtFirstChar(sName, XPR_STRING_LITERAL("_"));
    if (sName != XPR_STRING_LITERAL("__Hello world"))
        return false;

    sName = XPR_STRING_LITERAL("hELLo-world TEST");
    upperAtFirstCharOnEveryWord(sName, XPR_STRING_LITERAL("-"));
    if (sName != XPR_STRING_LITERAL("Hello-World Test"))
        return false;

    sName = XPR_STRING_LITERAL("MiXeD");
    toLower(sName);
    if (sName != XPR_STRING_LITERAL("mixed"))
        return false;
    toUpper(sName);
    if (sName != XPR_STRING_LITERAL("MIXED"))
        return false;

    sName.clear();
    appendNumber(sName, 2, 1, 2, XPR_TRUE, 3);
    if (sName != XPR_STRING_LITERAL("005"))
        return false;

    sName = XPR_STRING_LITERAL("unchanged");
    replaceText(
        sName,
        XPR_STRING_LITERAL(""),
        XPR_STRING_LITERAL("x"),
        -1,
        XPR_TRUE);
    if (sName != XPR_STRING_LITERAL("unchanged"))
        return false;

    sName = XPR_STRING_LITERAL("abcd");
    insertFromFirst(sName, 99, XPR_STRING_LITERAL("X"));
    if (sName != XPR_STRING_LITERAL("abcdX"))
        return false;

    sName = XPR_STRING_LITERAL("abcd");
    insertFromLast(sName, -3, XPR_STRING_LITERAL("X"));
    if (sName != XPR_STRING_LITERAL("abcdX"))
        return false;

#if defined(XPR_CFG_UNICODE)
    sName = L"\xD55C\xAE00.TXT";
    toLower(sName);
    if (sName != L"\xD55C\xAE00.txt")
        return false;
#endif

    return true;
}

bool testHashKnownVectors(void)
{
    static const char kVector[] = "123456789";

    xpr_uint8_t sCrc[CRC32_DIGEST_SIZE] = {0};
    xpr_uint8_t sMd5[MD5_DIGEST_SIZE] = {0};

    CRC32(kVector, 9, sCrc);
    MD5(kVector, 9, sMd5);

    static const xpr_uint8_t kExpectedCrc[CRC32_DIGEST_SIZE] =
        {0xcb, 0xf4, 0x39, 0x26};
    static const xpr_uint8_t kExpectedMd5[MD5_DIGEST_SIZE] =
        {
            0x25, 0xf9, 0xe7, 0x94,
            0x32, 0x3b, 0x45, 0x38,
            0x85, 0xf5, 0x18, 0x1f,
            0x1b, 0x62, 0x4d, 0x0b
        };

    return memcmp(sCrc, kExpectedCrc, CRC32_DIGEST_SIZE) == 0 &&
           memcmp(sMd5, kExpectedMd5, MD5_DIGEST_SIZE) == 0;
}

bool testShellRegistryCommandContract(void)
{
#if defined(XPR_CFG_UNICODE)
    const xpr::string sModuleDir =
        L"C:\\Program Files\\\xD50C\xB77C\xC774\\fxfile";
#else
    const xpr::string sModuleDir =
        "C:\\Program Files\\flyExplorer\\fxfile";
#endif

    xpr::string sCommand;
    fxfile::shellreg::buildOpenCommand(sModuleDir, sCommand);

    xpr::string sExpected =
        XPR_STRING_LITERAL("\"");
    sExpected += sModuleDir;
    sExpected += XPR_STRING_LITERAL("\\fxfile.exe\" \"%1\"");

    xpr::string sMenuKey;
    fxfile::shellreg::buildMenuKey(
        XPR_STRING_LITERAL("open-with-"),
        XPR_STRING_LITERAL("-menu"),
        sMenuKey);

    xpr::string sCommandKey;
    fxfile::shellreg::buildCommandKey(
        XPR_STRING_LITERAL("open-with-"),
        XPR_STRING_LITERAL("-menu"),
        sCommandKey);

    return sCommand == sExpected &&
           sMenuKey == XPR_STRING_LITERAL("open-with-fxfile-menu") &&
           sCommandKey == XPR_STRING_LITERAL("open-with-fxfile-menu\\command");
}

bool testRecursiveDelete(TestState &aState)
{
    const xpr::string sTree =
        joinPath(aState.mRoot, XPR_STRING_LITERAL("delete-tree"));
    const xpr::string sNested =
        joinPath(sTree, XPR_STRING_LITERAL("nested"));

    if (XPR_RCODE_IS_ERROR(
            xpr::FileSys::mkdir_recursive(sNested)))
    {
        return false;
    }

    const xpr::string sFile =
        joinPath(sNested, XPR_STRING_LITERAL("payload.bin"));

    if (!writeBytes(sFile, std::vector<xpr_uchar_t>(64, 0x33)))
        return false;

    return removeTree(sTree);
}
} // namespace

int _tmain(void)
{
    TestState sState;

    if (!prepareRoot(sState))
    {
        std::cerr << "[FAIL] fixture setup" << std::endl;
        return 1;
    }

    report(sState, "FileIo binary round-trip", testFileIoRoundTrip(sState));
    report(sState, "empty file", testEmptyFile(sState));
    report(sState, "recursive mkdir + FileSys rename", testRecursiveDirectoryAndRename(sState));
    report(sState, "Unicode/space shell copy", testUnicodeAndSpaceCopy(sState));
    report(sState, "same-volume shell move", testMove(sState));
    report(sState, "multi-file shell copy", testMultiFileCopy(sState));
    report(sState, "rename-on-collision shell copy", testRenameOnCollision(sState));
    report(sState, "read-only FileSys remove failure", testReadOnlyFailure(sState));
    report(sState, "missing shell source failure", testMissingSourceFailure(sState));
    report(sState, "long legacy path FileIo round-trip", testLongLegacyPath(sState));
    report(sState, "rename/format transform core", testRenameTransformCore());
    report(sState, "pattern/path contracts", fxfile::tests::testPatternAndPathContracts());
    report(sState, "config persistence contracts", fxfile::tests::testConfigPersistenceContracts());
    report(sState, "updater version contracts", fxfile::tests::testUpdaterContracts());
    report(sState, "CRC32/MD5 known vectors", testHashKnownVectors());
    report(sState, "shell context-menu command contract", testShellRegistryCommandContract());
    report(sState, "recursive shell delete", testRecursiveDelete(sState));

    if (!removeTree(sState.mRoot))
    {
        ++sState.mFailed;
        std::cerr << "[FAIL] fixture cleanup" << std::endl;
    }
    else
    {
        std::cout << "[PASS] fixture cleanup" << std::endl;
    }

    std::cout << "Functional regression summary: "
              << sState.mPassed << " passed, "
              << sState.mFailed << " failed."
              << std::endl;

    return sState.mFailed == 0 ? 0 : 1;
}
