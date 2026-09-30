# WinUI development tools

`run_checks.py` is the canonical bounded local orchestrator for the current
WinUI product. It knows the repository layout explicitly:

- product: `app/winui`
- tests: `tests/winui`
- logs: `logs/winui-scoped`

It does not dispatch CI or publish releases. Global clipboard and destructive
user-state scenarios remain separate explicit tests.
