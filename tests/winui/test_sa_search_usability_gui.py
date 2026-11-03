"""SA01/SA02: focused, test-owned WinUI search guidance and result viewport GUI.

Runs only through test_shell_gui's exact owned process/profile/fixture.  No OS
indexing, user Search history, global theme, personal files or clipboard writes.
"""
from pathlib import Path


def run(*, win, element, focus, eventually, left, right, owned):
    left, right = Path(left), Path(right)
    assert left.is_relative_to(owned) and right.is_relative_to(owned)
    assert (left / "readme.txt").is_file()

    focus()
    element("SearchPanelButton").invoke()
    eventually(lambda: element("SearchTermBox").is_visible(),
               "SA search panel did not open", 9)
    guidance = element("SearchModeGuidanceText")
    eventually(lambda: "직접 탐색" in guidance.window_text(),
               "SA01 default search guidance missing", 8)
    print("SA01_GUI_DIRECT_GUIDANCE=PASS", flush=True)

    element("SearchScopeBox").set_edit_text(str(left))
    element("SearchTermBox").set_edit_text("readme")
    element("SearchRunButton").invoke()
    # Search completion is reported in the always-visible status footer.
    # The existing 960x519 owned GUI intentionally clips the independent
    # SearchPanel: below-fold controls are absent from UI Automation until
    # its own ScrollViewer is moved, not evidence of missing search results.
    eventually(lambda: "검색 완료" in element("StatusText").window_text(),
               "SA02 owned search did not finish", 18)
    scroll = element("SearchPanel").wrapper_object().iface_scroll
    assert scroll.CurrentVerticallyScrollable, "SA search panel has no vertical scrollbar"

    def scroll_to(name):
        # Only scroll this test-owned flyExplorer SearchPanel. Do not resize
        # another window, change global settings or bypass real GUI controls.
        for percent in (100, 80, 60, 40, 20, 0):
            scroll.SetScrollPercent(-1, percent)
            candidate = element(name)
            if candidate.exists(timeout=.2) and candidate.is_visible():
                return candidate
        raise AssertionError("SA control is unreachable after owned panel scroll: " + name)

    def results():
        return [row for row in scroll_to("SearchMatches").descendants(
            control_type="ListItem") if "readme.txt" in row.window_text()]

    count_text = scroll_to("SearchCountText").window_text()
    assert "검색 결과 1개" in count_text, ("SA02 result summary incorrect", count_text)
    eventually(lambda: len(results()) == 1,
               "SA02 owned result not visible after panel scroll", 8)
    results()[0].select()
    eventually(lambda: scroll_to("SearchLocateButton").is_enabled(),
               "SA02 selected result is not actionable", 7)
    baseline = scroll_to("SearchMatches").rectangle().height()
    label = scroll_to("SearchResultsSizeButton")
    assert "결과 펼치기" in scroll_to("SearchResultsSizeButton").window_text(), scroll_to("SearchResultsSizeButton").window_text()
    assert baseline > 0 and baseline <= 155, baseline

    label.invoke()
    expanded = eventually(
        lambda: (height if (height := scroll_to("SearchMatches").rectangle().height())
                 >= baseline + 55 else False),
        "SA02 result viewport did not expand", 8)
    assert expanded <= 270, (baseline, expanded)
    assert "결과 접기" in scroll_to("SearchResultsSizeButton").window_text()
    assert len(results()) == 1
    assert scroll_to("SearchLocateButton").is_enabled()
    assert scroll_to("SearchCountText").window_text() == count_text
    print("SA02_GUI_EXPANDED_PRESERVED_RESULT=PASS", flush=True)

    label = scroll_to("SearchResultsSizeButton")
    label.invoke()
    eventually(lambda: scroll_to("SearchMatches").rectangle().height()
               <= baseline + 15 and "결과 펼치기" in scroll_to("SearchResultsSizeButton").window_text(),
               "SA02 viewport did not collapse", 8)
    assert len(results()) == 1
    assert scroll_to("SearchLocateButton").is_enabled()
    assert scroll_to("SearchCountText").window_text() == count_text
    print("SA02_GUI_COLLAPSED_PRESERVED_SELECTION=PASS", flush=True)

    scroll_to("SearchModeBox").select(1)
    eventually(lambda: "Windows 인덱스:" in scroll_to("SearchModeGuidanceText").window_text() and
               "정규식·내용·대소문자 구분·폴더 대상 미지원" in
               scroll_to("SearchModeGuidanceText").window_text(),
               "SA01 indexed limits not shown before running search", 8)
    assert "현재 설정의 미지원 조건:" not in scroll_to("SearchModeGuidanceText").window_text()
    print("SA01_GUI_INDEXED_LIMITS_BEFORE_SUBMIT=PASS", flush=True)

    scroll_to("SearchRegexBox").toggle()
    eventually(lambda: "현재 설정의 미지원 조건:" in scroll_to("SearchModeGuidanceText").window_text()
               and "이름 정규식" in scroll_to("SearchModeGuidanceText").window_text(),
               "SA01 index regex conflict not identified", 8)
    scroll_to("SearchCaseBox").toggle()
    eventually(lambda: "대소문자 구분" in
               scroll_to("SearchModeGuidanceText").window_text().split("현재 설정의 미지원 조건:", 1)[1],
               "SA01 case sensitivity conflict not identified", 8)
    scroll_to("SearchContentBox").set_edit_text("owned-only")
    eventually(lambda: "파일 내용/내용 정규식" in
               scroll_to("SearchModeGuidanceText").window_text().split("현재 설정의 미지원 조건:", 1)[1],
               "SA01 content conflict not identified", 8)
    scroll_to("SearchTargetBox").select(1)
    eventually(lambda: "폴더 대상" in
               scroll_to("SearchModeGuidanceText").window_text().split("현재 설정의 미지원 조건:", 1)[1],
               "SA01 folder target conflict not identified", 8)
    assert scroll_to("SearchRunButton").is_enabled()
    assert scroll_to("SearchCountText").window_text() == count_text
    assert len(results()) == 1
    print("SA01_GUI_UNSUPPORTED_OPTIONS_LIVE=PASS", flush=True)

    scroll_to("SearchModeBox").select(0)
    eventually(lambda: "직접 탐색:" in scroll_to("SearchModeGuidanceText").window_text() and
               "현재 설정의 미지원 조건:" not in scroll_to("SearchModeGuidanceText").window_text(),
               "SA01 direct mode guidance did not return", 8)
    assert scroll_to("SearchCountText").window_text() == count_text
    assert len(results()) == 1
    print("SA01_GUI_MODE_RESTORE_WITHOUT_SEARCH=PASS", flush=True)
