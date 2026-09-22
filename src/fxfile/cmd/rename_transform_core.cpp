//
// Copyright (c) 2026 flyExplorer contributors.
//

#include "rename_transform_core.h"

namespace fxfile
{
namespace cmd
{
namespace rename_core
{
void splitBaseFileNameAndExt(
    xpr_bool_t         aFolder,
    const xpr::string &aFileName,
    xpr::string       &aBaseFileName,
    xpr::string       &aFileExt)
{
    if (XPR_IS_TRUE(aFolder))
    {
        aBaseFileName = aFileName;
        aFileExt.clear();
        return;
    }

    const xpr_size_t sOffset = aFileName.rfind(XPR_FILE_EXT_SEPARATOR);
    if (sOffset != xpr::string::npos)
    {
        aBaseFileName = aFileName.substr(0, sOffset);
        aFileExt = aFileName.substr(sOffset);
    }
    else
    {
        aBaseFileName = aFileName;
        aFileExt.clear();
    }
}

void replaceText(
    xpr::string       &aName,
    const xpr::string &aFind,
    const xpr::string &aReplacement,
    xpr_sint_t         aRepeat,
    xpr_bool_t         aCaseSensitivity)
{
    if (aFind.empty() == XPR_TRUE || aRepeat == 0)
        return;

    xpr::string sOld(aName);
    xpr::string sFind(aFind);
    xpr_sint_t sRepeat = aRepeat;
    xpr_size_t sOffset = 0;
    const xpr_sint_t sLenDiff =
        static_cast<xpr_sint_t>(aReplacement.length()) -
        static_cast<xpr_sint_t>(aFind.length());

    if (sRepeat < 0)
        sRepeat = XPR_MAX_PATH;

    if (XPR_IS_FALSE(aCaseSensitivity))
    {
        sOld.upper_case();
        sFind.upper_case();
    }

    for (xpr_sint_t i = 0; i < sRepeat; ++i)
    {
        const xpr_size_t sFindPos = sOld.find(sFind, sOffset);
        if (sFindPos == xpr::string::npos)
            break;

        aName.erase(sFindPos + i * sLenDiff, aFind.length());
        aName.insert(sFindPos + i * sLenDiff, aReplacement);
        sOffset = sFindPos + sFind.length();
    }
}

void insertAtFirst(xpr::string &aName, const xpr::string &aText)
{
    aName.insert(0, aText);
}

void insertAtLast(xpr::string &aName, const xpr::string &aText)
{
    aName += aText;
}

void insertFromFirst(
    xpr::string       &aName,
    xpr_sint_t         aPos,
    const xpr::string &aText)
{
    xpr_sint_t sOffset = (aPos < 0) ? 0 : aPos;
    const xpr_sint_t sLength =
        static_cast<xpr_sint_t>(aName.length());

    if (sOffset > sLength)
        sOffset = sLength;

    aName.insert(static_cast<xpr_size_t>(sOffset), aText);
}

void insertFromLast(
    xpr::string       &aName,
    xpr_sint_t         aPos,
    const xpr::string &aText)
{
    const xpr_sint_t sLength =
        static_cast<xpr_sint_t>(aName.length());
    xpr_sint_t sPos = (aPos < 0) ? 0 : aPos;

    if (sPos > sLength)
        sPos = sLength;

    const xpr_sint_t sOffset = sLength - sPos;
    aName.insert(static_cast<xpr_size_t>(sOffset), aText);
}

void deleteAtFirst(xpr::string &aName, xpr_sint_t aLength)
{
    xpr_sint_t sLength = aLength;
    const xpr_sint_t sNameLength =
        static_cast<xpr_sint_t>(aName.length());

    if (sLength <= 0)
        return;

    if (sNameLength < sLength)
        sLength = sNameLength;

    aName.erase(0, sLength);
}

void deleteAtLast(xpr::string &aName, xpr_sint_t aLength)
{
    xpr_sint_t sLength = aLength;
    const xpr_sint_t sNameLength =
        static_cast<xpr_sint_t>(aName.length());

    if (sLength <= 0)
        return;

    if (sNameLength < sLength)
        sLength = sNameLength;

    const xpr_sint_t sOffset = sNameLength - sLength;
    aName.erase(sOffset, sLength);
}

void deleteFromFirst(
    xpr::string &aName,
    xpr_sint_t   aPos,
    xpr_sint_t   aLength)
{
    xpr_sint_t sOffset = aPos;
    xpr_sint_t sLength = aLength;
    const xpr_sint_t sNameLength =
        static_cast<xpr_sint_t>(aName.length());

    if (sLength <= 0 || sOffset < 0)
        return;

    if (sOffset > sNameLength)
        sOffset = sNameLength;

    if ((sOffset + sLength) > sNameLength)
        sLength = sNameLength - sOffset;

    aName.erase(sOffset, sLength);
}

void deleteFromLast(
    xpr::string &aName,
    xpr_sint_t   aPos,
    xpr_sint_t   aLength)
{
    xpr_sint_t sOffset = aPos;
    xpr_sint_t sLength = aLength;
    const xpr_sint_t sNameLength =
        static_cast<xpr_sint_t>(aName.length());

    if (sLength <= 0 || sOffset < 0)
        return;

    if (sOffset > sNameLength)
        sOffset = sNameLength;

    if ((sOffset + sLength) > sNameLength)
        sLength = sNameLength - sOffset;

    sOffset = sNameLength - sLength - sOffset;
    aName.erase(sOffset, sLength);
}

void toLower(xpr::string &aName)
{
    aName.lower_case();
}

void toUpper(xpr::string &aName)
{
    aName.upper_case();
}

void upperAtFirstChar(
    xpr::string       &aName,
    const xpr::string &aSkipChars)
{
    if (aName.empty() == XPR_TRUE)
        return;

    aName.lower_case();

    const xpr_size_t sOffset =
        aName.find_first_not_of(aSkipChars, 0);
    if (sOffset == xpr::string::npos || aName.length() == sOffset)
        return;

    xpr::string sChar(1, aName[sOffset]);
    sChar.upper_case();
    aName.replace(sOffset, 1, sChar);
}

void upperAtFirstCharOnEveryWord(
    xpr::string       &aName,
    const xpr::string &aSkipChars)
{
    if (aName.empty() == XPR_TRUE)
        return;

    xpr_size_t sOffset = 0;
    xpr::string sSkipChars(aSkipChars);
    xpr::string sChar;

    sSkipChars += XPR_MBCS_STRING_LITERAL(' ');
    aName.lower_case();

    while (true)
    {
        sOffset = aName.find_first_not_of(sSkipChars, sOffset);
        if (sOffset == xpr::string::npos)
            break;

        sChar = aName[sOffset];
        sChar.upper_case();
        aName.replace(sOffset, 1, sChar);

        sOffset = aName.find_first_of(sSkipChars, sOffset);
        if (sOffset == xpr::string::npos)
            break;
    }
}

void appendNumber(
    xpr::string &aName,
    xpr_uint_t   aIndex,
    xpr_sint_t   aStart,
    xpr_sint_t   aStep,
    xpr_bool_t   aZeroFilled,
    xpr_size_t   aDigit)
{
    const xpr_sint_t sNumber =
        aStart + static_cast<xpr_sint_t>(aIndex) * aStep;

    xpr::string sStringFormat;
    if (XPR_IS_TRUE(aZeroFilled))
        sStringFormat.format(XPR_STRING_LITERAL("%%0%dd"), aDigit);
    else
        sStringFormat.format(XPR_STRING_LITERAL("%%d"));

    aName.append_format(sStringFormat.c_str(), sNumber);
}
} // namespace rename_core
} // namespace cmd
} // namespace fxfile
