//
// Copyright (c) 2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "meta_data_file.h"

namespace fxfile
{
namespace upchecker
{
xpr_bool_t MetaDataFile::parseMetaFile(
    const xpr::string &aMetaFilePath,
    MetaData          &aMetaData)
{
    return fxfile::base::parseUpdateMetadataFile(
        aMetaFilePath,
        aMetaData);
}
} // namespace upchecker
} // namespace fxfile
