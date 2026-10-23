# PX12 native Windows Explorer / flyExplorer address visual comparison — 2026-10-23

## Scope and decision

**Result: partial visual review complete; PX12 visual acceptance NOT PASS.**
This report preserves the last stopped task's actual captures, comparison scope,
and failure boundary rather than re-running unchanged functional tests or
asserting Explorer-wide parity. Only the app's synthetic owned fixture was used.
The product C++ navigation code was not modified for this comparison.

- Exact application/harness source: `f0980b515f47288c14b6aded2d1829e2620d421e`.
- Windows focused visual run: [central #39911686462](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39911686462), `gui-address-visual-compare`.
- Central Quality [#39911150110](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39911150110) PASS; Python 4-file syntax and 1/1 visual-source ownership contract [#39911536117](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39911536117) PASS.
- Runner-health PASS (545 ms), GUI dependencies PASS (155 ms), actual Release build PASS (187,776 ms); visual probe **FAIL** (13,730 ms, exit 1), because the owned application subsequently exited abnormally.
- Windows reported build `10.0.26300`, **dark** apps theme, **96 DPI**, equal requested **940×620** window rectangles. Test fixture `Left/Nested` and a unique owned marker; no system-wide theme or DPI changes.
- Native Explorer was a newly created `CabinetWClass` top-level window, separately checked against the pre-existing HWND set and against unique synthetic marker content. Only this new window received keyboard input and close; existing user Explorer HWNDs were not targeted.

## Actual captured pixels and human review

The three original PNG frames are preserved as bounded base64 records in the
exact test-owned GUI log archived with the failed central Windows workspace.
Their identity and SHA-256 were re-checked in read-only [#39913822771](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39913822771):

| Captured state | Image dimensions | SHA-256 |
| --- | --- | --- |
| flyExplorer, address editor with visible `Nested — Left` candidate | 932×306 | `87d20eadbfadd8262ce5b1bff4b19153388bc911b6e1d6bb586796e0bca1b11c` |
| New Windows Explorer, focused address editor (header-only privacy crop) | 932×78 | `88b99fa4b1ec6674d40219b3c2c470fbfc13fe583793e9c61f340a8548449113` |
| flyExplorer, returned committed breadcrumb display | 932×176 | `c75592ca88f97b9638bd2a738119e7695ae63c3b13bc2fdf9b3f01eb77de8da8` |

Reviewed the actual images, not a XAML mockup. The flyExplorer candidate is
legible, below the address editor, and no obvious collision with its surrounding
command controls is evident at this one window size/DPI/theme. Its editor
truncates a long synthetic path due to narrower chrome; the native Explorer
header leaves more horizontal room for the editable path. This layout
difference alone is **not** a confirmed defect because flyExplorer has different
two-pane/command surfaces. After dismissing the candidate, the flyExplorer
breadcrumb reappeared and did not show an obvious overlap in the captured
header. No quantitative pixel-perfect equivalence is asserted across
different applications, fonts, control trees, or crop heights.

## Address-feature comparison, evidence boundaries

| Behavior | flyExplorer evidence | Native Explorer evidence / disposition |
| --- | --- | --- |
| `Ctrl+L` opens a keyboard-focused editable address | Real UIA/keyboard and pixels observed in the focused visual probe | Real focused Edit in the newly owned-window reference: observed |
| Partial absolute path input | `Left\\N` on test fixture, visible 1 in-memory `Nested` candidate | Same synthetic prefix placed into focused Edit; no assumption that the same candidate list exists |
| Visible candidate list and candidate selection | flyExplorer `Nested — Left` pixels; separate functional GUI [#39907990501](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39907990501) passed candidate Invoke, committed chrome, failure recovery, normal exit | Native suggestion list deliberately outside privacy-safe header crop: **NOT compared** |
| Escape / returning to committed path | flyExplorer two Escape actions and subsequent breadcrumb pixels observed | Native one Escape action observed; no full native history or directory-state oracle: **PARTIAL** |
| Long path appearance at 940 px | Compact address area, visible truncation | Wider address control, relatively more of test path visible; intentional design difference not an accepted parity defect |
| Enter, UNC, shell:, path quoting, Back/Forward, deep autocomplete, IME, keyboard arrows and click navigation in native Explorer | Existing flyExplorer evidence may cover subsets, but **not this paired visual run** | **NOT compared**, no Explorer-wide acceptance |
| Light theme, High Contrast, 125/150/200% DPI, Narrator spoken result | **NOT run** | **NOT run**; user-excluded/stopped gates remain excluded |

## Actual shutdown failure and separate G01 classification

After all three visual frames and probe-side completion markers,
`tests/winui/test_shell_gui.py` reported `OWNED_WINUI_SHELL_EXIT 3221225477`
(`0xC0000005` access violation), then raised on its requirement that
the owned application terminate with code 0. The failing visual run cannot
be reclassified as GUI/visual acceptance PASS.

Read-only Windows Application Error Event 1000 for the same owned process
([#39912873511](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39912873511)):
UTC **2026-10-23T06:32:05.6730856Z**, executable `flyExplorer.exe`,
PID `9492`, reported fault module `Microsoft.UI.Xaml.dll`,
exception `c0000005`, module offset `00000000000a0981`.
The module name and offset **do not establish a root cause or causality from
the visual capture or PX12 product change**. The product has separately
documented intermittent G01 shutdown risk; treat this as a real observed
shutdown failure, not as proof that any specific C++ or WinUI component is
defective.

Because the source harness asserts normal exit **before** the original
user-profile sentinel and synthetic-fixture retirement lines, those post-exit
sentinels were **not executed**, and their results are **UNVERIFIED**, not PASS.
Read-only inventory [#39913822771](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39913822771)
found one leftover test-owned synthetic fixture. After checking both unique
marker files, exact ignored scratch ancestry, absence of symlinks/protected
files and live matching app processes, the isolated fixture was retired in
[#39914030926](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39914030926):
**1/1 owned fixture cleanup PASS**, original three screenshot log frames
preserved. This cleanup operation did not touch user files. It is not
retrospective evidence that the failed GUI run's profile sentinel passed.

## Decision and next bounded actions

- **No PX12 visual layout code change** without a demonstrated address-area
  defect. The current one-size dark 96-DPI review supplies observations,
  not universal Windows 11 address-bar equivalence.
- **Do not replay the same visual suite/Release build blindly.** First obtain
  an isolated, causal crash stack or independently justified one-shot scoped
  comparison after a concrete harness/product change; re-check exact-source
  executable provenance if reusing retained artifacts.
- Treat any future observed crash as a separate, narrowly scoped G01
  diagnostic. The historical G01 intermittent reproduction task is otherwise
  deferred; G03–G05 are excluded and G07 remains stopped.
- Previous exact-source PX12 functional GUI [#39907990501](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39907990501)
  remains accepted at its own SHA. The newer visual run's failure does not
  erase or silently extend that existing functional evidence.
