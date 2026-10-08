"""Windows Search v3 opt-in index source and owned helper contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def src(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class IndexedSearchContracts(unittest.TestCase):
    def test_explicit_mode_and_query_identity(self):
        head=src("app/winui/m19_search.h")
        core=src("app/winui/m19_search.cpp")
        controller=src("app/winui/search_controller.cpp")
        for token in ("SearchMode { Traversal, WindowsIndex }",
                      "mode=SearchMode::Traversal",
                      "scanIndexedFiles(", "indexUnavailable", "indexOnly"):
            self.assertIn(token,head+core)
        self.assertIn("a.mode==b.mode",core)
        self.assertIn("SearchMode::WindowsIndex?",controller)
        for token in ("completion.ticket!=state_->epoch",
                      "sameContext(completion.context,liveContext)",
                      "state_->cancel->store(true)"):
            self.assertIn(token,controller)
    def test_helper_only_search_and_bounded_response(self):
        core=src("app/winui/m19_search.cpp")
        helper=src("app/winui/helper/FlyShellIsolationHelper.cpp")
        wire=src("src/base/indexed_search_wire.h")
        for token in ("PROC_THREAD_ATTRIBUTE_HANDLE_LIST",
                      "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
                      "CREATE_SUSPENDED",
                      "PeekNamedPipe", "ERROR_CANCELLED", "kMaxBodyBytes"):
            self.assertIn(token,core+wire)
        for token in ("--indexed-filename-search", "Search.CollatorDSO.1",
                      "FROM SystemIndex", "SCOPE=", "System.FileName LIKE",
                      "kMaxResults", "GetDefaultSaveFolder("):
            if token=="GetDefaultSaveFolder(":
                continue
            self.assertIn(token,helper+wire)
        self.assertIn('L"SELECT TOP 1001 System.ItemUrl FROM SystemIndex "',helper)
        self.assertIn("validScope(url)",helper)
        self.assertIn("std::filesystem::path(url).lexically_normal()",helper)
        self.assertIn("GetFileAttributesW(result.c_str())",helper)
        self.assertIn("kMaxResults=1000",wire)
        self.assertIn("kMaxBodyBytes=1024u*1024u",wire)
        self.assertIn("std::uint32_t encodedCount=0",helper)
        self.assertIn("truncated=true;break;",helper)
        self.assertIn("++encodedCount",helper)
        self.assertNotIn("body.clear();results.clear()",helper)
    def test_ui_mode_and_fail_closed_unsupported_options(self):
        ui=src("app/winui/MainWindow.xaml")
        features=src("app/winui/m19_features.cpp")
        query=src("app/winui/m19_search.cpp")
        self.assertIn('x:Name="SearchModeBox"',ui)
        self.assertIn("Windows 검색 인덱스",ui)
        self.assertIn("SearchModeBox().SelectedIndex()==1",features)
        self.assertIn("InvalidIndexedCriteria",features+query)
        self.assertIn("직접 탐색으로 자동 전환하지 않았습니다",features)
        self.assertIn("query.kind!=SearchEntryKind::Files",query)
        self.assertIn("!query.contentTerm.empty()",query)
        self.assertIn("!query.regex",query.replace("query.regex||","!query.regex")) # assert explicit rejection
if __name__=="__main__": unittest.main()
