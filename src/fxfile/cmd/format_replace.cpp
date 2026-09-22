//
// Copyright (c) 2014 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "format_replace.h"
#include "rename_transform_core.h"
#include "xml.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace cmd
{
namespace
{
const xpr_sint_t kDefaultRepeat          = -1;
const xpr_bool_t kDefaultCaseSensitivity = XPR_TRUE;

const xpr_tchar_t kXmlFormatReplaceElement    [] = XPR_STRING_LITERAL("FormatReplace");
const xpr_tchar_t kXmlFindStringElement       [] = XPR_STRING_LITERAL("FindString");
const xpr_tchar_t kXmlReplaceStringElement    [] = XPR_STRING_LITERAL("ReplaceString");
const xpr_tchar_t kXmlRepeatAttribute         [] = XPR_STRING_LITERAL("Repeat");
const xpr_tchar_t kXmlCaseSensitivityAttribute[] = XPR_STRING_LITERAL("CaseSensitivity");
} // namespace anonymous

FormatReplace::FormatReplace(void)
    : mRepeat(kDefaultRepeat), mCaseSensitivity(kDefaultCaseSensitivity)
{
}

FormatReplace::FormatReplace(const xpr::string &aFindString, const xpr::string &aReplaceString)
    : mFindString(aFindString), mReplaceString(aReplaceString)
    , mRepeat(kDefaultRepeat), mCaseSensitivity(kDefaultCaseSensitivity)
{
}

FormatReplace::FormatReplace(const xpr::string &aFindString, const xpr::string &aReplaceString, xpr_sint_t aRepeat, xpr_bool_t aCaseSensitivity)
    : mFindString(aFindString), mReplaceString(aReplaceString)
    , mRepeat(aRepeat), mCaseSensitivity(aCaseSensitivity)
{
}

FormatReplace::~FormatReplace(void)
{
}

xpr_sint_t FormatReplace::getDefaultRepeat(void)
{
    return kDefaultRepeat;
}

xpr_bool_t FormatReplace::getDefaultCaseSensitivity(void)
{
    return kDefaultCaseSensitivity;
}

Format *FormatReplace::newObject(void)
{
    return new FormatReplace;
}

Format *FormatReplace::newClone(void) const
{
    Format *sNewFormat = new FormatReplace(mFindString, mReplaceString, mRepeat, mCaseSensitivity);

    return sNewFormat;
}

void FormatReplace::rename(RenameContext &aContext) const
{
    rename_core::replaceText(
        aContext.mNewFileName,
        mFindString,
        mReplaceString,
        mRepeat,
        mCaseSensitivity);
}

xpr_bool_t FormatReplace::canParseXml(const xpr::string &aElementName)
{
    return (aElementName.compare(kXmlFormatReplaceElement) == 0) ? XPR_TRUE : XPR_FALSE;
}

xpr_bool_t FormatReplace::parseXml(const base::XmlReader &aXmlReader, base::XmlReader::Element *aElement)
{
    XPR_ASSERT(aElement != XPR_NULL);

    xpr::string  sName;
    xpr::string  sValue;
    xpr_sint_t   sRepeat          = kDefaultRepeat;
    xpr_bool_t   sCaseSensitivity = kDefaultCaseSensitivity;
    xpr::string  sFindString;
    xpr::string  sReplaceString;

    base::XmlReader::Attribute *sAttribute = aXmlReader.getFirstAttribute(aElement);
    while (XPR_IS_NOT_NULL(sAttribute))
    {
        if (aXmlReader.getAttribute(sAttribute, sName, sValue) == XPR_FALSE)
        {
            return XPR_FALSE;
        }

        if (sName.compare(kXmlRepeatAttribute) == 0)
        {
            sRepeat = _ttoi(sValue.c_str());
        }
        else if (sName.compare(kXmlCaseSensitivityAttribute) == 0)
        {
            sCaseSensitivity = _ttoi(sValue.c_str());
        }

        sAttribute = aXmlReader.nextAttribute(sAttribute);
    }

    base::XmlReader::Element *sFormatElement = aXmlReader.childElement(aElement);
    while (XPR_IS_NOT_NULL(sFormatElement))
    {
        if (aXmlReader.getElementEntity(sFormatElement, sName, sValue) == XPR_FALSE)
        {
            return XPR_FALSE;
        }

        if (sName.compare(kXmlFindStringElement) == 0)
        {
            sFindString = sValue;
        }
        else if (sName.compare(kXmlReplaceStringElement) == 0)
        {
            sReplaceString = sValue;
        }

        sFormatElement = aXmlReader.nextElement(sFormatElement);
    }

    mFindString      = sFindString;
    mReplaceString   = sReplaceString;
    mRepeat          = sRepeat;
    mCaseSensitivity = sCaseSensitivity;

    return XPR_TRUE;
}

xpr_bool_t FormatReplace::write(base::XmlWriter &aXmlWriter) const
{
    xpr_bool_t sResult = XPR_FALSE;

    if (aXmlWriter.beginElement(kXmlFormatReplaceElement) == XPR_TRUE)
    {
        FXFILE_XML_WRITE_ATTRIBUTE_SINT32(aXmlWriter, kXmlRepeatAttribute,          mRepeat);
        FXFILE_XML_WRITE_ATTRIBUTE_SINT32(aXmlWriter, kXmlCaseSensitivityAttribute, mCaseSensitivity);

        FXFILE_XML_WRITE_ELEMENT_ENTITY_STRING(aXmlWriter, kXmlFindStringElement,    mFindString);
        FXFILE_XML_WRITE_ELEMENT_ENTITY_STRING(aXmlWriter, kXmlReplaceStringElement, mReplaceString);

        aXmlWriter.endElement();

        sResult = XPR_TRUE;
    }

    return sResult;
}
} // namespace cmd
} // namespace fxfile
