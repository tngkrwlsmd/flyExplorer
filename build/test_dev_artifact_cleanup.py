"""Non-destructive regression tests for the opt-in cleanup tool."""
import importlib.util
from pathlib import Path
import tempfile
import time
import unittest

PATH=Path(__file__).with_name("cleanup_dev_artifacts.py")
spec=importlib.util.spec_from_file_location("cleanup_dev_artifacts",PATH)
tool=importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class CleanupSafety(unittest.TestCase):
    def test_release_selection_never_includes_debug_or_executable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            shell=root/"experiments"/"phase6_winui_shell"
            release=shell/"FlyExplo.DUMMY"/"x64"/"Release"
            debug=shell/"FlyExplo.DUMMY"/"x64"/"Debug"
            exe=shell/"x64"/"Release"/"FlyExplorerWinUIShell.exe"
            for p in (release,debug,exe.parent):p.mkdir(parents=True)
            exe.write_bytes(b"protected")
            self.assertEqual([release],tool.release_targets(root))
            self.assertEqual(b"protected",exe.read_bytes())

    def test_success_log_prune_preserves_latest_references_failures(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            now=time.time()
            for n in range(5):
                path=p/(f"2025010{n+1}-120000-source.log")
                path.write_text("Ran 3 tests in 0.1s\n\nOK\n",encoding="utf-8")
                stamp=now-86400*(45-n)
                import os
                os.utime(path,(stamp,stamp))
            fail=p/"20250106-120000-source.log"
            fail.write_text("Ran 3 tests in 0.1s\nFAILED\n",encoding="utf-8")
            import os
            os.utime(fail,(now-86400*60,now-86400*60))
            entries=tool.prune_candidates(p,"20250102-120000-source.log",
                                           now=now,days=30,keep=2)
            self.assertEqual(["20250101-120000-source.log",
                              "20250103-120000-source.log"],
                             [e.name for e in entries])
            self.assertTrue(fail.exists())

    def test_root_and_nested_document_evidence_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"AGENTS.md").write_text("do not remove evidence-foo.log",
                                          encoding="utf-8")
            (root/"experiments").mkdir()
            (root/"experiments"/"README.md").write_text(
                "keep nested-record.log",encoding="utf-8")
            docs=tool.documentation(root)
            self.assertIn("evidence-foo.log",docs)
            self.assertIn("nested-record.log",docs)

    def test_symlink_ancestor_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            outside=root/"elsewhere"
            outside.mkdir()
            link=root/"alias"
            try:link.symlink_to(outside,target_is_directory=True)
            except (OSError,NotImplementedError):
                self.skipTest("Windows cannot create symlinks")
            with self.assertRaises(RuntimeError):
                tool.no_links_under(root,link/"file")


if __name__ == "__main__":
    unittest.main()
