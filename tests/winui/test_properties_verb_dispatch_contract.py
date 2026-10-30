"""Execute the actual direct-verb branch with a bounded fake Shell menu."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PropertiesDispatch(unittest.TestCase):
    def test_direct_verb_initializes_success_and_rejects_missing_properties(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("host C++ compiler unavailable; Windows build is separate")
        source = (ROOT / "app/winui/helper/FlyShellIsolationHelper.cpp").read_text()
        body = source.split("if(directProperties){", 1)[1].split("}else{", 1)[0]
        program = r'''
#include <algorithm>
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
using UINT=unsigned;
constexpr int GCS_VERBA=0;
bool SUCCEEDED(int value){return value>=0;}
unsigned HRESULT_CODE(unsigned value){return value;}
struct Menu {
 std::vector<std::string> verbs;
 int GetCommandString(UINT i,int,void*,char* text,unsigned size){
  if(i>=verbs.size()||verbs[i]=="<failure>")return -1;
  std::strncpy(text,verbs[i].c_str(),size-1);return 0;
 }
};
int dispatch(Menu& fake,UINT& chosen){
 auto menu=&fake;const auto added=static_cast<UINT>(fake.verbs.size());
 int rc=59;
''' + body + r'''
 return rc;
}
int main(){
 UINT chosen=0;Menu present{{"open","PrOpErTiEs","delete"}};
 assert(dispatch(present,chosen)==0&&chosen==2);
 chosen=0;Menu missing{{"open","delete","advancedproperties"}};
 assert(dispatch(missing,chosen)==66&&chosen==0);
 chosen=0;Menu failed{{"<failure>","","properties"}};
 assert(dispatch(failed,chosen)==0&&chosen==3);
 chosen=0;Menu empty{{}};assert(dispatch(empty,chosen)==66&&chosen==0);
}
'''
        with tempfile.TemporaryDirectory(prefix="properties-verb-", dir=ROOT / "logs") as tmp:
            path = Path(tmp) / "test.cpp"
            binary = Path(tmp) / "test"
            path.write_text(program)
            result = subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                                     str(path), "-o", str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
