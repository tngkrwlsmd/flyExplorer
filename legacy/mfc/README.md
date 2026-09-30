# Legacy native MFC archive

The canonical product on `main` is `app/winui`.

This directory quarantines retained material from the former MFC default product:

- `src/`: former `src/fxfile*` and `src/xpr` trees
- `build/`: former MFC build/validation scripts
- `dist/`: former MFC packaging/installer scripts
- `lib/`: former MFC bundled third-party libraries
- root-level archived MFC entry scripts such as `build.bat` and `local_ci.bat`

These paths are kept for source/history reference. They were moved after the
WinUI cutover and are not guaranteed to be directly buildable in-place because
their historical relative paths described the old root layout.

For an exact runnable copy of the previous default product, check out Git commit
`cbffb48`. Do not add new flyExplorer product features here.
