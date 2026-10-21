# miniz low-level inflate subset (F08)

- Upstream: https://github.com/richgel999/miniz
- Pinned upstream release: `3.1.2` (2026-07-01).
- Vendored unchanged: `LICENSE`, `miniz_common.h`, `miniz_tinfl.h`.
- Deliberate adaptation: `miniz_tinfl.c` replaces its upstream
  `#include "miniz.h"` with `#include "miniz_tinfl.h"`
  to build only the independent low-level inflater.
- Local generated-header shim: `miniz_export.h` uses an empty export
  marker because the subset is statically compiled into flyExplorer.
- Upstream original `miniz.h` / ZIP archive reader/writer and
  unrelated compression APIs are not bundled. `MINIZ_NO_MALLOC`
  `MINIZ_NO_STDIO`, and `MINIZ_NO_TIME` are defined for the adapter
  and the separately compiled C translation unit in the project template.
- Copyright and MIT-style license conditions remain in the upstream
  `LICENSE` and preserved file headers.
- No native build, test, ZIP sample compatibility or source acceptance
  has been performed for this newly imported dependency.
