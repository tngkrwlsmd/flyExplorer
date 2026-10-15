"""F05 additional grouping model contracts. These do NOT certify WinUI UI."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
MODES=(ROOT/'app/winui/file_group_modes.h').read_text(encoding='utf-8')
TAB=(ROOT/'app/winui/file_group_tab_cache.h').read_text(encoding='utf-8')
RUNNER=(ROOT/'tools/winui/run_f05_group_native.py').read_text(encoding='utf-8')

class F05ExtensionContract(unittest.TestCase):
    def test_modes_and_metadata_gates(self):
        for token in ('Mode : std::uint8_t', 'ModifiedMonth', 'sizeKnown',
                      'dateKnown', 'expectedCount', 'indexComplete',
                      'modelLimitReached', 'DuplicateIdentity', 'metadataReady',
                      'kMaximumIndexedItems', 'logicalItems'):
            self.assertIn(token,MODES)
    def test_tab_scope_deferred_restore_and_limit(self):
        for token in ('kMaxSavedRoutes=32', 'pending_', 'onCompleteModel(',
                      'metadataCurrent && enumerationComplete', 'route_',
                      'tab_', 'side_', 'collapse_.resetFor', 'disable()'):
            self.assertIn(token,TAB)
    def test_extended_native_probes_are_in_canonical_runner(self):
        for name in ('native_f05_group_projection.cpp',
                     'native_f05_group_presentation.cpp',
                     'native_f05_group_modes.cpp',
                     'native_f05_group_tab_cache.cpp'):
            self.assertIn('ROOT / "tests/winui/' + name + '"', RUNNER)
        self.assertIn('F05_NATIVE_ALL_FOUR_GROUP_AND_TAB_PROBES=PASS', RUNNER)
        self.assertIn('"/std:c++17", "/utf-8", "/W4", "/WX"', RUNNER)
        self.assertIn('subprocess.run([str(target)]', RUNNER)

    def test_no_os_io_or_mutation(self):
        for text in (MODES,TAB):
            for forbidden in ('CreateFile', 'DeleteFile', 'ShellExecute',
                              'GetFileAttributes', 'SystemParametersInfo',
                              'DispatcherQueue', 'std::filesystem'):
                self.assertNotIn(forbidden,text)

if __name__=='__main__':
    unittest.main()
