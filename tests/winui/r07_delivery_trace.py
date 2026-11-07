"""R07 소유 런타임 UI 전달 로그에서 관측된 마지막 경계를 분류한다.

UI 스레드와 worker가 순서가 다른 로그를 쓸 수 있으므로 줄 순서를
시간순 증거로 취급하지 않는다. 기록이 없다는 사실은 실패 확증이 아니다.
"""


_STAGES = frozenset({
    "POST_CALLED", "POST_ACCEPTED", "POST_REJECTED", "POST_EXCEPTION",
    "UI_TASK_ENTERED", "UI_TASK_DISPATCH", "ON_FILE_COMPLETION",
})


def observed_delivery_boundary(lines: list[str] | None) -> str:
    if lines is None:
        return "TRACE_FILE_MISSING"
    observed = set(lines)
    if any(line and line not in _STAGES for line in observed):
        return "TRACE_INVALID"
    if "POST_ACCEPTED" in observed and (
        "POST_REJECTED" in observed or "POST_EXCEPTION" in observed
    ):
        return "POST_RESULT_CONFLICT"
    if "POST_CALLED" not in observed:
        return "POST_NOT_OBSERVED"
    if "POST_EXCEPTION" in observed:
        return "POST_EXCEPTION"
    if "POST_REJECTED" in observed:
        return "POST_REJECTED"
    if "POST_ACCEPTED" not in observed:
        return "POST_RESULT_NOT_OBSERVED"
    if "UI_TASK_ENTERED" not in observed:
        return "UI_TASK_NOT_OBSERVED"
    if "UI_TASK_DISPATCH" not in observed:
        return "UI_TASK_DISPATCH_NOT_OBSERVED"
    if "ON_FILE_COMPLETION" not in observed:
        return "FILE_COMPLETION_NOT_OBSERVED"
    return "FILE_COMPLETION_OBSERVED"
