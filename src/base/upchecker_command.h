//
// Copyright (c) 2026 flyExplorer contributors.
//

#ifndef __FXFILE_BASE_UPCHECKER_COMMAND_H__
#define __FXFILE_BASE_UPCHECKER_COMMAND_H__ 1
#pragma once

#include "xpr.h"

namespace fxfile
{
namespace base
{
void buildUpcheckerConfDirArgument(
    const xpr::string &aConfDir,
    xpr::string       &aArgument);

void buildUpcheckerStartupCommand(
    const xpr::string &aExecutablePath,
    const xpr::string &aConfDir,
    xpr::string       &aCommand);
} // namespace base
} // namespace fxfile

#endif // __FXFILE_BASE_UPCHECKER_COMMAND_H__
