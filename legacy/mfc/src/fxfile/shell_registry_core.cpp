//
// Copyright (c) 2026 flyExplorer contributors.
//

#include "shell_registry_core.h"

namespace fxfile
{
namespace shellreg
{
void buildMenuKey(
    const xpr::string &aPrefix,
    const xpr::string &aSuffix,
    xpr::string       &aKey)
{
    aKey  = aPrefix;
    aKey += XPR_STRING_LITERAL("fxfile");
    aKey += aSuffix;
}

void buildCommandKey(
    const xpr::string &aPrefix,
    const xpr::string &aSuffix,
    xpr::string       &aKey)
{
    buildMenuKey(aPrefix, aSuffix, aKey);
    aKey += XPR_STRING_LITERAL("\\command");
}

void buildOpenCommand(
    const xpr::string &aModuleDir,
    xpr::string       &aCommand)
{
    aCommand  = XPR_STRING_LITERAL("\"");
    aCommand += aModuleDir;
    aCommand += XPR_STRING_LITERAL("\\fxfile.exe\" \"%1\"");
}
} // namespace shellreg
} // namespace fxfile
