"""user_prompt.py UserPromptSubmit 훅 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.session.state import (
    DriftResult,
    ScopeState,
    SessionConfig,
    SessionState,
    SessionStats,
)

# 테스트 대상 모듈 경로 (mock 패치용)
_MOD = "oh_my_kanban.hooks.user_prompt"


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────


def _make_state(
    session_id: str = "test-session",
    opted_out: bool = False,
    tokens: list[str] | None = None,
    cooldown: int = 0,
    auto_expand: bool = True,
    cooldown_config: int = 3,
    total_prompts: int = 0,
    drift_warnings: int = 0,
    scope_expansions: int = 0,
    files_touched: list[str] | None = None,
    summary: str = "테스트 세션 목표",
) -> SessionState:
    """테스트용 SessionState를 생성한다."""
    state = SessionState(session_id=session_id)
    state.opted_out = opted_out
    state.scope = ScopeState(
        summary=summary,
        tokens=tokens if tokens is not None else [],
        keywords=["test", "keyword"] if tokens else [],
    )
    state.stats = SessionStats(
        total_prompts=total_prompts,
        drift_warnings=drift_warnings,
        scope_expansions=scope_expansions,
        cooldown_remaining=cooldown,
        files_touched=files_touched if files_touched is not None else [],
    )
    state.config = SessionConfig(
        sensitivity=0.5,
        cooldown=cooldown_config,
        auto_expand=auto_expand,
    )
    return state


def _make_drift(
    score: float = 1.0,
    level: str = "none",
    suppressed: bool = False,
) -> DriftResult:
    """테스트용 DriftResult를 생성한다."""
    return DriftResult(
        score=score,
        level=level,
        components={"tf_cosine": score, "keyword_jaccard": score, "file_jaccard": score},
        suppressed=suppressed,
    )


def _run_main(hook_input: dict) -> None:
    """user_prompt.main()을 실행한다. stdin mock 포함."""
    from oh_my_kanban.hooks.user_prompt import main

    main()


# ── 1. opted_out 세션 -> 즉시 exit 0, save 미호출 ───────────────────────────


class TestOptedOutSession:
    def test_opted_out_exits_without_save(self):
        """opted_out 세션이면 save_session을 호출하지 않고 exit 0한다."""
        state = _make_state(opted_out=True)
        hook_input = {"session_id": "test-session", "prompt": "hello"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session") as mock_save,
            patch(f"{_MOD}.exit_fail_open") as mock_exit,
        ):
            _run_main(hook_input)

        mock_exit.assert_called_once()
        mock_save.assert_not_called()


# ── 2. session_id 없음 -> exit 0 (fail-open) ────────────────────────────────


class TestNoSessionId:
    def test_no_session_id_exits_fail_open(self):
        """session_id가 빈 문자열이면 exit_fail_open이 호출된다."""
        hook_input = {"session_id": "", "prompt": "hello"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.get_session_id", return_value=""),
            patch(f"{_MOD}.exit_fail_open") as mock_exit,
            patch(f"{_MOD}.load_session") as mock_load,
        ):
            _run_main(hook_input)

        mock_exit.assert_called_once()
        mock_load.assert_not_called()


# ── 3. 세션 없음 -> exit 0 (fail-open) ──────────────────────────────────────


class TestSessionNotFound:
    def test_session_not_found_exits_fail_open(self):
        """load_session이 None을 반환하면 exit_fail_open이 호출된다."""
        hook_input = {"session_id": "nonexistent", "prompt": "hello"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=None),
            patch(f"{_MOD}.exit_fail_open") as mock_exit,
        ):
            _run_main(hook_input)

        mock_exit.assert_called_once()


# ── 4. 매 호출마다 total_prompts += 1 ───────────────────────────────────────


class TestPromptCount:
    def test_total_prompts_incremented(self):
        """호출 시 total_prompts가 1 증가한다."""
        state = _make_state(total_prompts=5, tokens=["existing", "scope", "tokens"])

        hook_input = {"session_id": "test-session", "prompt": "existing scope tokens test"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.compute_drift_score", return_value=_make_drift()),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
        ):
            _run_main(hook_input)

        assert state.stats.total_prompts == 6


# ── 5. scope.tokens 비어있고 prompt 짧음 -> scope 초기화 보류 ────────────────


class TestScopeInitShortPrompt:
    def test_short_prompt_does_not_init_scope(self):
        """토큰 부족 시 init_scope가 scope를 초기화하지 않는다 (MIN_SCOPE_TOKENS 미달)."""
        state = _make_state(tokens=[])  # scope 비어있음

        hook_input = {"session_id": "test-session", "prompt": "hi"}  # 토큰 부족

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session") as mock_save,
        ):
            with pytest.raises(SystemExit) as exc_info:
                _run_main(hook_input)

        # scope가 비어있으면 sys.exit(0) 호출됨
        assert exc_info.value.code == 0
        mock_save.assert_called_once()
        assert state.scope.tokens == []


# ── 6. scope.tokens 비어있고 prompt 충분 -> scope 초기화 ─────────────────────


class TestScopeInitSufficientPrompt:
    def test_sufficient_prompt_inits_scope(self):
        """충분한 토큰의 프롬프트로 scope가 초기화된다."""
        state = _make_state(tokens=[])

        # MIN_SCOPE_TOKENS(3) 이상의 토큰을 생성하는 프롬프트
        prompt = "implement user authentication system with JWT tokens"
        hook_input = {"session_id": "test-session", "prompt": prompt}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.compute_drift_score", return_value=_make_drift()),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
        ):
            _run_main(hook_input)

        # init_scope가 실제로 호출되어 tokens가 채워짐
        assert len(state.scope.tokens) >= 3


# ── 7. cooldown_remaining > 0 -> cooldown -= 1 후 즉시 저장+종료 ─────────────


class TestCooldownDecrement:
    def test_cooldown_decremented_and_exits(self):
        """cooldown_remaining > 0이면 1 감소 후 save + exit(0)."""
        state = _make_state(tokens=["test", "scope", "tokens"], cooldown=3)

        hook_input = {"session_id": "test-session", "prompt": "hello"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session") as mock_save,
            patch(f"{_MOD}.compute_drift_score") as mock_drift,
        ):
            with pytest.raises(SystemExit) as exc_info:
                _run_main(hook_input)

        assert exc_info.value.code == 0
        assert state.stats.cooldown_remaining == 2
        mock_save.assert_called_once()
        # 드리프트 계산은 호출되지 않아야 함
        mock_drift.assert_not_called()


# ── 8. drift level='none' -> 경고 없음, scope_expansions 미변경 ──────────────


class TestDriftNone:
    def test_no_warning_on_drift_none(self):
        """drift level이 none이면 경고 없이 정상 진행한다."""
        state = _make_state(tokens=["test", "scope", "tokens"], scope_expansions=0)

        hook_input = {"session_id": "test-session", "prompt": "test scope tokens"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.compute_drift_score", return_value=_make_drift(level="none")),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
            patch(f"{_MOD}.output_context") as mock_output,
        ):
            _run_main(hook_input)

        mock_output.assert_not_called()
        assert state.stats.scope_expansions == 0


# ── 9. drift level='minor' + auto_expand=True -> expand_scope 호출 ───────────


class TestDriftMinorAutoExpand:
    def test_minor_drift_expands_scope(self):
        """minor drift + auto_expand=True일 때 scope를 확장한다."""
        state = _make_state(tokens=["test", "scope", "tokens"], auto_expand=True)

        hook_input = {"session_id": "test-session", "prompt": "new topic discussion"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.compute_drift_score", return_value=_make_drift(score=0.5, level="minor")),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
            patch(f"{_MOD}.expand_scope") as mock_expand,
        ):
            _run_main(hook_input)

        mock_expand.assert_called_once_with(state, "new topic discussion")
        assert state.stats.scope_expansions == 1


# ── 10. drift level='minor' + auto_expand=False -> expand_scope 미호출 ───────


class TestDriftMinorNoAutoExpand:
    def test_minor_drift_no_expand_when_disabled(self):
        """minor drift + auto_expand=False일 때 expand_scope를 호출하지 않는다."""
        state = _make_state(tokens=["test", "scope", "tokens"], auto_expand=False)

        hook_input = {"session_id": "test-session", "prompt": "new topic"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.compute_drift_score", return_value=_make_drift(score=0.5, level="minor")),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
            patch(f"{_MOD}.expand_scope") as mock_expand,
        ):
            _run_main(hook_input)

        mock_expand.assert_not_called()
        assert state.stats.scope_expansions == 0


# ── 11. drift level='significant' + NOT suppressed -> 경고 주입 ──────────────


class TestDriftSignificantNotSuppressed:
    def test_significant_drift_triggers_warning(self):
        """significant drift (미억제) 시 경고가 주입되고 cooldown이 설정된다."""
        state = _make_state(
            tokens=["test", "scope", "tokens"],
            cooldown_config=3,
            summary="테스트 세션 목표",
        )

        hook_input = {"session_id": "test-session", "prompt": "completely different topic"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(
                f"{_MOD}.compute_drift_score",
                return_value=_make_drift(score=0.3, level="significant"),
            ),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
            patch(f"{_MOD}.output_system_message") as mock_output,
            patch(f"{_MOD}.load_config") as mock_cfg,
        ):
            mock_cfg.return_value.api_key = ""  # 댓글 폴링 비활성화
            _run_main(hook_input)

        assert state.stats.drift_warnings == 1
        assert state.stats.cooldown_remaining == 3
        mock_output.assert_called_once()
        call_args = mock_output.call_args
        # output_system_message(user_msg, hook_event_name, additional_context)
        assert call_args[0][1] == "UserPromptSubmit"
        assert "[omk drift 경고]" in call_args[0][2]


# ── 12. drift level='major' + NOT suppressed -> 경고 주입 ────────────────────


class TestDriftMajorNotSuppressed:
    def test_major_drift_triggers_warning(self):
        """major drift (미억제) 시 경고가 주입된다."""
        state = _make_state(tokens=["test", "scope", "tokens"], cooldown_config=5)

        hook_input = {"session_id": "test-session", "prompt": "totally unrelated"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(
                f"{_MOD}.compute_drift_score",
                return_value=_make_drift(score=0.1, level="major"),
            ),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
            patch(f"{_MOD}.output_system_message") as mock_output,
            patch(f"{_MOD}.load_config") as mock_cfg,
        ):
            mock_cfg.return_value.api_key = ""  # 댓글 폴링 비활성화
            _run_main(hook_input)

        assert state.stats.drift_warnings == 1
        assert state.stats.cooldown_remaining == 5
        mock_output.assert_called_once()
        # additional_context (3rd arg) contains level=major
        assert "level=major" in mock_output.call_args[0][2]


# ── 13. drift level='significant' + suppressed=True -> scope 확장 ────────────


class TestDriftSignificantSuppressed:
    def test_suppressed_significant_drift_expands_scope(self):
        """significant drift가 suppressed이면 경고 대신 scope를 확장한다."""
        state = _make_state(tokens=["test", "scope", "tokens"], auto_expand=True)

        hook_input = {"session_id": "test-session", "prompt": "이제 다음으로 새 기능 구현"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(
                f"{_MOD}.compute_drift_score",
                return_value=_make_drift(score=0.3, level="significant"),
            ),
            patch(f"{_MOD}.should_suppress_warning", return_value=True),
            patch(f"{_MOD}.expand_scope") as mock_expand,
            patch(f"{_MOD}.output_context") as mock_output,
        ):
            _run_main(hook_input)

        mock_expand.assert_called_once()
        assert state.stats.scope_expansions == 1
        assert state.stats.drift_warnings == 0
        mock_output.assert_not_called()


# ── 14. 타임라인에 prompt 이벤트 추가 (drift_score 포함) ─────────────────────


class TestTimelinePromptEvent:
    def test_prompt_event_added_to_timeline(self):
        """모든 호출에서 prompt 타입의 타임라인 이벤트가 추가된다."""
        state = _make_state(tokens=["test", "scope", "tokens"])

        hook_input = {"session_id": "test-session", "prompt": "test scope tokens"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.compute_drift_score", return_value=_make_drift(score=0.8)),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
        ):
            _run_main(hook_input)

        prompt_events = [e for e in state.timeline if e.type == "prompt"]
        assert len(prompt_events) == 1
        assert prompt_events[0].drift_score == 0.8
        assert prompt_events[0].summary == "test scope tokens"


# ── 15. scope_expanded 이벤트가 timeline에 추가됨 (minor+expand) ─────────────


class TestTimelineScopeExpandedEvent:
    def test_scope_expanded_event_in_timeline(self):
        """minor drift + auto_expand 시 scope_expanded 타임라인 이벤트가 추가된다."""
        state = _make_state(tokens=["test", "scope", "tokens"], auto_expand=True)

        hook_input = {"session_id": "test-session", "prompt": "new expansion topic"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.compute_drift_score", return_value=_make_drift(score=0.45, level="minor")),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
            patch(f"{_MOD}.expand_scope"),
        ):
            _run_main(hook_input)

        expanded_events = [e for e in state.timeline if e.type == "scope_expanded"]
        assert len(expanded_events) == 1
        assert "minor drift" in expanded_events[0].summary
        assert expanded_events[0].drift_score == 0.45


# ── 16. drift_detected 이벤트가 timeline에 추가됨 (significant/major) ────────


class TestTimelineDriftDetectedEvent:
    def test_drift_detected_event_in_timeline(self):
        """significant drift (미억제) 시 drift_detected 타임라인 이벤트가 추가된다."""
        state = _make_state(tokens=["test", "scope", "tokens"])

        hook_input = {"session_id": "test-session", "prompt": "unrelated topic"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(
                f"{_MOD}.compute_drift_score",
                return_value=_make_drift(score=0.25, level="significant"),
            ),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
            patch(f"{_MOD}.output_context"),
        ):
            _run_main(hook_input)

        drift_events = [e for e in state.timeline if e.type == "drift_detected"]
        assert len(drift_events) == 1
        assert "significant" in drift_events[0].summary
        assert drift_events[0].drift_score == 0.25


# ── 17. 예외 발생 시 fail-open (exit 0) ─────────────────────────────────────


class TestExceptionFailOpen:
    def test_exception_causes_fail_open(self):
        """예외 발생 시 stderr에 로그 후 exit_fail_open이 호출된다."""
        hook_input = {"session_id": "test-session", "prompt": "hello"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", side_effect=RuntimeError("DB 장애")),
            patch(f"{_MOD}.exit_fail_open") as mock_exit,
        ):
            _run_main(hook_input)

        mock_exit.assert_called_once()


# ── 18. scope가 충분히 없으면 바로 저장 후 종료 ──────────────────────────────


class TestInsufficientScopeExitsEarly:
    def test_empty_scope_after_init_attempt_saves_and_exits(self):
        """init_scope 후에도 scope가 비어있으면 save + exit(0)."""
        state = _make_state(tokens=[])

        # 토큰 부족 프롬프트 — init_scope가 scope를 채우지 못함
        hook_input = {"session_id": "test-session", "prompt": "ok"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session") as mock_save,
            patch(f"{_MOD}.compute_drift_score") as mock_drift,
        ):
            with pytest.raises(SystemExit) as exc_info:
                _run_main(hook_input)

        assert exc_info.value.code == 0
        mock_save.assert_called_once()
        mock_drift.assert_not_called()


# ── 추가: 빈 프롬프트 처리 ──────────────────────────────────────────────────


class TestEmptyPrompt:
    def test_empty_prompt_text_handled(self):
        """prompt 키가 없어도 빈 문자열로 처리된다."""
        state = _make_state(tokens=["test", "scope", "tokens"])

        hook_input = {"session_id": "test-session"}  # prompt 키 없음

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.compute_drift_score", return_value=_make_drift()),
            patch(f"{_MOD}.should_suppress_warning", return_value=False),
        ):
            _run_main(hook_input)

        prompt_events = [e for e in state.timeline if e.type == "prompt"]
        assert len(prompt_events) == 1


# ── 추가: major drift + suppressed -> scope 확장 ────────────────────────────


class TestDriftMajorSuppressed:
    def test_suppressed_major_drift_expands_scope(self):
        """major drift가 suppressed이면 경고 대신 scope를 확장한다."""
        state = _make_state(tokens=["test", "scope", "tokens"], auto_expand=True)

        hook_input = {"session_id": "test-session", "prompt": "now let's move to deployment"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.save_session"),
            patch(
                f"{_MOD}.compute_drift_score",
                return_value=_make_drift(score=0.1, level="major"),
            ),
            patch(f"{_MOD}.should_suppress_warning", return_value=True),
            patch(f"{_MOD}.expand_scope") as mock_expand,
            patch(f"{_MOD}.output_context") as mock_output,
        ):
            _run_main(hook_input)

        mock_expand.assert_called_once()
        assert state.stats.scope_expansions == 1
        assert state.stats.drift_warnings == 0
        mock_output.assert_not_called()
