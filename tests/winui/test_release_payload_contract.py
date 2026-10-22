"""Release payload selection and provenance are explicit and source-free."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
PACKAGE=ROOT/"packaging"/"package.py"
PROVENANCE=ROOT/"packaging"/"provenance.py"


def load_module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def module():
    return load_module(PACKAGE,"fly_package")


def provenance_module():
    return load_module(PROVENANCE,"fly_provenance")


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
        self.assertFalse((ROOT/"LICENSE").exists())
        self.assertFalse((ROOT/"packaging/licenses/GPL-3.0.txt").exists())
        self.assertNotIn("licenses/flyExplorer-LICENSE.txt",notices)
        self.assertNotIn("licenses/GPL-3.0.txt",notices)
        for name in ("licenses/THIRD_PARTY-NOTICES.txt","licenses/PAYLOAD_PROVENANCE.md",
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

    def test_packager_fails_closed_on_stale_provenance_before_embedding(self):
        script=PACKAGE.read_text(encoding="utf-8")
        self.assertIn("payload_provenance.verify_snapshot()",script)
        self.assertIn("RUNTIME_MANIFEST_SHA256=",script)
        self.assertLess(
            script.index("payload_provenance.verify_snapshot()"),
            script.index("pairs=collect_payload(args.configuration)"),
        )

    def test_provenance_hash_matches_runtime_and_requires_notice_inventory(self):
        p=provenance_module()
        with tempfile.TemporaryDirectory(prefix="provenance-contract-") as raw:
            root=Path(raw)
            release=root/"release"
            assets=root/"project.assets.json"
            packages=root/"packages"
            notices=root/"notices"
            release.mkdir()
            (release/"flyExplorer.exe").write_bytes(b"product-bytes")
            (release/"runtime.dll").write_bytes(b"nuget-runtime-bytes")
            demo=packages/"demo.package"/"1.2.3"
            demo.mkdir(parents=True)
            (demo/"runtimes"/"win-x64"/"native").mkdir(parents=True)
            (demo/"runtimes"/"win-x64"/"native"/"runtime.dll").write_bytes(
                b"nuget-runtime-bytes")
            sdk=packages/"microsoft.windowsappsdk"/"2.5.1"
            sdk.mkdir(parents=True)
            (sdk/"build.txt").write_text("build only",encoding="utf-8")
            assets.write_text(json.dumps({
                "libraries":{
                    "Demo.Package/1.2.3":{
                        "type":"package","path":"demo.package/1.2.3"},
                    "Microsoft.WindowsAppSDK/2.5.1":{
                        "type":"package","path":"microsoft.windowsappsdk/2.5.1"},
                }
            }),encoding="utf-8")
            for package,version in (
                ("demo.package","1.2.3"),
                ("microsoft.windowsappsdk","2.5.1"),
            ):
                target=notices/package/version
                target.mkdir(parents=True)
                (target/"LICENSE.txt").write_text("license",encoding="utf-8")

            manifest=p.build_manifest(
                release_root=release,
                assets_path=assets,
                packages_root=packages,
                notice_root=notices,
                source_revision="a"*40,
                generated_date="2026-10-05",
            )
            self.assertEqual(2,manifest["runtime_file_count"])
            self.assertEqual(1,manifest["product_generated_file_count"])
            self.assertEqual(1,manifest["nuget_matched_file_count"])
            self.assertEqual(
                [{"package":"demo.package","version":"1.2.3","files":1}],
                manifest["package_match_counts"],
            )
            self.assertEqual(
                {
                    ("demo.package","1.2.3"),
                    ("microsoft.windowsappsdk","2.5.1"),
                },
                {(x["package"],x["version"]) for x in manifest["notice_packages"]},
            )
            rendered=p.render_markdown(manifest)
            self.assertIn("Runtime manifest SHA-256",rendered)
            self.assertIn("PAYLOAD_PROVENANCE.json",rendered)

    def test_generated_payload_manifest_embeds_every_selected_file_once(self):
        m=module()
        owner=ROOT/"logs"/"m27-contract-owned"
        owner.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="payload-generate-",dir=owner) as raw:
            temp=Path(raw)
            source=temp/"source";source.mkdir()
            one=source/"one.bin";one.write_bytes(b"1")
            nested=source/"nested"/"two.dll";nested.parent.mkdir()
            nested.write_bytes(b"22")
            stage=temp/"stage";obj=temp/"obj"
            pairs=[(one,Path("one.bin")),(nested,Path("nested/two.dll"))]
            m.generate_payload(stage,obj,pairs)
            header=(obj/"payload_manifest.h").read_text(encoding="utf-8")
            rc=(obj/"payload.rc").read_text(encoding="utf-8")
            self.assertEqual(1,header.count('L"one.bin"'))
            self.assertEqual(1,header.count('L"nested/two.dll"'))
            self.assertEqual(2,rc.count(" RCDATA "))
            self.assertTrue((stage/"one.bin").is_file())
            self.assertTrue((stage/"nested"/"two.dll").is_file())

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
                self.assertNotIn("licenses/GPL-3.0.txt",rel)
                self.assertIn("licenses/nuget/microsoft.web.webview2/1.0.3719.77/LICENSE.txt",rel)
                self.assertIn("licenses/nuget/microsoft.web.webview2/1.0.3719.77/NOTICE.txt",rel)
                (release/"debug.pdb").write_bytes(b"debug")
                with self.assertRaises(SystemExit):
                    m.collect_payload("Release")
            finally:
                m.OUT=old_out


if __name__=="__main__":
    unittest.main()
