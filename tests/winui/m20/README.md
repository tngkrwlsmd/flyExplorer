# M2.0 standalone native state/command fixtures

The `src/base/explorer_ui_state.h/.cpp` model has no MFC or WinRT type; both the real standalone WinUI application and this isolated C++ console project compile that model. This fixture does NOT certify a GUI.

Run `app/winui/m20/build.cmd Debug`, set `FLY_M20_CONFIG=Debug`, then run `python app/winui/m20/test_native.py`. Repeat with `Release` and `FLY_M20_CONFIG=Release`. Both native configurations passed 16/16, including independent left/right stable routes, per-tab request supersession, stale-result rejection, hidden pane preservation, 32-tab limits, protected last tab and validated atomic workspace reset with non-reused routes.

Only disposable native values are manipulated. The Python harness reads and compares exact hashes of the six real user-setting files but never changes them. Real WinUI GUI and full source regressions are separate; see [M2.0 scoped proof](../../../docs/development/WINUI3_M20_FULL_WINDOW_NATIVE_COMMAND_MODEL_20260929.md).
