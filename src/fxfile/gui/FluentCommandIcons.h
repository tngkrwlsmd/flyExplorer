//
// Copyright (c) 2026 flyExplorer contributors.
//
// Shared Microsoft Fluent command-icon runtime adapter.
//

#ifndef __FXFILE_GUI_FLUENT_COMMAND_ICONS_H__
#define __FXFILE_GUI_FLUENT_COMMAND_ICONS_H__ 1
#pragma once

namespace fxfile
{
namespace ui
{
class FluentCommandIcons
{
public:
    static xpr_bool_t hasCommand(xpr_uint_t aCommandId);
    static HICON createIcon(
        xpr_uint_t aCommandId,
        xpr_sint_t aCellSize,
        COLORREF aColor);
};
} // namespace ui
} // namespace fxfile

#endif // __FXFILE_GUI_FLUENT_COMMAND_ICONS_H__
