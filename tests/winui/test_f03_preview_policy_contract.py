"""F03 phase-one source contract: conservative read-only preview screening."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
POLICY = (ROOT / "src/base/file_preview_policy.h").read_text(encoding="utf-8")
NATIVE = (ROOT / "tests/winui/native_preview_policy.cpp").read_text(
    encoding="utf-8")


class F03PreviewPolicyContract(unittest.TestCase):
    def test_pure_policy_caps_and_explicit_rejections(self):
        for marker in (
            "kMaxPathUnits = 32767;",
            "kMaxTextBytes = 256ull * 1024;",
            "kMaxImageBytes = 12ull * 1024 * 1024;",
            "kMaxDecodedPixels = 16ull * 1024 * 1024;",
            "NonLocal, NonRegular, Reparse, UnknownSize, InvalidPath",
            "UnsupportedType, TooLarge",
            "item.isLocalFixedDrive",
            "item.isRegularFile",
            "item.isReparsePoint",
            "item.hasKnownSize",
            "canonicalLocalPath(item.absolutePath)",
            "item.knownBytes > bound",
            "constexpr Decision screen(Candidate const& item) noexcept",
        ):
            self.assertIn(marker, POLICY)

    def test_file_types_are_closed_and_active_formats_are_not_enabled(self):
        for extension in (".txt", ".md", ".log", ".png", ".jpg",
                          ".jpeg", ".bmp"):
            self.assertIn(f'L"{extension}"', POLICY)
        for extension in (".svg", ".pdf", ".html", ".exe", ".dll"):
            self.assertNotIn(f'L"{extension}"', POLICY)
        self.assertIn("Rejection::UnsupportedType", POLICY)

    def test_scope_is_pure_not_native_io(self):
        for forbidden in ("CreateFile", "GetFileAttributes", "FindFirstFile",
                          "std::filesystem", "ShellExecute", "CoCreateInstance",
                          "ifstream", "std::thread", "ReadFile("):
            self.assertNotIn(forbidden, POLICY)
        self.assertIn("not authorization to open a file", POLICY)

    def test_native_static_asserts_cover_unsafe_paths_and_limits(self):
        for marker in (
            "static_assert(!canonicalLocalPath(",
            "static_assert(screen(local(",
            "Rejection::TooLarge",
            "Rejection::Reparse",
            "Rejection::NonRegular",
            "Rejection::NonLocal",
            "Rejection::InvalidPath",
            "Rejection::UnsupportedType",
            "static_assert(kMaxDecodedPixels",
        ):
            self.assertIn(marker, NATIVE)


if __name__ == "__main__":
    unittest.main()
