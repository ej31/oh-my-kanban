"""ST-19: 세션 재개 핸드오프 표시 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oh_my_kanban.session.state import SessionState


_MOD = "oh_my_kanban.hooks.session_start"


def _make_state(handoff_note: str = "", source: str = "resume") -> SessionState:
    state = SessionState(session_id="sess-resume-001")
    state.handoff_note = handoff_note
    state.scope.summary = "이전 세션 목표"
    state.stats.total_prompts = 5
    return state


def _make_cfg():
    cfg = MagicMock()
    cfg.api_key = "key"
    cfg.workspace_slug = "ws"
    cfg.project_id = "proj-uuid"
    cfg.base_url = "https://plane.example.com"
    cfg.drift_sensitivity = 0.5
    cfg.drift_cooldown = 3
    cfg.format_preset = "normal"
    return cfg


class TestSessionResumeHandoff:
    def test_shows_handoff_note_on_resume(self):
        """재개 세션에서 handoff_note가 있으면 systemMessage로 표시한다."""
        state = _make_state(handoff_note="refresh_token 미완성. token_store.py 36번줄부터.")
        hook_input = {"session_id": "sess-resume-001", "source": "resume"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.get_session_id", return_value="sess-resume-001"),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.load_config", return_value=_make_cfg()),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.output_system_message") as mock_sys_msg,
            patch(f"{_MOD}.output_context"),
            patch(f"{_MOD}._inject_new_session_wi_guidance"),
        ):
            from oh_my_kanban.hooks.session_start import main
            main()

        # output_system_message가 최소 1번 호출되어야 함 (핸드오프 메모)
        called_msgs = [str(call_args[0][0]) for call_args in mock_sys_msg.call_args_list]
        assert any("이전 세션 메모" in m for m in called_msgs), \
            f"핸드오프 메모 메시지를 찾지 못했습니다. 호출된 메시지: {called_msgs}"

    def test_shows_handoff_note_content(self):
        """핸드오프 메모 내용이 systemMessage에 포함된다."""
        note = "redis 연결 오류 수정 필요. config.py 참고."
        state = _make_state(handoff_note=note)
        hook_input = {"session_id": "sess-resume-001", "source": "resume"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.get_session_id", return_value="sess-resume-001"),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.load_config", return_value=_make_cfg()),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.output_system_message") as mock_sys_msg,
            patch(f"{_MOD}.output_context"),
            patch(f"{_MOD}._inject_new_session_wi_guidance"),
        ):
            from oh_my_kanban.hooks.session_start import main
            main()

        messages = [str(c[0][0]) for c in mock_sys_msg.call_args_list]
        assert any(note[:30] in msg for msg in messages)

    def test_no_handoff_message_when_note_empty(self):
        """handoff_note가 없으면 핸드오프 관련 systemMessage를 출력하지 않는다."""
        state = _make_state(handoff_note="")
        state.plane_context.work_item_ids = []  # WI 없음 (notify_success 차단)
        hook_input = {"session_id": "sess-resume-001", "source": "resume"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.get_session_id", return_value="sess-resume-001"),
            patch(f"{_MOD}.load_session", return_value=state),
            patch(f"{_MOD}.load_config", return_value=_make_cfg()),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.output_system_message") as mock_sys_msg,
            patch(f"{_MOD}.output_context"),
            patch(f"{_MOD}._inject_new_session_wi_guidance"),
        ):
            from oh_my_kanban.hooks.session_start import main
            main()

        # 핸드오프 메모 관련 systemMessage가 없어야 함
        called_msgs = [str(c[0][0]) for c in mock_sys_msg.call_args_list]
        assert not any("이전 세션 메모" in m for m in called_msgs)

    def test_no_handoff_message_on_startup(self):
        """startup 소스에서는 handoff_note가 있어도 핸드오프 메시지를 표시하지 않는다."""
        state = _make_state(handoff_note="이 메모는 표시 안 됨")
        state.plane_context.work_item_ids = []
        hook_input = {"session_id": "sess-resume-001", "source": "startup"}

        with (
            patch(f"{_MOD}.read_hook_input", return_value=hook_input),
            patch(f"{_MOD}.get_session_id", return_value="sess-resume-001"),
            patch(f"{_MOD}.load_session", return_value=None),  # 신규 세션
            patch(f"{_MOD}.create_session", return_value=state),
            patch(f"{_MOD}.load_config", return_value=_make_cfg()),
            patch(f"{_MOD}.save_session"),
            patch(f"{_MOD}.output_system_message") as mock_sys_msg,
            patch(f"{_MOD}.output_context"),
            patch(f"{_MOD}._inject_new_session_wi_guidance"),
        ):
            from oh_my_kanban.hooks.session_start import main
            main()

        called_msgs = [str(c[0][0]) for c in mock_sys_msg.call_args_list]
        assert not any("이전 세션 메모" in m for m in called_msgs)
