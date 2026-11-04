"""R07 restore observation must fail closed when Windows path comparison fails.

Run: python -m unittest discover -s tests/winui -p test_r07_compare_fail_closed_contract.py
This is a source contract, not a Windows native/GUI acceptance test.
"""
from pathlib import Path
import re
import unittest


SOURCE = Path(__file__).resolve().parents[2] / "src/base/file_command_core.cpp"


class RenameRestoreCompareContract(unittest.TestCase):
    def test_comparison_failure_is_rejected(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("RenameRestoreObservation inspectRenameRestore(")
        end = source.index("\nbool validLeaf(", start)
        function = source[start:end]
        self.assertRegex(
            function,
            r"\(\[\]\(int comparison\) noexcept \{\s*"
            r"return comparison != CSTR_LESS_THAN && "
            r"comparison != CSTR_GREATER_THAN;\s*\}\)"
            r"\(::CompareStringOrdinal\(original\.c_str\(\),-1,"
            r"target\.c_str\(\),-1,TRUE\)\)\s*\|\|"
            r"\s*!safeRenameEvidenceParent",
            "only explicit less/greater outcomes may pass; zero and equal must fail closed",
        )
        self.assertIn("return RenameRestoreObservation::UnsafePaths;", function)


    def test_rename_mutation_rejects_failed_comparison(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("if(task.kind!=Kind::RenameSelected)")
        end = source.index("// Capture only read-only identity evidence", start)
        function = source[start:end]
        self.assertRegex(
            function,
            r"int const renameComparison=::CompareStringOrdinal\(\s*"
            r"src\.c_str\(\),-1,target\.c_str\(\),-1,TRUE\);"
            r"\s*if\(renameComparison!=CSTR_LESS_THAN&&"
            r"renameComparison!=CSTR_GREATER_THAN\)",
        )
        self.assertIn("ERROR_ALREADY_EXISTS:ERROR_INVALID_NAME", function)
        self.assertIn("return result;", function)


    def test_rename_guard_precedes_mutation_and_preserves_error_distinction(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("if(task.kind!=Kind::RenameSelected)")
        end = source.index("if(::MoveFileW(src.c_str(),target.c_str()))", start)
        guard = source[start:end]
        comparison = guard.index("int const renameComparison=::CompareStringOrdinal(")
        rejection = guard.index("if(renameComparison!=CSTR_LESS_THAN&&")
        error = guard.index("result.error=renameComparison==CSTR_EQUAL?")
        exit_guard = guard.index("return result;", error)
        evidence = guard.index("RenameEvidence before{};")
        self.assertLess(comparison, rejection)
        self.assertLess(rejection, error)
        self.assertLess(error, exit_guard)
        self.assertLess(exit_guard, evidence)
        self.assertRegex(
            guard[error:exit_guard],
            r"renameComparison==CSTR_EQUAL\?\s*"
            r"ERROR_ALREADY_EXISTS:ERROR_INVALID_NAME;",
            "equal paths must retain collision error; API failure must use invalid-name error",
        )
        self.assertNotIn("::MoveFileW(", guard)


if __name__ == "__main__":
    unittest.main()
