"""Cheap standard-library static checks for Python validation helpers.

This is intentionally narrow. It catches syntax errors and undefined global names
such as using sys.argv without importing sys, without adding a lint dependency.
"""
from __future__ import annotations

import argparse
import builtins
from pathlib import Path
import symtable
import sys

IMPLICIT_GLOBALS = {
    "__name__",
    "__file__",
    "__package__",
    "__spec__",
    "__loader__",
    "__cached__",
}


def _module_bindings(table: symtable.SymbolTable) -> set[str]:
    bindings = set(IMPLICIT_GLOBALS)
    bindings.update(dir(builtins))
    for symbol in table.get_symbols():
        if symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace():
            bindings.add(symbol.get_name())
    return bindings


def undefined_names(source: str, filename: str = "<string>") -> list[str]:
    compile(source, filename, "exec")
    table = symtable.symtable(source, filename, "exec")
    bindings = _module_bindings(table)
    failures: set[str] = set()

    def visit(scope: symtable.SymbolTable) -> None:
        for symbol in scope.get_symbols():
            if (
                symbol.is_referenced()
                and symbol.is_global()
                and symbol.get_name() not in bindings
            ):
                failures.add(symbol.get_name())
        for child in scope.get_children():
            visit(child)

    visit(table)
    return sorted(failures)


def check_path(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8-sig")
    names = undefined_names(source, str(path))
    return [f"{path}: undefined global name: {name}" for name in names]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)

    failures: list[str] = []
    for path in args.paths:
        try:
            failures.extend(check_path(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f"{path}: {exc}")

    if failures:
        for failure in failures:
            print(f"PYTHON_STATIC_FAILURE: {failure}", file=sys.stderr)
        return 2

    print(f"PYTHON_STATIC_PASS paths={len(args.paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
