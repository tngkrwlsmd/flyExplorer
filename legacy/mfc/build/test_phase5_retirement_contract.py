"""Phase5 local code is retired; historical evidence remains recoverable in Git."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"dist"/"copy.bat"

class Phase5Retirement(unittest.TestCase):
    def test_local_phase5_sources_and_old_contracts_are_gone(self):
        for rel in ("experiments/phase5_island_bridge",
                    "experiments/phase5_winui3",
                    "build/test_phase5_native_address_contract.py",
                    "build/test_phase5_optional_package.py"):
            self.assertFalse((ROOT/rel).exists(),rel)

    def test_distribution_has_no_phase5_optin_or_island_payload(self):
        text=DIST.read_text(encoding="utf-8-sig")
        for token in ("FLYEXP_PHASE5_INCLUDE_WINUI",
                      "phase5_island_bridge",
                      "FlyExplorerIslandBridge",
                      "FlyExplorerIslandBridge.pri"):
            self.assertNotIn(token,text)
        self.assertIn('call :require_input "..\\bin\\x64\\fxfile.exe"',text)
        self.assertIn('call :copy_required "..\\bin\\x64\\fxfile.exe"',text)

    def test_legacy_mfc_has_no_phase5_runtime_hooks(self):
        sources="\n".join((ROOT/rel).read_text(encoding="utf-8-sig")
            for rel in ("src/fxfile/main_frame.cpp",
                        "src/fxfile/main_frame.h",
                        "src/fxfile/win_app.cpp",
                        "src/fxfile/explorer_view.cpp",
                        "src/fxfile/explorer_view_observer.h"))
        for token in ("FLYEXP_PHASE5_TEST_ISLAND_DLL",
                      "FlyIslandInitialize","TestIsland",
                      "WM_TEST_ISLAND_PATH_CHANGED",
                      "onActivePathChanged"):
            self.assertNotIn(token,sources)

    def test_phase6_manifest_uses_current_shell_identity(self):
        text=(ROOT/"experiments/phase6_winui_shell/app.manifest").read_text(
            encoding="utf-8-sig")
        self.assertIn('name="FlyExplorerWinUIShell.app"',text)
        self.assertNotIn("NavPoC",text)

    def test_native_dist_still_stages_transactionally_with_old_env_ignored(self):
        source=DIST.read_text(encoding="utf-8-sig")
        required=re.findall(r'(?im)^\s*call :require_input "([^"]+)"',source)
        required=[x for x in required
                  if x.lower().startswith(("..\\bin\\","..\\src\\"))]
        self.assertTrue(required)
        logs=ROOT/"logs"/"phase5-retirement"
        logs.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="native-dist-owned-",dir=logs) as tmp:
            base=Path(tmp)
            dist=base/"dist"
            dist.mkdir()
            shutil.copy2(DIST,dist/"copy.bat")
            for raw in required:
                target=dist.joinpath(*raw.split("\\")).resolve()
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(b"native-stub:"+target.name.encode("utf-8"))
            languages=base/"src"/"fxfile"/"Languages"
            languages.mkdir(parents=True,exist_ok=True)
            (languages/"English.xml").write_text("<test/>\n",encoding="utf-8")
            env=os.environ.copy()
            # A stale user/machine setting from the retired experiment must
            # have no effect now.
            env["FLYEXP_PHASE5_INCLUDE_WINUI"]="1"
            result=subprocess.run(["cmd","/d","/c","copy.bat"],cwd=dist,
                env=env,capture_output=True,text=True,errors="replace",timeout=35)
            self.assertEqual(0,result.returncode,
                             (result.stdout[-600:],result.stderr[-600:]))
            x64=dist/"bin"/"x64"
            self.assertTrue((x64/"fxfile.exe").is_file())
            self.assertFalse((x64/"FlyExplorerIslandBridge.dll").exists())
            self.assertFalse((x64/"resources.pri").exists())

if __name__=="__main__":
    unittest.main()
