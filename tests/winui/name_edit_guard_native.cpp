// Native-only regression: no WinUI, filesystem writes or global state.
#include "../../src/base/name_edit_guard.h"
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <string>

struct Context {
 std::uint64_t windowTabIdentity=77;
 int side=0;
 std::size_t tab=1;
 std::uint64_t route=55;
 std::wstring visibleFolder=L"C:\\test-owned\\folder";
 std::wstring visibleShellFolder=L"shell:owned";
};

int main() {
 int passed=0,failed=0;
 auto check=[&](bool okay,char const* name) {
  std::printf("NAME_EDIT_%s %s\n",okay?"PASS":"FAIL",name);
  if(okay)++passed;else ++failed;
 };
 const Context saved{};
 Context changed=saved;
 check(fxfile::nameedit::sameScope(saved,changed),"same_context");
 changed.windowTabIdentity++;
 check(!fxfile::nameedit::sameScope(saved,changed),"other_workspace");changed=saved;
 changed.side=1;
 check(!fxfile::nameedit::sameScope(saved,changed),"other_pane");changed=saved;
 changed.tab++;
 check(!fxfile::nameedit::sameScope(saved,changed),"other_pane_tab");changed=saved;
 changed.route++;
 check(!fxfile::nameedit::sameScope(saved,changed),"other_route");changed=saved;
 changed.visibleFolder+=L"\\other";
 check(!fxfile::nameedit::sameScope(saved,changed),"other_filesystem_folder");changed=saved;
 changed.visibleShellFolder+=L"\\other";
 check(!fxfile::nameedit::sameScope(saved,changed),"other_shell_folder");
 check(fxfile::nameedit::sameRenameSource(L"C:\\owned\\report.txt",
                                          L"C:\\owned\\report.txt"),
       "same_rename_source");
 check(!fxfile::nameedit::sameRenameSource(L"C:\\owned\\report.txt",
                                           L"C:\\owned\\other.txt"),
       "changed_selection");
 check(!fxfile::nameedit::sameRenameSource(L"",L"C:\\owned\\other.txt"),
       "empty_captured_source");
 check(!fxfile::nameedit::sameRenameSource(L"C:\\owned\\report.txt",L""),
       "empty_current_source");
 check(!fxfile::nameedit::sameRenameSource(L"C:\\owned\\report.txt",
                                           L"C:\\owned\\REPORT.txt"),
       "exact_spelling_required");
 std::printf("NAME_EDIT_NATIVE_SUMMARY %d passed, %d failed.\n",passed,failed);
 return passed==12&&failed==0?0:1;
}
