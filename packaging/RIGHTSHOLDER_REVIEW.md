# flyExplorer rightsholder / GPL grant review

Status: **OPEN / HUMAN CONFIRMATION REQUIRED**.

This file records technical evidence only. It is not a legal conclusion.

## Current Release source evidence

- The root `LICENSE` states GPLv3-or-later and names `Copyright (c) 2012 Leon Lee Author`.
- The current WinUI application/helper projects compile 32 repository source files.
- 30 current paths have committed Git history under the author name `YoungMin Jeon`.
- The two current paths without committed history are M2.7 renames:
  `src/base/ui_session.cpp` <- `src/base/preview_session.cpp` and
  `src/base/ui_preferences.cpp` <- `src/base/preview_preferences.cpp`;
  both predecessor paths also have committed history under `YoungMin Jeon`.
- Of the 32 compiled source files, only `src/base/file_operation_core.cpp`
  currently carries an explicit source header identifying `Copyright (c) 2026
  flyExplorer contributors`; the other compiled files rely on repository-level
  licensing rather than per-file copyright/license headers.
- No root `CLA*`, `CONTRIBUTING*`, `AUTHORS*`, or `COPYRIGHT*` file was found.

Git author metadata does not establish copyright ownership, employment/work-for-
hire status, assignment, or authority to relicense. The names above therefore
cannot by themselves prove that the GPLv3-or-later grant covers all current
application source.

## Required human/rightsholder confirmation before public release

Confirm and retain an auditable answer for each item:

1. What is the legal/rightsholder relationship between the `Leon Lee` named in
   the root license and the `YoungMin Jeon` Git author identity?
2. Does the person/entity publishing flyExplorer have authority to distribute
   the original Leon Lee code under GPLv3-or-later?
3. Were the 2026 WinUI/shared-source contributions authored by that same
   rightsholder, assigned to that rightsholder, or intentionally contributed
   under GPLv3-or-later?
4. Are there any copied/vendor source portions inside the 32 compiled files
   whose terms are not represented by the tracked notices/provenance?
5. Is the intended public binary/source distribution model consistent with all
   of those grants and obligations?

Until those points are confirmed, keep `PUBLIC REDISTRIBUTION = NOT CLEARED`.
