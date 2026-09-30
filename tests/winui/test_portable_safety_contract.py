"""Preview-only packaging: temporary noninstalled local smoke, no default cutover."""
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class PortableSafety(unittest.TestCase):
 def test_no_install_registry_or_cross_user_mutation(self):
  s=(HERE/"test_owned_release_portable_gui.py").read_text(encoding="utf-8")
  for x in ("root/\"logs\"/\"m23\"","prefix=\"portable-owned-\"",
            "shutil.copy2(file,dest)","if file.suffix.lower()",
            "FlyShellIsolationHelper.exe","RELEASE_PORTABLE_OWNED_FILE_AND_REGISTERED_TYPE",
            "LEGACY_PRESENT_SETTINGS_UNCHANGED"):
   self.assertIn(x,s)
  self.assertNotIn("Windows ??:",s)
  self.assertIn('file.name=="Assets"',s)
  self.assertIn('not candidate.is_symlink()',s)
  for x in ("EmptyClipboard(", "SHEmptyRecycleBinW","winreg.SetValue",
            "subprocess.run([\"msiexec\"","RegSetValue"):
   self.assertNotIn(x,s)
if __name__=="__main__":unittest.main()
