"""M2.7 release payload selection is explicit and source-free."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
PACKAGE=ROOT/"packaging"/"package.py"

def module():
    spec=importlib.util.spec_from_file_location("fly_package",PACKAGE)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod

class ReleasePayloadContract(unittest.TestCase):
    def test_required_product_payload(self):
        m=module()
        required=set(m.REQUIRED_TOP)
        for name in ("flyExplorer.exe","flyExplorer.pri","FlyExplorer.winmd",
                     "FlyShellIsolationHelper.exe",
                     "Microsoft.WindowsAppRuntime.Bootstrap.dll"):
            self.assertIn(name,required)
        for old in ("FlyExplorerWinUIShell.exe","FlyExplorerIslandBridge.dll"):
            self.assertNotIn(old,required)
        notices={rel.as_posix() for _,rel in m.distribution_sources()}
        for name in ("licenses/flyExplorer-LICENSE.txt","licenses/GPL-3.0.txt",
                     "licenses/THIRD_PARTY-NOTICES.txt","licenses/PAYLOAD_PROVENANCE.md",
                     "licenses/nuget/microsoft.windowsappsdk/2.5.1/license.txt",
                     "licenses/nuget/microsoft.windowsappsdk/2.5.1/NOTICE.txt",
                     "licenses/nuget/microsoft.web.webview2/1.0.3719.77/LICENSE.txt",
                     "licenses/nuget/microsoft.web.webview2/1.0.3719.77/NOTICE.txt",
                     "licenses/nuget/microsoft.windows.ai.machinelearning/2.1.74/ThirdPartyNotices.txt"):
            self.assertIn(name,notices)

    def test_tracked_nuget_notice_inventory_covers_current_runtime_origins(self):
        base=ROOT/"packaging/licenses/nuget"
        expected={
            ("microsoft.web.webview2","1.0.3719.77"),
            ("microsoft.windows.ai.machinelearning","2.1.74"),
            ("microsoft.windowsappsdk","2.5.1"),
            ("microsoft.windowsappsdk.ai","2.5.5"),
            ("microsoft.windowsappsdk.dwrite","2.1.0"),
            ("microsoft.windowsappsdk.foundation","2.3.12"),
            ("microsoft.windowsappsdk.interactiveexperiences","2.1.9"),
            ("microsoft.windowsappsdk.search","2.5.5"),
            ("microsoft.windowsappsdk.widgets","2.0.5"),
            ("microsoft.windowsappsdk.winui","2.3.9"),
        }
        actual={(pkg.name,ver.name) for pkg in base.iterdir() if pkg.is_dir()
                for ver in pkg.iterdir() if ver.is_dir()}
        self.assertEqual(expected,actual)
        for package,version in expected:
            files=[p for p in (base/package/version).rglob("*") if p.is_file()]
            self.assertTrue(files,(package,version))

    def test_release_build_separates_symbols_and_link_artifacts(self):
        build=(ROOT/"app/winui/build.cmd").read_text(encoding="utf-8-sig")
        self.assertIn(r"%OUT%\symbols\winui\Release",build)
        self.assertIn("flyExplorer.pdb",build)
        self.assertIn("flyExplorer.lib",build)
        self.assertIn("flyExplorer.exp",build)

    def test_selector_excludes_build_and_source_artifacts(self):
        m=module()
        owner=ROOT/"logs"/"m27-contract-owned"
        owner.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="payload-",dir=owner) as raw:
            temp=Path(raw)
            old_out=m.OUT
            try:
                m.OUT=temp
                release=temp/"winui"/"Release"
                (release/"Assets").mkdir(parents=True)
                for name in m.REQUIRED_TOP:
                    p=release/name;p.parent.mkdir(parents=True,exist_ok=True)
                    p.write_bytes(b"runtime")
                (release/"Assets"/"icon.png").write_bytes(b"png")
                for i in range(8):
                    (release/f"runtime-{i}.dll").write_bytes(b"runtime")
                pairs=m.collect_payload("Release")
                rel={p.as_posix() for _,p in pairs}
                self.assertIn("flyExplorer.exe",rel)
                self.assertIn("Assets/icon.png",rel)
                self.assertIn("licenses/GPL-3.0.txt",rel)
                self.assertIn("licenses/nuget/microsoft.web.webview2/1.0.3719.77/LICENSE.txt",rel)
                self.assertIn("licenses/nuget/microsoft.web.webview2/1.0.3719.77/NOTICE.txt",rel)
                (release/"debug.pdb").write_bytes(b"debug")
                with self.assertRaises(SystemExit):
                    m.collect_payload("Release")
            finally:
                m.OUT=old_out

if __name__=="__main__":
    unittest.main()
