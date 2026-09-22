//
// Copyright (c) 2026 flyExplorer contributors.
//
// UI-independent entry point for the legacy shell file-operation path.
//

#include "file_operation_core.h"

namespace fxfile
{
namespace fileop
{
int execute(SHFILEOPSTRUCT *aOperation)
{
    if (aOperation == NULL)
        return ERROR_INVALID_PARAMETER;

    return ::SHFileOperation(aOperation);
}
} // namespace fileop
} // namespace fxfile
