# flyExplorer current WinUI GUI and visual retest workflow

Use the canonical current product and test-owned fixtures only.

## Acceptance rule

For any user-visible UI change, screenshot/final-pixel review is a mandatory
acceptance gate. Functional/UIA automation is necessary but is not sufficient
to declare the UI change complete.

A pure behavior-preserving refactor that does not alter composited pixels does
not require fresh visual screenshots; it still requires the relevant GUI
regression and normal process exit.

## Automated owned checks

From the repository root:

    python -X utf8 tools\winui\run_checks.py source
    python -X utf8 tools\winui\run_checks.py build --configuration Release
    python -X utf8 tools\winui\run_checks.py gui --configuration Release

For the v7 Window Tab/session slice:

    python -X utf8 tools\winui\run_checks.py gui --configuration Release --v7-window-tabs-only

A GUI PASS must include a normal owned process exit. Do not accept a functional
sentinel followed by a crash exit code.

## Mandatory BEFORE / AFTER capture

Before changing user-visible pixels, capture the actual current product in the
state being changed. After implementation, capture the actual changed product
under like-for-like conditions.

Record with each comparison:
- source/binary revision;
- Debug or Release configuration;
- Windows build;
- theme;
- DPI/scaling;
- window dimensions;
- test-owned folder/view fixture;
- relevant pane/tab/focus/selection state.

Capture additional AFTER states when the change affects them, for example:
active/inactive pane, keyboard focus, selected/disabled control, expanded or
collapsed surface, empty/loading/error state, dialog/menu, narrow window or
split-pane layout.

Do not substitute a mockup, static XAML inspection or source-level assertion for
the actual composited product pixels.

## Visual review checklist

Review the captured pixels for:
- alignment, spacing, padding and visual hierarchy;
- typography, clipping, truncation and unintended wrapping;
- overlap and minimum usable control dimensions;
- icon/glyph alignment and consistent borders/dividers;
- focus, selection, hover and disabled-state readability where applicable;
- status/progress visibility;
- light/dark theme consistency and contrast where exercised;
- narrow-window and dual-pane density/behavior;
- consistency with the public Windows 11 File Explorer interaction/chrome
  reference without requiring a pixel clone.

Classify differences as intended or unintended. A material unintended visual
regression blocks visual acceptance.

## Mandatory feedback loop

If review finds a material defect:

    implement
      -> run actual GUI
      -> capture screenshot
      -> inspect/compare pixels
      -> fix
      -> run actual GUI again
      -> recapture
      -> re-review

Repeat until the changed state has no known blocking visual regression or an
explicit environment blocker is recorded. Taking one screenshot without
reviewing and acting on it is not sufficient.

## Functional vs visual evidence

Report these gates separately:

- **Functional GUI acceptance** — input delivery, state transition, expected
  command behavior, accessibility/UIA interaction where applicable, and normal
  process exit.
- **Visual acceptance** — actual screenshot/final-pixel inspection and
  BEFORE/AFTER comparison.

If no final-pixel review occurred, report exactly:

    VISUAL ACCEPTANCE: NOT TESTED

Do not collapse a functional PASS into a visual PASS.

## Visual comparisons

Use the same revision/binary context, Windows build, DPI/scaling, theme, window
dimensions and folder/view fixture as closely as possible. If a condition must
differ, record the difference and do not present the comparison as like-for-like.

Capture only synthetic/test-owned paths. Never commit screenshots containing
personal filenames or private desktop content. Prefer ignored local evidence
under logs/ or bounded CI artifacts rather than product-source PNGs.

## Theme, scale and accessibility gates

For layout/theme/scale-sensitive UI work, exercise the relevant environments
that are actually available. Do not infer a PASS for an unavailable one.

Actual 125/150/200% display scaling, High Contrast ON, human Narrator/Korean
IME behavior and physical pointer drag remain separate manual/environment gates
unless the current task explicitly exercises them. RDP restrictions,
source-level support or code-level RasterizationScale behavior do not certify
them.

## Evidence language

Use PASS, FAIL, NOT TESTED, ENVIRONMENT BLOCKED, or similarly explicit states.
Keep source/compile/runtime/functional-GUI/visual evidence distinct. A
user-visible UI task is not fully accepted while its required visual gate is
NOT TESTED or FAIL.
