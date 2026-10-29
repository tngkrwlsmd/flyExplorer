"""Address candidates reuse bounded committed folder-tab caches only."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def gathering():
    source = (ROOT / "app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")
    update = source.split("void MainWindow::UpdateAddressSuggestions()", 1)[1].split("void MainWindow::OnAddressTextChanged(", 1)[0]
    return "std::vector<std::wstring> choices;" + update.split("std::vector<std::wstring> choices;", 1)[1].split("for(std::size_t candidateIndex=0;", 1)[0]


class AddressCachedTabsContract(unittest.TestCase):
    def test_no_io_or_navigation_while_gathering(self):
        code = gathering()
        for forbidden in ("FindFirstFile", "SHParseDisplayName", "GetFileAttributes", "QueuePath(", "QueuePidl(", "OpenFolder(", "std::filesystem::exists", "std::thread"):
            self.assertNotIn(forbidden, code)
        self.assertIn("pane.pending[tab]", code)
        self.assertIn("if(side==1&&!model.split)continue;", code)
        self.assertIn("offerChildren(activeSide,activePane.active);", code)
        self.assertIn("if(side==activeSide&&tab==activePane.active)continue;", code)

    def test_shared_budget_and_prefix_segment_boundary(self):
        code = gathering()
        self.assertIn("size_t inspected=0;", code)
        self.assertIn("++i,++inspected", code)
        self.assertIn("choices.size()<8&&inspected<2048", code)
        self.assertIn("prefix.size()>folder.size()", code)
        self.assertIn("prefix[folder.size()]!=L'\\\\'", code)

    def test_production_gathering_body_compiles_and_runs(self):
        compiler = shutil.which("g++")
        if not compiler:
            self.skipTest("host C++ compiler unavailable")
        code = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cwchar>
#include <string>
#include <vector>
constexpr bool TRUE=true;
constexpr int CSTR_EQUAL=2;
// ASCII ordinal shim only; this does not verify the Windows API.
int CompareStringOrdinal(wchar_t const* a,int na,wchar_t const* b,int nb,bool){
 if(na<0)na=static_cast<int>(std::wcslen(a));
 if(nb<0)nb=static_cast<int>(std::wcslen(b));
 if(na!=nb)return 1;
 for(int i=0;i<na;++i){
  auto fold=[](wchar_t c){return c>=L'A'&&c<=L'Z'?c+32:c;};
  if(fold(a[i])!=fold(b[i]))return 1;
 }
 return CSTR_EQUAL;
}
struct Item {std::wstring parsingName;bool folder=true,filesystem=true;
 bool isFolder()const{return folder;}bool isFileSystem()const{return filesystem;}};
struct Snapshot {std::wstring parsingName;};
struct Tab {Snapshot saved;std::vector<Item> names;
 Snapshot const& snapshot()const{return saved;}
 std::vector<Item> const& nameIndex()const{return names;}};
struct Pane {std::vector<Tab> tabs;std::vector<unsigned long long> pending;size_t active=0;};
struct Model {std::array<Pane,2> panes;bool split=true;int activePane=0;};
struct Window {Model model;};
struct Output {std::vector<std::wstring> choices;size_t inspected;};
Output gather(Window const& w,std::wstring const& prefix){
 auto ActiveWindowTab=[&]() -> Window const& {return w;};
''' + gathering() + r'''
 return {choices,inspected};
}
Tab tab(std::wstring folder,std::vector<Item> names){
 return {{std::move(folder)},std::move(names)};
}
int main(){
 Window w;
 w.model.panes[0].tabs.push_back(tab(L"C:\\Unrelated",std::vector<Item>(2048,{L"ignored",false,true})));
 w.model.panes[1].tabs.push_back(tab(L"C:\\Target",{{L"C:\\Target\\Needle-한글"}}));
 auto r=gather(w,L"C:\\Target\\Ne");
 assert(r.choices.size()==1&&r.choices[0]==L"C:\\Target\\Needle-한글"&&r.inspected==1);
 w.model.split=false;
 assert(gather(w,L"C:\\Target\\Ne").choices.empty());
 w.model.split=true;w.model.panes[1].pending={91};
 assert(gather(w,L"C:\\Target\\Ne").choices.empty());
 w.model.panes[1].pending.clear();
 w.model.panes[0].tabs.push_back(tab(L"C:\\Sibling",{{L"C:\\Sibling\\Docs"}}));
 assert(gather(w,L"C:\\Sibling\\Do").choices.size()==1);
 w.model.panes[0].active=1;
 w.model.panes[1].tabs.push_back(tab(L"c:\\sibling",{{L"c:\\sibling\\docs"}}));
 r=gather(w,L"C:\\Sibling\\Do");
 assert(r.choices.size()==1&&r.choices[0]==L"C:\\Sibling\\Docs");
 Window limited;
 limited.model.panes[0].tabs.push_back(tab(L"C:\\Bound",std::vector<Item>(2048,{L"file",false,true})));
 limited.model.panes[0].tabs.push_back(tab(L"C:\\Bound",{{L"C:\\Bound\\Hit"}}));
 r=gather(limited,L"C:\\Bound\\Hi");
 assert(r.inspected==2048&&r.choices.empty());
 Window many;
 many.model.panes[0].tabs.push_back(tab(L"C:\\Many",{}));
 for(int i=0;i<12;++i)many.model.panes[0].tabs[0].names.push_back({L"C:\\Many\\Child"+std::to_wstring(i)});
 r=gather(many,L"C:\\Many\\Ch");
 assert(r.choices.size()==8&&r.inspected==8);
 Window boundary;
 boundary.model.panes[0].tabs.push_back(tab(L"C:\\Foo",{{L"C:\\Foobar\\ChildBogus"}}));
 boundary.model.panes[1].tabs.push_back(tab(L"C:\\Foobar",{{L"C:\\Foobar\\ChildReal"}}));
 r=gather(boundary,L"C:\\Foobar\\Child");
 assert(r.choices.size()==1&&r.choices[0]==L"C:\\Foobar\\ChildReal");
}
'''
        with tempfile.TemporaryDirectory(prefix="fly-address-tabs-") as directory:
            source = Path(directory) / "address.cpp"
            binary = Path(directory) / "address"
            source.write_text(code, encoding="utf-8")
            compiled = subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic", str(source), "-o", str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
