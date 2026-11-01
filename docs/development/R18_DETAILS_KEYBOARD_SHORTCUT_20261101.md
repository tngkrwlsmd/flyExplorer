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

## Verification / acceptance status

- Source revision is a **separate unmerged branch**. Actual Windows source suite, compilation, keyboard input, functional GUI, screen pixels, settings preservation and normal owned process exit are **NOT TESTED** for R18.
- Direct main acceptance requires the affected source check and, if separately authorized, one owned Windows keyboard GUI scenario with both Alt+Shift+P transitions, Alt+P unchanged, no implicit content reading, source/settings preservation and normal exit. Record visual evidence separately if presentation changes.
- The R17 physical View-menu second-click defect remains blocked independently. No previously accepted functionality should be retested unless its boundary changed.
