# Real Windows Narrator spoken-output acceptance — flyExplorer

Status: **OPEN / NOT ACCEPTED** on 2026-10-12. This is a specific
accessibility gate, separate from UI Automation names, physical keyboard,
Korean IME composition, current-96-DPI visual checks, and OS scale testing.

## Evidence so far

On Windows 11 Pro build 26300 (interactive session 2), the Narrator
executable, Windows audio services and one healthy playback endpoint were
present. Before testing there were no Narrator processes.

- Read-only capability inventory:
  [38229681112](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38229681112).
- Starting `Narrator.exe` directly from a limited user task failed with
  `WinError 740`; do not bypass a UAC prompt:
  [38230127856](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230127856).
- **Windows+Ctrl+Enter successfully started Narrator** while a disposable
  native Win32 EDIT was focused:
  `NARRATOR_SHORTCUT_LAUNCH_COUNT=1` and
  `NARRATOR_OWNED_LAUNCH_ACTIVE=True`.
  The automatic Narrator+Alt+X Speech Recap/UIA attempt did not expose
  Narrator-owned text nodes or prove a spoken reference phrase; the
  waveform was **not captured**. The wrapper job failed when non-elevated
  psutil attempted to wait for the higher-integrity Narrator process:
  [38230388533](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230388533).
- An independent SYSTEM-level inventory after the test confirmed **zero**
  Narrator processes and **zero** test task registrations:
  [38230563415](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230563415).
- This is **not a product failure**, but it is also **not speech
  acceptance**: no actual Narrator phrase has been verified yet.

## 2026-10-12 unattended follow-up: capability boundary

A synthetic **foreground-controlled Win32 EDIT** case confirmed
Narrator Speech Recap windows and 35 UIA nodes after recovering
foreground focus; see
[38232530406](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38232530406).
The original zero-node result reflected overly restrictive window
discovery and startup focus ownership, **not** proof that Speech Recap
could not be opened. Yet there was still no match for the test-only
reference utterance.

A second synthetic reference using a native **Button** with a verified
UIA accessible Name confirmed that the button was meaningfully
labeled and focused, and that a Recap window existed. The test still
could **not** verify that the exact phrase had been spoken from the
accessible Recap transcript
([38233608351](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38233608351)).
This outcome cannot be treated as an application defect or as speech
acceptance. The collector may be incomplete and no audio was captured.

**Operational recovery warning:** when Speech Recap is open, injecting
`Windows+Ctrl+Enter` or `Narrator+Esc` alone did not reliably
terminate the test's higher-integrity Narrator process. One supervised
exact-PID stop was followed by a second Narrator PID. The successful
bounded cleanup, following strict initial-off, executable identity,
session, fresh-creation-time and exact test-root guards, is in
[38234299929](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38234299929).
Only this specific disposable test was eligible for that operation.
Never generalize it into permission to kill a user's preexisting
screen reader.

**Do not keep repeating unattended hotkey/Recap probes on the shared
Windows session.** The next speech attempt needs a separate attended
desktop and a real listening observer, or an independently validated
privacy-limited capture path that proves a named flyExplorer phrase
came from Narrator (not simply from the app's own UIA tree). Only
then resume the product checklist below. Confirm initial Narrator
state before *and after* any run.

## Safe preparation

1. Use a separate, **attended** Windows 11 graphical session where the
   verifier can hear the speaker/headphones. Confirm the output device
   and human-verifiable volume before launching Narrator. Avoid
   connecting to an actively used private desktop.
2. Record exact flyExplorer `main` source SHA, built Release runtime,
   Windows OS build, display resolution, **actual** OS DPI, language,
   Narrator version, audio output configuration, and whether Narrator
   was already running. Do not mix results from different revisions or
   scales.
3. Use only a disposable, test-owned folder with synthetic files
   (`alpha.cpp`, `beta.h`, `notes.txt`) and isolated `APPDATA`,
   `LOCALAPPDATA`, `TEMP` and `TMP` for the flyExplorer process.
   Preserve a hash-only snapshot of preexisting user settings. Do not
   capture private window names, desktop audio or unrelated speech.
4. If Narrator is already running, **do not toggle or terminate** it
   through automation. Have the attending verifier explicitly manage
   their own session. Use the standard `Windows+Ctrl+Enter` toggle to
   start Narrator only when it was initially off. Never launch the
   executable with an unreviewed elevation request.

## Actual application speech checklist

Run the exact Release product in the test-owned folder and use keyboard
navigation, not a script that merely queries `AutomationProperties.Name`.
The verifier must hear the speech and may use Narrator's live Speech
Recap as a corroborating **spoken-phrase** transcript.

| Step | Focus/action | Required human-observed spoken semantics |
| --- | --- | --- |
| 1 | Enter the filter rule manager | Filter management control has a meaningful role/name rather than an unlabeled button |
| 2 | Focus rule name and create `코드 파일` | Rule name/editor is identified; after save, selected preset name is conveyed |
| 3 | Focus color selector and choose `파랑` | Control/selected option conveys **파랑** rather than only a color swatch |
| 4 | Focus icon selector and choose `별` | Category **별** is announced; not only “image” or a glyph |
| 5 | Save and apply `*.cpp;*.h` | Saved filter can be selected; list rows appear as expected |
| 6 | Focus/select `alpha.cpp` and `beta.h` | Actual spoken row context contains the preset name, category color and icon meaning, with distinguishable focus/selection feedback |
| 7 | Change selection and keyboard focus | The announced row/selection tracks the *new* focused item, not a stale label |

Repeat representative color/icon combinations as required by the
release scope; do not infer that the single blue/star example covers
green/orange/red, pin/flag/tag, every voice or every Narrator setting.

### Speech Recap and audio evidence

Microsoft documents `Narrator key+Alt+X` to display the last 500 spoken
phrases and live transcription; the default Narrator key is **Insert
or Caps Lock**. Use it while Narrator is already running. Speech Recap
can corroborate the exact announced label, but its mere appearance does
not prove audible hardware playback. **Actually listen** to the output;
when auditing audio programmatically, require an independently isolated
and privacy-reviewed recording source, not just a working endpoint or
a process list.

Do **not** use `Narrator key+Ctrl+X` in an unattended test: it copies
the last phrase to the machine-wide clipboard and changes user-global
state. Do not enable Narrator telemetry or write user settings as a
side effect. If the Speech Recap cannot be observed through an
accessibility/elevation boundary, record that failure without
substituting the app's own UIA names as the spoken phrase.

References:
- [Microsoft Narrator startup/shutdown](https://support.microsoft.com/en-us/accessibility/windows/narrator/chapter-1-introducing-narrator)
- [Microsoft Narrator speech recap and live transcription](https://support.microsoft.com/en-us/accessibility/windows/narrator/chapter-2-narrator-basics)

## Exit and acceptance evidence

- Use **Narrator+Esc** or, when it was initially off, the same
  `Windows+Ctrl+Enter` shortcut to stop it. Confirm the initial
  running state is restored by independent process/session inspection.
  Never indiscriminately kill a preexisting Narrator process.
- Close only the test-owned flyExplorer window, wait for normal exit,
  compare the existing user settings hashes, and remove only the
  verified nonlinked test-owned folder when no owned processes remain.
  Keep bounded textual evidence; do not commit raw desktop screenshots
  or audio containing unrelated personal information.
- Report **PASS** only with a human- or otherwise independently verified
  *actual spoken* rule name, color, icon category and selection
  announcements plus normal cleanup. Report **BLOCKED/NOT TESTED** if
  Narrator launches but the spoken content or actual playback cannot
  be confirmed. Keep UIA and audio acceptance distinct.
