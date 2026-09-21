//
// Copyright (c) 2014 Leon Lee author. All rights reserved.
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#ifndef __XPR_REG_EXPR_H__
#define __XPR_REG_EXPR_H__ 1
#pragma once

#include "xpr_config.h"
#include <regex>

namespace xpr
{
#if defined(XPR_CFG_UNICODE)
typedef std::wregex  tregex;
typedef std::wcmatch tcmatch;
typedef std::wsmatch tsmatch;
#else
typedef std::regex  tregex;
typedef std::cmatch tcmatch;
typedef std::smatch tsmatch;
#endif
} // namespace xpr

#endif // __XPR_REG_EXPR_H__
