"""V8-E SearchController ownership and stale-result contracts."""
from pathlib import Path
import unittest

R=Path(__file__).resolve().parents[2]
A=R/"app"/"winui"
def src(path):
    return (R/path).read_text(encoding="utf-8-sig")

class SearchControllerContracts(unittest.TestCase):
    def test_controller_is_built_and_mainwindow_does_not_own_raw_search_lifecycle(self):
        project=src("app/winui/flyExplorer.project-template.xml")
        header=src("app/winui/MainWindow.xaml.h")
        controller=src("app/winui/search_controller.cpp")
        controller_h=src("app/winui/search_controller.h")
        self.assertIn("search_controller.cpp",project)
        self.assertIn("search_controller.h",project)
        self.assertIn("SearchController mSearchController",header)
        for old in ("mSearchCancel","mSearchEpoch","mRecentScopes","mRecentEdited"):
            self.assertNotIn(old,header)
        for token in ("state_->epoch","state_->cancel",
                      "scanFiles(","prepareForClose","loadRecents",
                      "recentScopes","clearRecent"):
            self.assertIn(token,controller+controller_h)

    def test_new_search_supersedes_old_and_close_invalidates_callbacks(self):
        controller=src("app/winui/search_controller.cpp")
        main=src("app/winui/MainWindow.xaml.cpp")
        for token in ("if(state_->cancel)state_->cancel->store(true)",
                      "ticket=++state_->epoch",
                      "completion.ticket!=state_->epoch",
                      "state_->closing=true",
                      "++state_->epoch"):
            self.assertIn(token,controller)
        self.assertIn("mSearchController.prepareForClose()",main)

    def test_search_context_rejects_navigation_tab_and_input_changes(self):
        controller=src("app/winui/search_controller.cpp")
        features=src("app/winui/m19_features.cpp")
        main=src("app/winui/MainWindow.xaml.cpp")
        for field in ("windowIdentity","side","tab","route",
                      "paneFolder","scope","term"):
            self.assertIn("a."+field+"==b."+field,controller)
        self.assertIn("mSearchController.accept(",features)
        self.assertIn("Disposition::StaleContext",features)
        self.assertIn("mSearchController.invalidate()",main)
        self.assertIn("action!=fxfile::shellnav::NavigationAction::Refresh",main)

    def test_recent_state_and_persistence_are_controller_owned(self):
        controller=src("app/winui/search_controller.cpp")
        features=src("app/winui/m19_features.cpp")
        for token in ("readRecentScopes(loaded)","rememberScope(",
                      "writeRecentScopes(persist)","recentRevision"):
            self.assertIn(token,controller)
        self.assertIn("mSearchController.recentScopes()",features)
        self.assertIn("mSearchController.clearRecent()",features)
        self.assertNotIn("writeRecentScopes(",features)
        self.assertNotIn("readRecentScopes(",features)

    def test_existing_bounded_filename_search_limits_remain_exact(self):
        search=src("app/winui/m19_search.cpp")
        for token in ("kMaxWalk=2500","kMaxDepth=5","kMaxResults=100",
                      "kRecentMax=8","kMaxRecentBytes=65536",
                      "term.size()>256","FILE_ATTRIBUTE_REPARSE_POINT"):
            self.assertIn(token,search)

if __name__=="__main__":
    unittest.main()
