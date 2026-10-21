# miniz low-level inflate/deflate subset (F08)

- Upstream: https://github.com/richgel999/miniz
- Pinned upstream release: `3.1.2` (2026-07-01).
- Vendored unchanged: `LICENSE`, `miniz_common.h`, `miniz_tinfl.h`, `miniz_tdef.h`.
- Deliberate adaptation: `miniz_tinfl.c` replaces its upstream
  `#include "miniz.h"` with `#include "miniz_tinfl.h"`
  to build only the independent low-level inflater.
- Deliberate adaptation: `miniz_tdef.c` replaces `#include "miniz.h"`
  with `#include "miniz_tdef.h"` and a new local
  `miniz_tdef_compat.h` shim. The shim supplies only the constants and
  private checksum helpers normally provided by upstream `miniz.h`.
  It is not a general miniz ABI.
- Local generated-header shim: `miniz_export.h` uses an empty export
  marker because the subset is statically compiled into flyExplorer.
- Upstream original `miniz.h` / ZIP archive reader/writer and
  unrelated compression APIs are not bundled. `MINIZ_NO_MALLOC`
  `MINIZ_NO_STDIO`, and `MINIZ_NO_TIME` are defined for the adapters
  and the separately compiled C translation units in the project template.
- Copyright and MIT-style license conditions remain in the upstream
  `LICENSE` and preserved file headers.
- No native build, test, ZIP sample compatibility or source acceptance
  has been performed for this newly imported dependency.
