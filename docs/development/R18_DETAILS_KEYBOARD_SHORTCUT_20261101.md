# R18 — Windows Explorer Details pane shortcut (Alt+Shift+P)

## Scope and evidence

- Official Windows File Explorer keyboard guidance: Alt+P opens/closes Preview, Alt+Shift+P opens/closes Details: https://support.microsoft.com/ko-kr/windows/windows%EC%9D%98-%EB%B0%94%EB%A1%9C-%EA%B0%80%EA%B8%B0-%ED%82%A4-dcc61a57-8ff0-cffe-9796-cb9706c75eec
- Current accepted main `84b1780e94483f8aa70043d1e19296cc0b561b1f` already maps Alt+P to the shared Details/Preview pane with explicit preview focus. It does not map Alt+Shift+P.
- The separate R17 View-flyout work `be5ed935c9b6360afa77f400d4ca079312ffb848` passed relevant source contracts and x64 Release in [Windows #41278326721](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41278326721), EXE SHA256 `03e5ccd0875c7a082abb09f6c4992cf722035bc08ae57c50de2569f437f0ed3e`, but [physical-click GUI #41282607675](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41282607675) **failed** its second click; the menu stayed open even though the exact app-owned item was hit. This R18 shortcut does **not** claim to repair that bug.

## R18 change

- Add `Alt+Shift+P` to the existing root `PreviewKeyDown` dispatch. Preserve the existing Alt+P preview path, Escape/Enter for dialogs and editor focus guards.
- Dispatch only the first press of P (`KeyStatus().WasKeyDown` blocks key repeat), call the existing `OnToggleFileInfoPane` state transition and consume the shortcut. Unlike Alt+P, do not call `OnRevealTextPreview`, start a file-content read, or shift keyboard focus.
- Keep the current active WindowTab, pane/PaneTab ownership, private session v4, FileOperationController and bounded preview opt-in rules. Do not change the unaccepted R12 menu entry or any GUI screenshot.
- Add focused R18 source contract to the existing core source suite; no broad suite, installer, clean build or user-data operations.

## Verification / limited acceptance (2026-11-01)

- **Exact product source:** `c57fc3b7e851e29589c6401a42f4c6b8c2532c77`, based on then-main `84b1780e94483f8aa70043d1e19296cc0b561b1f`. The only product behavior change is the shortcut; the legacy shortcut contract also updates two stale expectations to the already-accepted eight view modes and Ctrl+wheel icon limit.
- **Windows source + x64 Release:** [#41284881498](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41284881498) **PASS**, focused source contracts **24/24**, build **PASS**; executable SHA256 `29d7cb3fa94f4b91cd245a7185b14d77a634f847eaa961c82576a2fc12bab4d8`. The earlier harness-path and pre-existing shortcut assertion failures were corrected without dismissing failed evidence or repeating unrelated tests.
- **Actual owned keyboard GUI:** [#41286258463](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41286258463) **PASS** with the exact same executable hash and product source. Physical `Alt+Shift+P` opened and closed Details; legacy `Alt+P` still opened and closed the pane; the selected synthetic text file was not read without explicit opt-in. Owned source bytes and real settings remained unchanged; app exit code 0, disposable profile/fixture and worker cleanup **PASS**.
- **Bounded scope:** Dark theme, one interactive Windows desktop and owned local fixture only. Actual screen pixels were **NOT REVIEWED**, and other themes/DPI/remote providers, full suite, package, and native Debug remain untested. No layout or preview opt-in policy was changed.
- **Independently unresolved:** R17 physical View-menu Details second click [#41282607675](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41282607675) still fails; R18 keyboard success does not repair or certify the R12/R17 flyout entry.
