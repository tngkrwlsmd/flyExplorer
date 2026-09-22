//
// Copyright (c) 2026 flyExplorer contributors.
//
// UI-independent entry point for the legacy shell file-operation path.
//

#ifndef __FXFILE_FILE_OPERATION_CORE_H__
#define __FXFILE_FILE_OPERATION_CORE_H__ 1
#pragma once

#include <windows.h>
#include <shellapi.h>

namespace fxfile
{
namespace fileop
{
int execute(SHFILEOPSTRUCT *aOperation);
} // namespace fileop
} // namespace fxfile

#endif // __FXFILE_FILE_OPERATION_CORE_H__
