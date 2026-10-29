"""Search depth wiring and executable lexical scope/identity boundaries.

The native probe compiles the production pure function bodies on the host.
Its ASCII ordinal shim is not a Windows API or full-app build test.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def src(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class SearchScopeContracts(unittest.TestCase):
    def test_scope_control_defaults_to_existing_recursive_behavior(self):
        root = ET.fromstring(src("app/winui/MainWindow.xaml"))
        name = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"
        control = next(n for n in root.iter() if n.get(name) == "SearchSubfoldersBox")
        self.assertEqual(control.get("IsChecked"), "True")
        self.assertEqual(control.get("Content"), "하위 폴더 포함")
        self.assertIn("bool includeSubfolders=true;", src("app/winui/m19_search.h"))
        features = src("app/winui/m19_features.cpp")
        self.assertIn("context.query.includeSubfolders=SearchSubfoldersBox().IsChecked().GetBoolean();", features)
        self.assertIn("completion.request.query.includeSubfolders?", features)
        self.assertIn('L" · 지정한 폴더만"', features)

    def test_traversal_depth_does_not_change_matching_or_safety_limits(self):
        core = src("app/winui/m19_search.cpp")
        scan = core.split("SearchResults scanFiles(", 1)[1].split("SearchResults scanIndexedFiles(", 1)[0]
        self.assertIn("if(query.includeSubfolders&&folderEntry&&", scan)
        self.assertLess(scan.index("if(matched){"), scan.index("if(query.includeSubfolders"))
        self.assertIn("FILE_ATTRIBUTE_REPARSE_POINT", scan)
        self.assertIn("top.second<kMaxDepth", scan)
        self.assertIn("walked>=kMaxWalk", scan)
        self.assertIn("cancel&&cancel->load()", scan)

    def test_index_depth_is_sent_validated_and_rechecked(self):
        core = src("app/winui/m19_search.cpp")
        helper = src("app/winui/helper/FlyShellIsolationHelper.cpp")
        self.assertIn('quoteArg(query.includeSubfolders?L"1":L"0")', core)
        self.assertIn('includeSubfolders?L"WHERE SCOPE=\'":L"WHERE DIRECTORY=\'"', helper)
        self.assertIn("!insideScope(scope,result,includeSubfolders)", helper)
        self.assertIn('if(argc==10&&wcscmp(argv[9],L"0")&&wcscmp(argv[9],L"1"))return 1;', helper)
        self.assertIn('argc<10||!wcscmp(argv[9],L"1")', helper)
        self.assertIn('argc>=9?argv[7]:L"",argc>=9?argv[8]:L""', helper)

    def test_changed_depth_invalidates_result_identity_without_persistence_change(self):
        core = src("app/winui/m19_search.cpp")
        controller = src("app/winui/search_controller.cpp")
        self.assertIn("a.includeSubfolders==b.includeSubfolders", core)
        self.assertIn("fxfile::preview::sameSearchQuery(a.query,b.query)", controller)
        self.assertIn("sameContext(completion.context,liveContext)", controller)
        self.assertNotIn("includeSubfolders", src("src/base/search_preset_store.h"))
        self.assertNotIn("SearchSubfoldersBox", src("app/winui/search_preset_features.cpp"))

    def test_production_lexical_scope_and_context_bodies_compile_and_execute(self):
        compiler = shutil.which("g++")
        if not compiler:
            self.skipTest("host C++ compiler unavailable")
        helper = src("app/winui/helper/FlyShellIsolationHelper.cpp")
        inside = "bool insideScope(" + helper.split("bool insideScope(", 1)[1].split("int runIndexedFilenameSearch(", 1)[0]
        quote_sql = "std::wstring sqlQuoted(" + helper.split("std::wstring sqlQuoted(", 1)[1].split("bool insideScope(", 1)[0]
        sql_body = "std::wstring sql=" + helper.split("std::wstring sql=", 1)[1].split("if(!extension.empty())", 1)[0]
        core = src("app/winui/m19_search.cpp")
        same_query = "bool sameSearchQuery(" + core.split("bool sameSearchQuery(", 1)[1].split("SearchResults scanFiles(", 1)[0]
        controller = src("app/winui/search_controller.cpp")
        same_context = "bool SearchController::sameContext(" + controller.split("bool SearchController::sameContext(", 1)[1].split("SearchController::StartStatus SearchController::start(", 1)[0]
        code = r'''
#include "app/winui/search_controller.h"
#include <algorithm>
#include <cassert>
#include <cstdio>
constexpr bool TRUE=true;
constexpr int CSTR_EQUAL=2;
// Only the case-insensitive ASCII behavior needed by the lexical tests.
int CompareStringOrdinal(wchar_t const* a,int na,wchar_t const* b,int nb,bool) {
 if(na!=nb)return 1;
 for(int i=0;i<na;++i){
  auto fold=[](wchar_t c){return c>=L'A'&&c<=L'Z'?c+32:c;};
  if(fold(a[i])!=fold(b[i]))return 1;
 }
 return CSTR_EQUAL;
}
''' + quote_sql + inside + "\nstd::wstring indexSql(bool includeSubfolders,std::wstring const& url,std::wstring const& term){\n" + sql_body + "return sql;\n}\nnamespace fxfile::preview {\n" + same_query + "}\nnamespace fxfile::previewsearch {\n" + same_context + r'''
}
int main(){
 assert(insideScope(L"C:\\Owned",L"C:\\Owned\\match.txt",false));
 assert(insideScope(L"c:\\owned\\",L"C:\\Owned\\한글.txt",false));
 assert(insideScope(L"C:/Owned/",L"C:\\Owned\\match.txt",false));
 assert(!insideScope(L"C:\\Owned",L"C:\\Owned\\Child\\match.txt",false));
 assert(insideScope(L"C:\\Owned",L"C:\\Owned\\Child\\match.txt",true));
 assert(!insideScope(L"C:\\Owned",L"C:\\OwnedOther\\match.txt",true));
 assert(!insideScope(L"C:\\Owned",L"C:\\Owned",true));
 assert(!insideScope(L"C:\\Owned",L"D:\\Owned\\match.txt",true));
 assert(insideScope(L"C:\\",L"C:\\match.txt",false));
 assert(!insideScope(L"C:\\",L"C:\\Child\\match.txt",false));
 assert(insideScope(L"C:/",L"C:\\Child\\match.txt",true));
 assert(indexSql(false,L"file:C:/O'Brien/",L"report").find(
     L"WHERE DIRECTORY='file:C:/O''Brien/'")!=std::wstring::npos);
 assert(indexSql(true,L"file:C:/Owned/",L"a'b").find(
     L"WHERE SCOPE='file:C:/Owned/' AND System.FileName LIKE '%a''b%'")!=std::wstring::npos);
 fxfile::previewsearch::SearchController::Context a{},b{};
 a.query.term=b.query.term=L"한글 report";
 assert(a.query.includeSubfolders&&b.query.includeSubfolders);
 assert(fxfile::previewsearch::SearchController::sameContext(a,b));
 b.query.includeSubfolders=false;
 assert(!fxfile::previewsearch::SearchController::sameContext(a,b));
 a.query.includeSubfolders=false;
 assert(fxfile::previewsearch::SearchController::sameContext(a,b));
 a.query.mode=b.query.mode=fxfile::preview::SearchMode::WindowsIndex;
 b.query.includeSubfolders=true;
 assert(!fxfile::previewsearch::SearchController::sameContext(a,b));
 std::puts("LEXICAL_SCOPE_AND_QUERY_CONTEXT_PASS");
}
'''
        with tempfile.TemporaryDirectory(prefix="fly-search-scope-") as directory:
            source = Path(directory) / "scope.cpp"
            exe = Path(directory) / "scope"
            source.write_text(code, encoding="utf-8")
            compiled = subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic", "-I", str(ROOT), str(source), "-o", str(exe)], capture_output=True, text=True, timeout=30)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("LEXICAL_SCOPE_AND_QUERY_CONTEXT_PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
