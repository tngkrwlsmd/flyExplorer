//
// Copyright (c) 2026 flyExplorer contributors.
//

#include "upchecker_command.h"

namespace fxfile
{
namespace base
{
void buildUpcheckerConfDirArgument(
    const xpr::string &aConfDir,
    xpr::string       &aArgument)
{
    aArgument  = XPR_STRING_LITERAL("--conf_dir=\"");
    aArgument += aConfDir;
    aArgument += XPR_STRING_LITERAL("\"");
}

void buildUpcheckerStartupCommand(
    const xpr::string &aExecutablePath,
    const xpr::string &aConfDir,
    xpr::string       &aCommand)
{
    xpr::string sArgument;
    buildUpcheckerConfDirArgument(aConfDir, sArgument);

    aCommand  = XPR_STRING_LITERAL("\"");
    aCommand += aExecutablePath;
    aCommand += XPR_STRING_LITERAL("\" ");
    aCommand += sArgument;
}
} // namespace base
} // namespace fxfile
