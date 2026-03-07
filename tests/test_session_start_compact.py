"""session_start.py _handle_compact 경로 단위 테스트."""

from __future__ import annotations

import json
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.session.state import (
    PlaneContext,
    ScopeState,
    SessionState,
    SessionStats,
)


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _make_state(
    session_id: str = "test-session",
    summary: str = "테스트 목표",
    work_item_ids: list[str] | None = None,
    project_id: str = "proj-123",
) -> SessionState:
    """테스트용 SessionState를 생성한다."""
    state = SessionState(session_id=session_id)
    state.scope = ScopeState(summary=summary, topics=["topic1"], expanded_topics=[])
    state.stats = SessionStats(total_prompts=5, drift_warnings=1, files_touched=["a.py"])
    state.plane_context = PlaneContext(
        project_id=project_id,
        work_item_ids=work_item_ids if work_item_ids is not None else [],
    )
    return state


def _make_config(api_key: str = "test-key", workspace_slug: str = "ws", project_id: str = "proj-123"):
    """테스트용 Config mock을 생성한다."""
    cfg = MagicMock()
    cfg.api_key = api_key
    cfg.workspace_slug = workspace_slug
    cfg.project_id = project_id
    cfg.base_url = "https://api.plane.so"
    return cfg


def _run_compact(session_id: str = "test-session") -> dict:
    """_handle_compact를 실행하고 stdout JSON을 파싱해 반환한다."""
    from oh_my_kanban.hooks.session_start import _handle_compact

    captured = StringIO()
    with patch("sys.stdout", captured):
        _handle_compact(session_id)

    output = captured.getvalue().strip()
    return json.loads(output)


# ── 테스트 1: build_plane_context 반환값이 additionalContext에 포함됨 ─────────

class TestCompactIncludesPlaneContext:
    """compact 호출 시 Plane WI 내용이 additionalContext에 주입되는지 검증."""

    def test_wi_content_in_additional_context(self):
        """build_plane_context 반환값이 additionalContext에 포함된다."""
        wi_content = "### WI: 테스트 작업\n상태: In Progress"
        state = _make_state(work_item_ids=["wi-001"])

        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_start.save_session"),
            patch("oh_my_kanban.hooks.session_start.load_config", return_value=_make_config()),
            patch(
                "oh_my_kanban.hooks.session_start.build_plane_context",
                return_value=(wi_content, []),
            ),
        ):
            result = _run_compact()

        additional = result["hookSpecificOutput"]["additionalContext"]
        assert "[Plane Work Item 상세]" in additional
        assert "### WI: 테스트 작업" in additional
        assert "상태: In Progress" in additional

    def test_additional_context_key_exists(self):
        """출력 JSON에 additionalContext 키가 반드시 존재한다."""
        state = _make_state(work_item_ids=["wi-001"])

        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_start.save_session"),
            patch("oh_my_kanban.hooks.session_start.load_config", return_value=_make_config()),
            patch(
                "oh_my_kanban.hooks.session_start.build_plane_context",
                return_value=("### WI: X\n상태: Done", []),
            ),
        ):
            result = _run_compact()

        assert "hookSpecificOutput" in result
        assert "additionalContext" in result["hookSpecificOutput"]


# ── 테스트 2: api_key 없을 때 build_plane_context 호출 안 됨 ──────────────────

class TestCompactSkipsPlaneWhenNoApiKey:
    """Plane API 미설정 시 build_plane_context를 호출하지 않는다."""

    @pytest.mark.parametrize("api_key", ["", None])
    def test_no_api_key_skips_build(self, api_key):
        """api_key가 비어있거나 None이면 build_plane_context를 호출하지 않는다."""
        state = _make_state(work_item_ids=["wi-001"])
        cfg = _make_config(api_key=api_key or "")
        # api_key 빈 문자열이면 조건에서 제외됨

        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_start.save_session"),
            patch("oh_my_kanban.hooks.session_start.load_config", return_value=cfg),
            patch(
                "oh_my_kanban.hooks.session_start.build_plane_context"
            ) as mock_build,
        ):
            _run_compact()

        mock_build.assert_not_called()

    def test_no_workspace_slug_skips_build(self):
        """workspace_slug가 없으면 build_plane_context를 호출하지 않는다."""
        state = _make_state(work_item_ids=["wi-001"])
        cfg = _make_config(workspace_slug="")

        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_start.save_session"),
            patch("oh_my_kanban.hooks.session_start.load_config", return_value=cfg),
            patch(
                "oh_my_kanban.hooks.session_start.build_plane_context"
            ) as mock_build,
        ):
            _run_compact()

        mock_build.assert_not_called()


# ── 테스트 3: build_plane_context 빈 문자열 반환 시 섹션 없음 ─────────────────

class TestCompactEmptyPlaneContent:
    """build_plane_context가 빈 문자열을 반환하면 Plane 섹션이 출력에 없다."""

    def test_empty_plane_content_no_section(self):
        """빈 문자열 반환 시 '[Plane Work Item 상세]' 섹션이 없다."""
        state = _make_state(work_item_ids=["wi-001"])

        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_start.save_session"),
            patch("oh_my_kanban.hooks.session_start.load_config", return_value=_make_config()),
            patch(
                "oh_my_kanban.hooks.session_start.build_plane_context",
                return_value=("", []),
            ),
        ):
            result = _run_compact()

        additional = result["hookSpecificOutput"]["additionalContext"]
        assert "[Plane Work Item 상세]" not in additional

    def test_empty_plane_content_still_outputs_context(self):
        """빈 문자열이어도 기본 세션 컨텍스트는 출력된다."""
        state = _make_state(work_item_ids=["wi-001"])

        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_start.save_session"),
            patch("oh_my_kanban.hooks.session_start.load_config", return_value=_make_config()),
            patch(
                "oh_my_kanban.hooks.session_start.build_plane_context",
                return_value=("", []),
            ),
        ):
            result = _run_compact()

        additional = result["hookSpecificOutput"]["additionalContext"]
        assert "[omk: 컨텍스트 압축 후 복원]" in additional


# ── 테스트 4: work_item_ids 빈 리스트일 때 build_plane_context 호출 안 됨 ─────

class TestCompactSkipsWhenNoWorkItems:
    """work_item_ids가 빈 리스트이면 build_plane_context를 호출하지 않는다."""

    def test_empty_work_item_ids_skips_build(self):
        """빈 work_item_ids일 때 build_plane_context가 호출되지 않는다."""
        state = _make_state(work_item_ids=[])

        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_start.save_session"),
            patch("oh_my_kanban.hooks.session_start.load_config", return_value=_make_config()),
            patch(
                "oh_my_kanban.hooks.session_start.build_plane_context"
            ) as mock_build,
        ):
            _run_compact()

        mock_build.assert_not_called()

    def test_empty_work_item_ids_still_outputs_base_context(self):
        """work_item_ids 없어도 기본 압축 복원 컨텍스트는 출력된다."""
        state = _make_state(work_item_ids=[])

        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_start.save_session"),
            patch("oh_my_kanban.hooks.session_start.load_config", return_value=_make_config()),
        ):
            result = _run_compact()

        additional = result["hookSpecificOutput"]["additionalContext"]
        assert "[omk: 컨텍스트 압축 후 복원]" in additional
        assert "[Plane Work Item 상세]" not in additional


# ── 테스트 5: session 없을 때 exit_fail_open 호출 ─────────────────────────────

class TestCompactExitsWhenNoSession:
    """load_session이 None을 반환할 때 exit_fail_open이 호출된다."""

    def test_no_session_calls_exit_fail_open(self):
        """세션이 없으면 exit_fail_open이 호출되고 SystemExit(0)이 발생한다."""
        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=None),
            patch(
                "oh_my_kanban.hooks.session_start.exit_fail_open",
                side_effect=SystemExit(0),
            ) as mock_exit,
        ):
            with pytest.raises(SystemExit) as exc_info:
                from oh_my_kanban.hooks.session_start import _handle_compact
                _handle_compact("nonexistent-session")

        mock_exit.assert_called_once()
        assert exc_info.value.code == 0

    def test_no_session_does_not_call_build_plane_context(self):
        """세션이 없으면 build_plane_context를 호출하지 않는다."""
        with (
            patch("oh_my_kanban.hooks.session_start.load_session", return_value=None),
            patch("oh_my_kanban.hooks.session_start.exit_fail_open"),
            patch(
                "oh_my_kanban.hooks.session_start.build_plane_context"
            ) as mock_build,
        ):
            from oh_my_kanban.hooks.session_start import _handle_compact
            _handle_compact("nonexistent-session")

        mock_build.assert_not_called()
