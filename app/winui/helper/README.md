# Isolated native Shell helper

FlyShellIsolationHelper.exe is the current bounded out-of-process Shell fault
boundary used by the canonical WinUI application.

It accepts a strict private binary request over inherited pipes and returns
bounded Shell snapshots/visual data. The host supervisor owns exact child
process handles and Job objects, limits concurrent work to the product's
bounded lanes, applies finite timeouts and rejects stale route/request results.

The helper is read-oriented and must not become a general file-operation API.
It is not a restricted-token security sandbox and does not make arbitrary
third-party Shell extensions trusted.

Debug-only owned fault injection exists solely for deterministic timeout/restart
acceptance. It must require explicit test opt-in and must never target a real
third-party process.

Build from the tracked project template using helper\build.cmd or the root
product build. Never edit generated .vcxproj files.

Current architectural requirements are in
docs/development/ARCHITECTURE.md and current verification/open gates in
docs/development/CURRENT_STATUS.md.
