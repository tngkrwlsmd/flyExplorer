//
// Copyright (c) 2026 flyExplorer contributors.
//
// Pure shell-registration string contracts shared by production and tests.
//

#ifndef __FXFILE_SHELL_REGISTRY_CORE_H__
#define __FXFILE_SHELL_REGISTRY_CORE_H__ 1
#pragma once

#include "xpr_string.h"

namespace fxfile
{
namespace shellreg
{
void buildMenuKey(
    const xpr::string &aPrefix,
    const xpr::string &aSuffix,
    xpr::string       &aKey);

void buildCommandKey(
    const xpr::string &aPrefix,
    const xpr::string &aSuffix,
    xpr::string       &aKey);

void buildOpenCommand(
    const xpr::string &aModuleDir,
    xpr::string       &aCommand);
} // namespace shellreg
} // namespace fxfile

#endif // __FXFILE_SHELL_REGISTRY_CORE_H__
