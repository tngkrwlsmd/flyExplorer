//
// Copyright (c) 2001-2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#ifndef __FXFILE_BASE_DEF_H__
#define __FXFILE_BASE_DEF_H__ 1
#pragma once

//
// C++ standard libraries
//
#include <stack>
#include <queue>
#include <deque>
#include <vector>
#include <list>
#include <set>
#include <map>
#include <unordered_set>
#include <unordered_map>
#include <algorithm>
#include <string>
#include <cctype>
#include <memory>

#if defined(XPR_CFG_COMPILER_MSVC) && (XPR_CFG_COMPILER_VER > 1500)
namespace std
{
namespace tr1
{
using ::std::unordered_map;
using ::std::unordered_multimap;
using ::std::unordered_set;
} // namespace tr1
} // namespace std
#endif

#define FXFILE_STL_FOR_EACH(aIterator, aContainer) \
    for ((aIterator) = (aContainer).begin(); (aIterator) != (aContainer).end(); ++(aIterator))

#define FXFILE_STL_FOR_EACH_REVERSE(aIterator, aContainer) \
    for ((aIterator) = (aContainer).rbegin(); (aIterator) != (aContainer).rend(); ++(aIterator))

#define FXFILE_STL_IS_INDEXABLE(aIndex, aContainer) \
    ((0 <= ((xpr_sint_t)(aIndex))) && (((xpr_sint_t)(aIndex)) < ((xpr_sint_t)(aContainer).size())))

#if defined(XPR_CFG_OS_WINDOWS)
#include "def_win.h"
#else // not XPR_CFG_OS_WINDOWS
#error Please, support your OS. <def.h>
#endif // XPR_CFG_OS_WINDOWS

#endif // __FXFILE_BASE_DEF_H__
