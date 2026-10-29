// M2.1 initial safe local-filesystem command boundary (no MFC/WinRT).
#pragma once
#include <windows.h>
#include <string>
namespace fxfile::filecommand {
enum class Kind { CreateFolder, RenameSelected, CreateTextFile, CreateMarkdownFile };
struct Request {
 Kind kind=Kind::CreateFolder;
 std::wstring parent; // exact accepted filesystem folder from isolated helper
 std::wstring source; // full selected native filesystem parsing path for rename
 std::wstring name;   // single leaf only, never a path or virtual Shell GUID
};
struct Result { DWORD error=ERROR_INVALID_PARAMETER; std::wstring target; };
bool validLeaf(std::wstring const& name) noexcept;
bool validTextDocumentLeaf(std::wstring const& name) noexcept;
bool validMarkdownDocumentLeaf(std::wstring const& name) noexcept;
Result execute(Request const& request) noexcept; // invoke off the UI thread
}
