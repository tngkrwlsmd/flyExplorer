//
// Copyright (c) 2026 flyExplorer contributors.
//
// Pure filename transformation helpers shared by production and native tests.
//

#ifndef __FXFILE_RENAME_TRANSFORM_CORE_H__
#define __FXFILE_RENAME_TRANSFORM_CORE_H__ 1
#pragma once

#include "xpr.h"

namespace fxfile
{
namespace cmd
{
namespace rename_core
{
void splitBaseFileNameAndExt(
    xpr_bool_t         aFolder,
    const xpr::string &aFileName,
    xpr::string       &aBaseFileName,
    xpr::string       &aFileExt);

void replaceText(
    xpr::string       &aName,
    const xpr::string &aFind,
    const xpr::string &aReplacement,
    xpr_sint_t         aRepeat,
    xpr_bool_t         aCaseSensitivity);

void insertAtFirst(xpr::string &aName, const xpr::string &aText);
void insertAtLast(xpr::string &aName, const xpr::string &aText);
void insertFromFirst(xpr::string &aName, xpr_sint_t aPos, const xpr::string &aText);
void insertFromLast(xpr::string &aName, xpr_sint_t aPos, const xpr::string &aText);

void deleteAtFirst(xpr::string &aName, xpr_sint_t aLength);
void deleteAtLast(xpr::string &aName, xpr_sint_t aLength);
void deleteFromFirst(xpr::string &aName, xpr_sint_t aPos, xpr_sint_t aLength);
void deleteFromLast(xpr::string &aName, xpr_sint_t aPos, xpr_sint_t aLength);

void toLower(xpr::string &aName);
void toUpper(xpr::string &aName);
void upperAtFirstChar(xpr::string &aName, const xpr::string &aSkipChars);
void upperAtFirstCharOnEveryWord(
    xpr::string       &aName,
    const xpr::string &aSkipChars);

void appendNumber(
    xpr::string &aName,
    xpr_uint_t   aIndex,
    xpr_sint_t   aStart,
    xpr_sint_t   aStep,
    xpr_bool_t   aZeroFilled,
    xpr_size_t   aDigit);
} // namespace rename_core
} // namespace cmd
} // namespace fxfile

#endif // __FXFILE_RENAME_TRANSFORM_CORE_H__
