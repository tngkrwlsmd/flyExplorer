"""M2.7 final product identity is no longer a migration/preview shell."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app"/"winui"

class ProductIdentityContract(unittest.TestCase):
    def test_canonical_identity_and_version_source(self):
        project=(APP/"flyExplorer.project-template.xml").read_text(encoding="utf-8")
        manifest=(APP/"app.manifest").read_text(encoding="utf-8")
        version=(APP/"product_version.h").read_text(encoding="utf-8")
        resource=(APP/"product.rc").read_text(encoding="utf-8")
        self.assertIn("<ProjectName>flyExplorer</ProjectName>",project)
        self.assertIn("<RootNamespace>FlyExplorer</RootNamespace>",project)
        self.assertIn("<TargetName>flyExplorer</TargetName>",project)
        xml=ET.fromstring(project)
        ns={"m":"http://schemas.microsoft.com/developer/msbuild/2003"}
        self_contained=[]
        for group in xml.findall("m:PropertyGroup",ns):
            value=group.find("m:WindowsAppSDKSelfContained",ns)
            if value is not None:
                self_contained.append((group.attrib.get("Condition",""),(value.text or "").strip()))
        self.assertEqual(self_contained,[
            ("'$(Configuration)'=='Debug'","false"),
            ("'$(Configuration)'=='Release'","true"),
        ])
        self.assertIn("<RuntimeLibrary>MultiThreaded</RuntimeLibrary>",project)
        self.assertIn('name="flyExplorer.app"',manifest)
        self.assertIn('FLYEXPLORER_VERSION_STRING "1.0.0.0"',version)
        for token in ("ProductName","FileDescription","CompanyName",
                      "InternalName","OriginalFilename","ProductVersion",
                      "FileVersion","LegalCopyright"):
            self.assertIn(token,resource)
        self.assertTrue((APP/"Assets/flyExplorer.ico").is_file())

    def test_current_product_paths_have_no_retired_identity(self):
        roots=(APP,ROOT/"src/base",ROOT/"packaging")
        extensions={".cpp",".h",".xaml",".idl",".xml",".cmd",".bat",".py",".md",".manifest",".rc"}
        bodies=[]
        for root in roots:
            for p in root.rglob("*"):
                if p.is_file() and p.suffix.lower() in extensions:
                    bodies.append(p.read_text(encoding="utf-8-sig",errors="replace"))
        body="\n".join(bodies)
        for token in ("FlyExplorerWinUIShell","WinUI3NavPoC",
                      "phase6_winui_shell","Phase6","PoC","Migration"):
            self.assertNotIn(token,body,token)
        # Retired product identity used Preview as a standalone label. Do not
        # reject legitimate WinUI API identifiers such as PreviewKeyDown.
        self.assertIsNone(re.search(r"\bPreview\b",body),"Preview")

    def test_runtime_path_resolver_uses_final_executable_name(self):
        paths=(ROOT/"tests/winui/paths.py").read_text(encoding="utf-8")
        run=(ROOT/"run.bat").read_text(encoding="utf-8-sig")
        self.assertIn('"flyExplorer.exe"',paths)
        self.assertIn(r"flyExplorer.exe",run)
        self.assertNotIn("FlyExplorerWinUIShell",paths+run)

if __name__=="__main__":
    unittest.main()
