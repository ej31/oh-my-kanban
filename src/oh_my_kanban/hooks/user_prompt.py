"""UserPromptSubmit 훅: 프롬프트 카운트, 스코프 초기화, 드리프트 감지.

Claude Code가 이 스크립트를 독립 프로세스로 실행한다.
stdin: {"session_id": "...", "prompt": "...", ...}
stdout: JSON (additionalContext 주입용 — 드리프트 경고 시)
exit code 0: 항상 (fail-open)
"""

from __future__ import annotations

import sys

from oh_my_kanban.hooks.common import (
    exit_fail_open,
    get_session_id,
    output_context,
    read_hook_input,
)
from oh_my_kanban.session.manager import load_session, save_session
from oh_my_kanban.session.scope import (
    compute_drift_score,
    expand_scope,
    init_scope,
    should_suppress_warning,
)
from oh_my_kanban.session.state import TimelineEvent, now_iso


def main() -> None:
    """UserPromptSubmit 훅 메인. 예외는 모두 catch해 fail-open으로 처리한다."""
    try:
        hook_input = read_hook_input()
        session_id = get_session_id(hook_input)
        if not session_id:
            exit_fail_open()
            return

        state = load_session(session_id)
        if state is None:
            exit_fail_open()
            return
        if state.opted_out:
            exit_fail_open()
            return

        # 1. 프롬프트 카운트
        prompt_text = str(hook_input.get("prompt", ""))
        state.stats.total_prompts += 1

        # 2. 스코프 초기화 시도 (첫 번째 또는 scope가 비어있을 때)
        if not state.scope.tokens:
            init_scope(state, prompt_text)

        # 3. 쿨다운 처리
        if state.stats.cooldown_remaining > 0:
            state.stats.cooldown_remaining -= 1
            save_session(state)
            sys.exit(0)

        # 4. 스코프가 충분히 초기화되지 않으면 바로 저장 후 종료
        if not state.scope.tokens:
            save_session(state)
            sys.exit(0)

        # 5. 드리프트 감지 (세션 sensitivity 값 전달)
        drift = compute_drift_score(
            state.scope,
            prompt_text,
            state.stats.files_touched,
            sensitivity=state.config.sensitivity,
        )

        # suppressed 판정: 프롬프트에 명시적 전환 패턴이 있으면 경고 억제
        if drift.level in ("significant", "major"):
            drift.suppressed = should_suppress_warning(prompt_text)

        # 6. 드리프트 레벨별 처리
        if drift.level == "none":
            pass  # 정상
        elif drift.level == "minor":
            if state.config.auto_expand:
                expand_scope(state, prompt_text)
                state.stats.scope_expansions += 1
                state.timeline.append(
                    TimelineEvent(
                        timestamp=now_iso(),
                        type="scope_expanded",
                        summary=f"스코프 확장 (minor drift, score={drift.score:.3f})",
                        drift_score=drift.score,
                        drift_level="minor",
                    )
                )
        elif drift.level in ("significant", "major"):
            if drift.suppressed:
                # suppressed -> minor처럼 scope 확장, 이력은 남김
                if state.config.auto_expand:
                    expand_scope(state, prompt_text)
                    state.stats.scope_expansions += 1
                state.timeline.append(
                    TimelineEvent(
                        timestamp=now_iso(),
                        type="scope_expanded",
                        summary=f"스코프 확장 (suppressed {drift.level}, score={drift.score:.3f})",
                        drift_score=drift.score,
                        drift_level=drift.level,
                    )
                )
            else:
                # 경고 주입
                state.stats.drift_warnings += 1
                state.stats.cooldown_remaining = state.config.cooldown
                state.timeline.append(
                    TimelineEvent(
                        timestamp=now_iso(),
                        type="drift_detected",
                        summary=f"드리프트 감지 (level={drift.level}, score={drift.score:.3f})",
                        drift_score=drift.score,
                        drift_level=drift.level,
                    )
                )
                # alpha 모드: additionalContext로 경고 주입 (사용자 미표시)
                warning = (
                    f"[omk drift 경고] 현재 요청이 세션 범위에서 벗어난 것으로 보입니다 "
                    f"(level={drift.level}, score={drift.score:.2f}). "
                    f"범위: {state.scope.summary[:50] if state.scope.summary else '미설정'}"
                )
                output_context("UserPromptSubmit", warning)

        # 7. 타임라인에 prompt 이벤트 추가
        state.timeline.append(
            TimelineEvent(
                timestamp=now_iso(),
                type="prompt",
                summary=prompt_text[:100] if prompt_text else "(빈 프롬프트)",
                drift_score=drift.score if state.scope.tokens else None,
            )
        )

        save_session(state)

    except Exception as e:
        print(
            f"[omk] UserPromptSubmit 훅 예외 (fail-open): {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        exit_fail_open()


if __name__ == "__main__":
    main()
