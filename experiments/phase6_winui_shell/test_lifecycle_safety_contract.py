"""No system-wide install effects; verify exact bounded owned lifecycle."""
import unittest
from pathlib import Path
BODY=(Path(__file__).resolve().parent/"test_owned_release_lifecycle.py").read_text(encoding="utf-8")
class OwnedLifecycleContract(unittest.TestCase):
 def test_revisions_scope_and_restore(self):
  for x in ("old!=new", "installed.rename(backup)",
            "backup.rename(installed)","inventory(installed)==expected",
            "signed_msix_or_production_installer_certified",
            "ORIGINAL_SIX_MFC_SETTINGS_IDENTICAL",
            '".fly-owned-install-marker"'):
   self.assertIn(x,BODY)
  self.assertIn("tempfile.mkdtemp(prefix=\"lifecycle-run-owned-\",dir=root)",BODY)
  self.assertIn('run.name.startswith("lifecycle-run-owned-")',BODY)
  self.assertIn("wait_owned_stage_processes(d)",BODY)
  self.assertIn("Path(exe).resolve().is_relative_to(root)",BODY)
  for forbidden in ("EmptyClipboard(","SHEmptyRecycleBinW","winreg.SetValue",
                    "Set-ItemProperty","msiexec","Add-AppxPackage"):
   self.assertNotIn(forbidden,BODY)
if __name__=="__main__":unittest.main()
