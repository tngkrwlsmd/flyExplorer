"""Source-only contracts for L08 WinUI API preflight; no Windows build."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "winui" / "l08_winui_projection_preflight.ps1"


class L08WinUIProjectionPreflightContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8")

    def test_pinned_components_and_generator_signature(self):
        source = self.source
        self.assertEqual(len(re.findall(r"Hash='[0-9A-F]{64}'", source)), 5)
        for name in ("microsoft.windowsappsdk.winui",
                     "microsoft.windowsappsdk.foundation",
                     "microsoft.windowsappsdk.interactiveexperiences",
                     "microsoft.web.webview2", "microsoft.windows.cppwinrt"):
            self.assertIn(name, source)
        for marker in ("Get-FileHash", "SHA256",
                       "Get-AuthenticodeSignature", "L08_CPPWINRT_SIGNATURE_VALID=True"):
            self.assertIn(marker, source)

    def test_final_generated_projection_inputs_and_versions(self):
        source = self.source
        for marker in ("Microsoft.UI.Xaml.winmd", "Microsoft.UI.winmd",
                       "Microsoft.Foundation.winmd", "Microsoft.UI.h",
                       "Microsoft.UI.Xaml.Controls.h",
                       "L08_MATCHING_CPPWINRT_BASE_HEADER_MISSING",
                       "L08_FINAL_GENERATED_BASE_HEADER_MISSING",
                       "function ProjectionVersion",
                       "CPPWINRT_VERSION",
                       "L08_CPPWINRT_GENERATED_VERSION_MISMATCH"):
            self.assertIn(marker, source)
        platform = source.index("Generate @('-input','sdk'")
        winui = source.index("Generate @('-input',('")
        final_guard = source.index("L08_CPPWINRT_GENERATED_VERSION_MATCH=True")
        compile_start = source.index("cl.exe /nologo /std:c++20")
        self.assertLess(platform, winui)
        self.assertLess(winui, final_guard)
        self.assertLess(final_guard, compile_start)

    def test_native_error_retention_and_owned_cleanup(self):
        source = self.source
        for marker in ("L08_GENERATOR_ERROR", "L08_COMPILE_ERROR",
                       "L08_COMPILE_ERROR", "_EMISSION_LIMIT=160",
                       "L08_WINUI_SCRATCH_REMOVED=True",
                       "FileAttributes]::ReparsePoint",
                       "L08_UNSAFE_OWNED_DIRECTORY"):
            self.assertIn(marker, source)
        self.assertLess(source.index("LogErrors $log 'L08_COMPILE_ERROR'"),
                        source.index("L08_CPP_API_COMPILE_FAILED"))
        self.assertIn("finally{", source)

    def test_no_product_or_gui_side_effects(self):
        source = self.source
        for prohibited in ("build.bat", "run_checks.py gui", "Remove-Item -LiteralPath $env:APPDATA",
                           "Set-ItemProperty -Path 'HKCU:", "gh workflow run"):
            self.assertNotIn(prohibited, source)
        self.assertIn("/Zs", source)
        self.assertIn("$owned=Join-Path $parent", source)


if __name__ == "__main__":
    unittest.main()
