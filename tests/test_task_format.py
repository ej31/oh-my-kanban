"""US-005: Task format system 테스트.

task_mode 설정에 따른 태스크 형식 결정 로직과 apply 엔진을 검증한다.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from oh_my_kanban.config import Config
from oh_my_kanban.provider import ProviderClient, ProviderContext
from oh_my_kanban.session.state import PlaneContext, ScopeState, SessionState
from oh_my_kanban.session.task_format import (
    TASK_MODE_FLAT,
    TASK_MODE_MAIN_SUB,
    TASK_MODE_MODULE_TASK_SUB,
    VALID_TASK_MODES,
    _VALID_TASK_MODES,
    apply_task_format,
    build_task_description,
    build_task_title,
    normalize_task_mode,
    should_create_subtask,
)


# ── normalize_task_mode ───────────────────────────────────────────────────────


class TestNormalizeTaskMode:
    """normalize_task_mode 함수 테스트."""

    def test_valid_main_sub(self) -> None:
        assert normalize_task_mode("main-sub") == "main-sub"

    def test_valid_flat(self) -> None:
        assert normalize_task_mode("flat") == "flat"

    def test_valid_module_task_sub(self) -> None:
        assert normalize_task_mode("module-task-sub") == "module-task-sub"

    def test_invalid_value_fallback(self) -> None:
        """유효하지 않은 값은 main-sub로 fallback되어야 한다."""
        assert normalize_task_mode("invalid") == TASK_MODE_MAIN_SUB

    def test_empty_string_fallback(self) -> None:
        """빈 문자열은 main-sub로 fallback되어야 한다."""
        assert normalize_task_mode("") == TASK_MODE_MAIN_SUB


# ── should_create_subtask ─────────────────────────────────────────────────────


class TestShouldCreateSubtask:
    """should_create_subtask 함수 테스트."""

    def test_main_sub_returns_true(self) -> None:
        assert should_create_subtask("main-sub") is True

    def test_module_task_sub_returns_true(self) -> None:
        assert should_create_subtask("module-task-sub") is True

    def test_flat_returns_false(self) -> None:
        assert should_create_subtask("flat") is False

    def test_invalid_mode_returns_true(self) -> None:
        """유효하지 않은 모드는 main-sub fallback이므로 True."""
        assert should_create_subtask("unknown") is True


# ── build_task_title ──────────────────────────────────────────────────────────


class TestBuildTaskTitle:
    """build_task_title 함수 테스트."""

    def test_flat_mode_returns_plain_summary(self) -> None:
        assert build_task_title("로그인 구현", "flat") == "로그인 구현"

    def test_flat_mode_subtask_same_as_main(self) -> None:
        """flat 모드에서는 is_subtask 여부와 관계없이 동일한 제목."""
        assert build_task_title("로그인 구현", "flat", is_subtask=True) == "로그인 구현"

    def test_main_sub_main_task(self) -> None:
        assert build_task_title("로그인 구현", "main-sub") == "로그인 구현"

    def test_main_sub_subtask(self) -> None:
        assert build_task_title("로그인 구현", "main-sub", is_subtask=True) == "[하위] 로그인 구현"

    def test_module_task_sub_main(self) -> None:
        assert build_task_title("인증 모듈", "module-task-sub") == "[모듈] 인증 모듈"

    def test_module_task_sub_subtask(self) -> None:
        assert build_task_title("인증 모듈", "module-task-sub", is_subtask=True) == "[하위] 인증 모듈"

    def test_empty_summary_uses_default(self) -> None:
        """빈 summary는 '무제'로 대체되어야 한다."""
        assert build_task_title("", "flat") == "무제"


# ── build_task_description ────────────────────────────────────────────────────


class TestBuildTaskDescription:
    """build_task_description 함수 테스트."""

    def test_flat_mode_description(self) -> None:
        desc = build_task_description("구현", ["auth"], "flat")
        assert "**요약**" in desc
        assert "auth" in desc

    def test_main_sub_description(self) -> None:
        desc = build_task_description("구현", ["auth", "api"], "main-sub")
        assert "**목표**" in desc
        assert "auth" in desc

    def test_module_task_sub_description(self) -> None:
        desc = build_task_description("구현", [], "module-task-sub")
        assert "**모듈 태스크**" in desc

    def test_empty_topics(self) -> None:
        """토픽이 없으면 토픽 섹션이 생략되어야 한다."""
        desc = build_task_description("구현", [], "flat")
        assert "토픽" not in desc


# ── apply 엔진 헬퍼 ──────────────────────────────────────────────────────────


def _make_state(
    session_id: str = "test-session-id-abc",
    project_id: str = "proj-1234-abcd-efgh-000000000000",
    scope_summary: str = "",
    auto_created_task_id: str | None = None,
    work_item_ids: list[str] | None = None,
    focused_work_item_id: str | None = None,
) -> SessionState:
    """테스트용 SessionState를 생성한다."""
    state = SessionState(session_id=session_id)
    state.plane_context = PlaneContext(
        project_id=project_id,
        work_item_ids=work_item_ids or [],
        auto_created_task_id=auto_created_task_id,
        focused_work_item_id=focused_work_item_id,
    )
    state.scope = ScopeState(summary=scope_summary)
    return state


def _make_cfg(
    task_mode: str = "main-sub",
    project_id: str = "proj-1234-abcd-efgh-000000000000",
) -> Config:
    """테스트용 Config를 생성한다."""
    cfg = Config()
    cfg.task_mode = task_mode
    cfg.project_id = project_id
    return cfg


class _FakeProviderClient(ProviderClient):
    """테스트용 mock provider 클라이언트."""

    def __init__(self, wi_id: str = "wi-aaaa-bbbb-cccc-dddddddddddd") -> None:
        self._wi_id = wi_id
        self.call_count = 0
        self.last_title: str = ""
        self.last_context: ProviderContext | None = None

    @property
    def name(self) -> str:
        return "fake"

    def build_compact_context(self, context: ProviderContext) -> tuple[str, list[str]]:
        return "", []

    def post_comment(self, context: ProviderContext, comment: str, work_item_id: str = "") -> list[dict[str, Any]]:
        return []

    def poll_comments(self, context: ProviderContext, known_ids: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
        return [], []

    def check_subtask_completion(self, context: ProviderContext) -> int | None:
        return None

    def create_work_item(self, context: ProviderContext, title: str, description: str = "") -> dict[str, Any]:
        self.call_count += 1
        self.last_title = title
        self.last_context = context
        return {"id": self._wi_id}

    def switch_task(self, context: ProviderContext, new_task_title: str, reason: str = "") -> dict[str, Any]:
        return {}


class _ErrorProviderClient(_FakeProviderClient):
    """create_work_item 호출 시 예외를 발생시키는 클라이언트."""

    def create_work_item(self, context: ProviderContext, title: str, description: str = "") -> dict[str, Any]:
        self.call_count += 1
        raise RuntimeError("Plane API 연결 실패")


# ── TestApplyTaskFormatSessionStart ───────────────────────────────────────────


class TestApplyTaskFormatSessionStart:
    """trigger="session_start" 케이스."""

    def test_main_sub_creates_work_item_once(self) -> None:
        """main-sub + session_start → create_work_item 1회 호출."""
        state = _make_state()
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient(wi_id="wi-new-0000")

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="session_start")

        assert client.call_count == 1
        assert state.plane_context.auto_created_task_id == "wi-new-0000"
        assert "wi-new-0000" in state.plane_context.work_item_ids
        assert state.plane_context.focused_work_item_id == "wi-new-0000"

    def test_flat_creates_work_item_once(self) -> None:
        """flat + session_start → create_work_item 1회 호출."""
        state = _make_state()
        cfg = _make_cfg(task_mode="flat")
        client = _FakeProviderClient(wi_id="wi-flat-0001")

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="session_start")

        assert client.call_count == 1
        assert state.plane_context.auto_created_task_id == "wi-flat-0001"

    def test_none_mode_skips_creation(self) -> None:
        """none → create_work_item 0회."""
        state = _make_state()
        cfg = _make_cfg(task_mode="none")
        client = _FakeProviderClient()

        apply_task_format(state, cfg, client, trigger="session_start")

        assert client.call_count == 0
        assert state.plane_context.auto_created_task_id is None

    def test_duplicate_prevention_already_has_auto_id(self) -> None:
        """auto_created_task_id가 이미 있으면 → 0회 (중복 방지)."""
        state = _make_state(auto_created_task_id="wi-existing-id")
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient()

        apply_task_format(state, cfg, client, trigger="session_start")

        assert client.call_count == 0
        # 기존 값 불변
        assert state.plane_context.auto_created_task_id == "wi-existing-id"

    def test_no_project_id_skips_creation(self) -> None:
        """project_id 없음 → 0회, ValueError 아님."""
        state = _make_state(project_id="")
        cfg = _make_cfg(task_mode="main-sub", project_id="")
        client = _FakeProviderClient()

        # ValueError가 아니라 그냥 리턴되어야 함
        apply_task_format(state, cfg, client, trigger="session_start")

        assert client.call_count == 0

    def test_title_uses_scope_summary(self) -> None:
        """scope.summary가 있으면 WI 제목으로 사용한다."""
        state = _make_state(scope_summary="인증 모듈 리팩토링")
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient()

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="session_start")

        assert client.last_title == "인증 모듈 리팩토링"

    def test_title_uses_default_when_no_summary(self) -> None:
        """scope.summary가 없으면 기본 제목을 사용한다."""
        state = _make_state(session_id="abcdef12-xxxx", scope_summary="")
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient()

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="session_start")

        assert client.last_title.startswith("[omk] 새 세션 abcdef12")

    def test_timeline_event_added(self) -> None:
        """session_start 성공 시 타임라인 이벤트가 추가된다."""
        state = _make_state()
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient(wi_id="wi-timeline-test")

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="session_start")

        assert len(state.timeline) == 1
        assert state.timeline[0].type == "scope_init"
        assert "wi-timeline-test" in state.timeline[0].summary

    def test_cfg_project_id_takes_priority_over_state(self) -> None:
        """cfg.project_id가 있으면 state.plane_context.project_id보다 우선한다."""
        state = _make_state(project_id="state-project-id")
        cfg = _make_cfg(task_mode="main-sub", project_id="cfg-project-id")
        client = _FakeProviderClient()

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="session_start")

        # create_work_item에 전달된 context의 project_id는 cfg 값
        assert client.call_count == 1
        assert client.last_context is not None
        assert client.last_context.project_id == "cfg-project-id"

    def test_state_project_id_used_when_cfg_empty(self) -> None:
        """cfg.project_id가 없고 state.plane_context.project_id가 있으면 생성된다."""
        state = _make_state(project_id="state-only-project-id")
        cfg = _make_cfg(task_mode="main-sub", project_id="")
        client = _FakeProviderClient()

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="session_start")

        assert client.call_count == 1
        assert client.last_context is not None
        assert client.last_context.project_id == "state-only-project-id"


# ── TestApplyTaskFormatDriftDetected ──────────────────────────────────────────


class TestApplyTaskFormatDriftDetected:
    """trigger="drift_detected" 케이스."""

    def test_main_sub_with_auto_id_creates_subtask(self) -> None:
        """drift + main-sub + auto_created_task_id 있음 → 1회, focused 교체, auto 불변."""
        state = _make_state(
            auto_created_task_id="wi-main-0001",
            work_item_ids=["wi-main-0001"],
            focused_work_item_id="wi-main-0001",
        )
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient(wi_id="wi-sub-0002")

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="drift_detected", prompt_text="새로운 버그 수정 작업")

        assert client.call_count == 1
        # focused_work_item_id는 새 서브태스크로 교체
        assert state.plane_context.focused_work_item_id == "wi-sub-0002"
        # auto_created_task_id는 불변
        assert state.plane_context.auto_created_task_id == "wi-main-0001"
        # work_item_ids에 서브태스크 추가
        assert "wi-sub-0002" in state.plane_context.work_item_ids
        assert "wi-main-0001" in state.plane_context.work_item_ids

    def test_flat_mode_skips_drift(self) -> None:
        """flat + drift_detected → 0회."""
        state = _make_state(auto_created_task_id="wi-flat-main")
        cfg = _make_cfg(task_mode="flat")
        client = _FakeProviderClient()

        apply_task_format(state, cfg, client, trigger="drift_detected", prompt_text="드리프트 프롬프트")

        assert client.call_count == 0

    def test_no_auto_created_task_id_skips_drift(self) -> None:
        """auto_created_task_id 없음 → 0회."""
        state = _make_state(auto_created_task_id=None)
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient()

        apply_task_format(state, cfg, client, trigger="drift_detected", prompt_text="뭔가 다른 작업")

        assert client.call_count == 0

    def test_drift_title_uses_prompt_text(self) -> None:
        """prompt_text가 있으면 서브태스크 제목으로 사용한다 (최대 60자)."""
        long_prompt = "A" * 80
        state = _make_state(auto_created_task_id="wi-main-xyz")
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient()

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="drift_detected", prompt_text=long_prompt)

        assert len(client.last_title) == 60
        assert client.last_title == "A" * 60

    def test_drift_title_uses_default_when_no_prompt(self) -> None:
        """prompt_text가 없으면 기본 제목을 사용한다."""
        state = _make_state(auto_created_task_id="wi-main-xyz")
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient()

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="drift_detected", prompt_text="")

        assert client.last_title.startswith("[omk] 드리프트 작업 ")

    def test_drift_timeline_event_added(self) -> None:
        """drift_detected 성공 시 타임라인 이벤트가 추가된다."""
        state = _make_state(auto_created_task_id="wi-main-abc")
        cfg = _make_cfg(task_mode="main-sub")
        client = _FakeProviderClient(wi_id="wi-sub-abc")

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="drift_detected", prompt_text="드리프트 이벤트 테스트")

        assert len(state.timeline) == 1
        assert state.timeline[0].type == "drift_detected"
        assert "wi-sub-abc" in state.timeline[0].summary

    def test_none_project_id_skips_drift(self) -> None:
        """project_id 없음 → 0회."""
        state = _make_state(project_id="", auto_created_task_id="wi-main")
        cfg = _make_cfg(task_mode="main-sub", project_id="")
        client = _FakeProviderClient()

        apply_task_format(state, cfg, client, trigger="drift_detected")

        assert client.call_count == 0


# ── TestApplyTaskFormatValidation ─────────────────────────────────────────────


class TestApplyTaskFormatValidation:
    """검증 및 예외 케이스."""

    def test_invalid_mode_raises_value_error(self) -> None:
        """유효하지 않은 task_mode → ValueError."""
        state = _make_state()
        cfg = _make_cfg(task_mode="invalid-mode")
        client = _FakeProviderClient()

        with pytest.raises(ValueError, match="유효하지 않은 task_mode"):
            apply_task_format(state, cfg, client, trigger="session_start")

    def test_provider_exception_reraises(self) -> None:
        """provider 예외 → re-raise (swallow 금지)."""
        state = _make_state()
        cfg = _make_cfg(task_mode="main-sub")
        client = _ErrorProviderClient()

        with pytest.raises(RuntimeError, match="Plane API 연결 실패"):
            apply_task_format(state, cfg, client, trigger="session_start")

    def test_provider_exception_drift_reraises(self) -> None:
        """drift_detected provider 예외 → re-raise."""
        state = _make_state(auto_created_task_id="wi-main-err")
        cfg = _make_cfg(task_mode="main-sub")
        client = _ErrorProviderClient()

        with pytest.raises(RuntimeError, match="Plane API 연결 실패"):
            apply_task_format(state, cfg, client, trigger="drift_detected", prompt_text="오류 유발 프롬프트")

    def test_valid_modes_are_correct(self) -> None:
        """VALID_TASK_MODES에 정확히 4개의 모드가 있다."""
        assert VALID_TASK_MODES == frozenset({"main-sub", "flat", "none", "module-task-sub"})


# ── TestWiIdExtraction ────────────────────────────────────────────────────────


class TestWiIdExtraction:
    """_extract_wi_id 헬퍼 간접 테스트 (raw 폴백 경로)."""

    def test_wi_id_from_raw_fallback(self) -> None:
        """result["id"]가 없을 때 result["raw"]["id"]를 사용한다."""

        class _RawFallbackClient(_FakeProviderClient):
            def create_work_item(self, context: ProviderContext, title: str, description: str = "") -> dict[str, Any]:
                self.call_count += 1
                self.last_title = title
                # id 없이 raw에만 id 포함
                return {"raw": {"id": "wi-raw-fallback-id"}}

        state = _make_state()
        cfg = _make_cfg(task_mode="main-sub")
        client = _RawFallbackClient()

        with patch("oh_my_kanban.session.task_format.save_session"):
            apply_task_format(state, cfg, client, trigger="session_start")

        assert state.plane_context.auto_created_task_id == "wi-raw-fallback-id"

    def test_empty_result_does_not_set_auto_id(self) -> None:
        """result가 빈 dict이면 auto_created_task_id를 설정하지 않는다."""

        class _EmptyResultClient(_FakeProviderClient):
            def create_work_item(self, context: ProviderContext, title: str, description: str = "") -> dict[str, Any]:
                self.call_count += 1
                return {}

        state = _make_state()
        cfg = _make_cfg(task_mode="main-sub")
        client = _EmptyResultClient()

        apply_task_format(state, cfg, client, trigger="session_start")

        assert state.plane_context.auto_created_task_id is None
        assert state.plane_context.work_item_ids == []
