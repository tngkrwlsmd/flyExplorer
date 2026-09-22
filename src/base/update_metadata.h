//
// Copyright (c) 2026 flyExplorer contributors.
//
// Shared update metadata parser used by production upchecker and native tests.
//

#ifndef __FXFILE_BASE_UPDATE_METADATA_H__
#define __FXFILE_BASE_UPDATE_METADATA_H__ 1
#pragma once

#include "conf_file_ex.h"
#include "version_compare.h"

namespace fxfile
{
namespace base
{
struct UpdateMetadata
{
    xpr::string mProgram;
    xpr::string mVersion;
    xpr::string mNewUrl;
};

inline xpr_bool_t parseUpdateMetadataFile(
    const xpr::string &aMetaFilePath,
    UpdateMetadata    &aMetaData)
{
    ConfFileEx sConfFile(aMetaFilePath);
    sConfFile.setFlags(ConfFile::kFlagLock);

    if (XPR_IS_FALSE(sConfFile.load()))
        return XPR_FALSE;

    ConfFile::Section *sSection =
        sConfFile.findSection(XPR_STRING_LITERAL(""));
    if (XPR_IS_NULL(sSection))
        return XPR_FALSE;

    aMetaData.mProgram = sConfFile.getValueS(
        sSection, XPR_STRING_LITERAL("program"), XPR_STRING_LITERAL(""));
    aMetaData.mVersion = sConfFile.getValueS(
        sSection, XPR_STRING_LITERAL("version"), XPR_STRING_LITERAL(""));
    aMetaData.mNewUrl = sConfFile.getValueS(
        sSection, XPR_STRING_LITERAL("new_url"), XPR_STRING_LITERAL(""));

    Version sVersion;
    if (aMetaData.mProgram.empty() == XPR_TRUE ||
        aMetaData.mNewUrl.empty() == XPR_TRUE ||
        XPR_IS_FALSE(parseVersion(aMetaData.mVersion, sVersion)))
    {
        return XPR_FALSE;
    }

    return XPR_TRUE;
}
} // namespace base
} // namespace fxfile

#endif // __FXFILE_BASE_UPDATE_METADATA_H__
