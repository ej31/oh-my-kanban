"""oh-my-kanban MCP server.py 5개 툴 단위 테스트.

mcp 패키지가 설치되지 않아도 실행 가능하도록 sys.modules에 mock을 주입한 뒤 import한다.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# ── mcp 패키지 mock 주입 (설치 없이도 import 가능하게) ────────────────────
_mock_mcp = MagicMock()
_mock_fastmcp_cls = MagicMock()
_mock_fastmcp_instance = MagicMock()
_mock_fastmcp_cls.return_value = _mock_fastmcp_instance
# tool 데코레이터는 함수를 그대로 반환하도록
_mock_fastmcp_instance.tool.return_value = lambda f: f

sys.modules.setdefault("mcp", _mock_mcp)
sys.modules.setdefault("mcp.server", MagicMock())
sys.modules.setdefault("mcp.server.fastmcp", MagicMock(FastMCP=_mock_fastmcp_cls))

# mcp.server.fastmcp.FastMCP 경로를 실제로 반환하도록 설정
sys.modules["mcp.server.fastmcp"].FastMCP = _mock_fastmcp_cls

# ── 실제 모듈 import ─────────────────────────────────────────────────────────
# 이미 캐시된 경우 제거해 재 import 보장
for _mod in list(sys.modules):
    if _mod.startswith("oh_my_kanban.mcp"):
        del sys.modules[_mod]

from oh_my_kanban.mcp.server import (  # noqa: E402
    _find_active_session_id,
    omk_add_comment,
    omk_get_session_status,
    omk_get_timeline,
    omk_link_work_item,
    omk_update_scope,
)
from oh_my_kanban.session.state import (  # noqa: E402
    PlaneContext,
    ScopeState,
    SessionConfig,
    SessionState,
    SessionStats,
    STATUS_ACTIVE,
    TimelineEvent,
)


# ── 공통 픽스처 ──────────────────────────────────────────────────────────────

def _make_session(
    session_id: str = "sess-0001",
    status: str = STATUS_ACTIVE,
    work_item_ids: list[str] | None = None,
    project_id: str = "00000000-0000-0000-0000-000000000001",
    summary: str = "테스트 세션",
    topics: list[str] | None = None,
    keywords: list[str] | None = None,
    timeline: list[TimelineEvent] | None = None,
) -> SessionState:
    """테스트용 SessionState를 생성한다."""
    return SessionState(
        session_id=session_id,
        status=status,
        created_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:01:00+00:00",
        scope=ScopeState(
            summary=summary,
            topics=topics or ["topic-a"],
            keywords=keywords or ["kw1"],
        ),
        plane_context=PlaneContext(
            project_id=project_id,
            work_item_ids=work_item_ids or [],
        ),
        stats=SessionStats(),
        config=SessionConfig(),
        timeline=timeline or [],
    )


# ════════════════════════════════════════════════════════════════════════════
# 1. omk_get_session_status
# ════════════════════════════════════════════════════════════════════════════

class TestOmkGetSessionStatus:
    """omk_get_session_status 툴 테스트."""

    def test_활성_세션_있을때_올바른_dict_구조_반환(self):
        """활성 세션이 있을 때 필수 키를 포함한 dict를 반환해야 한다."""
        state = _make_session(session_id="s001", summary="기능 구현")

        with (
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
        ):
            result = omk_get_session_status()

        assert result["session_id"] == "s001"
        assert result["status"] == STATUS_ACTIVE
        assert "scope" in result
        assert result["scope"]["summary"] == "기능 구현"
        assert "plane_context" in result
        assert "stats" in result
        assert "config" in result

    def test_세션_없을때_error_반환(self):
        """활성 세션이 없을 때 error 키를 포함한 dict를 반환해야 한다."""
        with patch("oh_my_kanban.mcp.server._find_active_session_id", return_value=None):
            result = omk_get_session_status()

        assert "error" in result

    def test_session_id_빈문자열_find_active_session_id_호출(self):
        """session_id가 빈 문자열이면 _find_active_session_id를 호출해야 한다."""
        with patch(
            "oh_my_kanban.mcp.server._find_active_session_id", return_value=None
        ) as mock_find:
            omk_get_session_status(session_id="")
            mock_find.assert_called_once()

    def test_load_session이_None_반환시_error_반환(self):
        """load_session이 None을 반환하면 error dict를 반환해야 한다."""
        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s999"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=None),
        ):
            result = omk_get_session_status()

        assert "error" in result
        assert "s999" in result["error"]

    def test_명시적_session_id_제공시_해당_세션_조회(self):
        """명시적으로 session_id를 지정하면 해당 세션을 조회해야 한다."""
        state = _make_session(session_id="explicit-id")

        with patch("oh_my_kanban.mcp.server.load_session", return_value=state) as mock_load:
            result = omk_get_session_status(session_id="explicit-id")

        mock_load.assert_called_once_with("explicit-id")
        assert result["session_id"] == "explicit-id"


# ════════════════════════════════════════════════════════════════════════════
# 2. omk_link_work_item
# ════════════════════════════════════════════════════════════════════════════

VALID_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
VALID_UUID_2 = "b2c3d4e5-f6a7-8901-bcde-f01234567891"


class TestOmkLinkWorkItem:
    """omk_link_work_item 툴 테스트."""

    def test_유효한_UUID_연결_성공(self):
        """유효한 UUID로 work item을 연결하면 success=True를 반환해야 한다."""
        state = _make_session(work_item_ids=[])

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.save_session") as mock_save,
        ):
            result = omk_link_work_item(work_item_id=VALID_UUID)

        assert result["success"] is True
        assert VALID_UUID in result["work_item_ids"]
        mock_save.assert_called_once()

    def test_잘못된_UUID_형식_error_반환(self):
        """UUID 형식이 아닌 문자열을 전달하면 error를 반환해야 한다."""
        result = omk_link_work_item(work_item_id="not-a-uuid")

        assert "error" in result
        assert "UUID" in result["error"]

    def test_빈_work_item_id_error_반환(self):
        """work_item_id가 빈 문자열이면 error를 반환해야 한다."""
        result = omk_link_work_item(work_item_id="")

        assert "error" in result

    def test_공백만_있는_work_item_id_error_반환(self):
        """work_item_id가 공백만 있으면 error를 반환해야 한다."""
        result = omk_link_work_item(work_item_id="   ")

        assert "error" in result

    def test_이미_연결된_WI_success_True_중복_없음(self):
        """이미 연결된 Work Item을 다시 연결하면 success=True이고 중복이 없어야 한다."""
        state = _make_session(work_item_ids=[VALID_UUID])

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.save_session") as mock_save,
        ):
            result = omk_link_work_item(work_item_id=VALID_UUID)

        assert result["success"] is True
        assert result["work_item_ids"].count(VALID_UUID) == 1
        # 중복이므로 save_session은 호출되지 않아야 함
        mock_save.assert_not_called()

    def test_활성_세션_없을때_error_반환(self):
        """활성 세션이 없으면 error를 반환해야 한다."""
        with patch("oh_my_kanban.mcp.server._find_active_session_id", return_value=None):
            result = omk_link_work_item(work_item_id=VALID_UUID)

        assert "error" in result


# ════════════════════════════════════════════════════════════════════════════
# 3. omk_update_scope
# ════════════════════════════════════════════════════════════════════════════

class TestOmkUpdateScope:
    """omk_update_scope 툴 테스트."""

    def test_summary_업데이트(self):
        """summary만 제공하면 summary가 업데이트되어야 한다."""
        state = _make_session(summary="이전 요약")

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.save_session"),
        ):
            result = omk_update_scope(summary="새로운 요약")

        assert result["success"] is True
        assert result["scope"]["summary"] == "새로운 요약"
        assert "summary" in result["message"]

    def test_topics_업데이트(self):
        """topics를 제공하면 topics가 업데이트되어야 한다."""
        state = _make_session(topics=["old-topic"])

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.save_session"),
        ):
            result = omk_update_scope(topics=["new-topic-a", "new-topic-b"])

        assert result["success"] is True
        assert result["scope"]["topics"] == ["new-topic-a", "new-topic-b"]

    def test_keywords_업데이트(self):
        """keywords를 제공하면 keywords가 업데이트되어야 한다."""
        state = _make_session(keywords=["old-kw"])

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.save_session"),
        ):
            result = omk_update_scope(keywords=["kw-a", "kw-b"])

        assert result["success"] is True
        assert result["scope"]["keywords"] == ["kw-a", "kw-b"]

    def test_변경_없음_케이스_메시지_반환(self):
        """아무 값도 제공하지 않으면 '변경할 내용이 없습니다' 메시지를 반환해야 한다."""
        state = _make_session()

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.save_session") as mock_save,
        ):
            result = omk_update_scope()

        assert result["success"] is True
        assert "변경할 내용이 없습니다" in result["message"]
        # 변경 없으므로 save_session 호출 안 됨
        mock_save.assert_not_called()

    def test_빈_summary는_기존값_보존(self):
        """summary가 빈 문자열이면 기존 값을 유지해야 한다."""
        state = _make_session(summary="유지되어야 할 요약")

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.save_session"),
        ):
            result = omk_update_scope(summary="", topics=["새 토픽"])

        assert result["scope"]["summary"] == "유지되어야 할 요약"

    def test_expanded_topics_업데이트시_scope_expansions_증가(self):
        """expanded_topics 업데이트 시 stats.scope_expansions가 증가해야 한다."""
        state = _make_session()
        initial_expansions = state.stats.scope_expansions

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.save_session"),
        ):
            omk_update_scope(expanded_topics=["확장 토픽"])

        assert state.stats.scope_expansions == initial_expansions + 1

    def test_활성_세션_없을때_error_반환(self):
        """활성 세션이 없으면 error를 반환해야 한다."""
        with patch("oh_my_kanban.mcp.server._find_active_session_id", return_value=None):
            result = omk_update_scope(summary="무언가")

        assert "error" in result


# ════════════════════════════════════════════════════════════════════════════
# 4. omk_get_timeline
# ════════════════════════════════════════════════════════════════════════════

def _make_events(n: int) -> list[TimelineEvent]:
    """n개의 타임라인 이벤트를 생성한다."""
    return [
        TimelineEvent(
            timestamp=f"2024-01-01T00:0{i}:00+00:00",
            type="prompt",
            summary=f"이벤트 {i}",
        )
        for i in range(n)
    ]


class TestOmkGetTimeline:
    """omk_get_timeline 툴 테스트."""

    def test_limit_5_최신_5개만_반환(self):
        """limit=5이면 최신 5개 이벤트만 반환해야 한다."""
        events = _make_events(10)
        state = _make_session(timeline=events)

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
        ):
            result = omk_get_timeline(limit=5)

        assert result["returned"] == 5
        assert result["total_events"] == 10

    def test_limit_150_100으로_클램핑(self):
        """limit=150이면 100으로 클램핑되어야 한다."""
        events = _make_events(110)
        state = _make_session(timeline=events)

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
        ):
            result = omk_get_timeline(limit=150)

        assert result["returned"] == 100

    def test_limit_0_1로_클램핑(self):
        """limit=0이면 1로 클램핑되어야 한다."""
        events = _make_events(5)
        state = _make_session(timeline=events)

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
        ):
            result = omk_get_timeline(limit=0)

        assert result["returned"] == 1

    def test_음수_limit_1로_클램핑(self):
        """limit이 음수이면 1로 클램핑되어야 한다."""
        events = _make_events(5)
        state = _make_session(timeline=events)

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
        ):
            result = omk_get_timeline(limit=-5)

        assert result["returned"] == 1

    def test_이벤트_없는_세션_빈_목록_반환(self):
        """이벤트가 없는 세션이면 빈 타임라인을 반환해야 한다."""
        state = _make_session(timeline=[])

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
        ):
            result = omk_get_timeline(limit=20)

        assert result["returned"] == 0
        assert result["timeline"] == []

    def test_타임라인_이벤트_필드_포함_확인(self):
        """반환된 이벤트에 timestamp, type, summary, drift_score 필드가 있어야 한다."""
        events = [TimelineEvent(timestamp="2024-01-01T00:00:00+00:00", type="scope_expanded", summary="범위 확장", drift_score=0.8)]
        state = _make_session(timeline=events)

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
        ):
            result = omk_get_timeline(limit=1)

        event = result["timeline"][0]
        assert "timestamp" in event
        assert "type" in event
        assert "summary" in event
        assert "drift_score" in event
        assert event["drift_score"] == 0.8

    def test_활성_세션_없을때_error_반환(self):
        """활성 세션이 없으면 error를 반환해야 한다."""
        with patch("oh_my_kanban.mcp.server._find_active_session_id", return_value=None):
            result = omk_get_timeline()

        assert "error" in result


# ════════════════════════════════════════════════════════════════════════════
# 5. omk_add_comment
# ════════════════════════════════════════════════════════════════════════════

class TestOmkAddComment:
    """omk_add_comment 툴 테스트."""

    def _make_cfg(self):
        """Plane API 설정이 완료된 Config mock을 반환한다."""
        from oh_my_kanban.config import Config
        cfg = Config()
        cfg.api_key = "test-api-key"
        cfg.workspace_slug = "test-workspace"
        cfg.base_url = "https://api.plane.so"
        return cfg

    def test_빈_comment_error_반환(self):
        """댓글 내용이 비어있으면 error를 반환해야 한다."""
        result = omk_add_comment(comment="")

        assert "error" in result

    def test_공백만_있는_comment_error_반환(self):
        """댓글이 공백만 있으면 error를 반환해야 한다."""
        result = omk_add_comment(comment="   ")

        assert "error" in result

    def test_WI_없는_세션_error_반환(self):
        """세션에 연결된 Work Item이 없으면 error를 반환해야 한다."""
        state = _make_session(work_item_ids=[], project_id="00000000-0000-0000-0000-000000000001")

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
        ):
            result = omk_add_comment(comment="댓글 내용")

        assert "error" in result

    def test_project_id_없는_세션_error_반환(self):
        """project_id가 없는 세션이면 error를 반환해야 한다."""
        state = _make_session(work_item_ids=[VALID_UUID], project_id="")

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
        ):
            result = omk_add_comment(comment="댓글 내용")

        assert "error" in result

    def test_httpx_성공_success_True(self):
        """httpx POST가 201을 반환하면 success=True여야 한다."""
        state = _make_session(work_item_ids=[VALID_UUID], project_id="00000000-0000-0000-0000-000000000001")
        cfg = self._make_cfg()

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.load_config", return_value=cfg),
            patch("oh_my_kanban.mcp.server.plane_http_client", return_value=mock_client),
            patch("oh_my_kanban.mcp.server.plane_request", return_value=mock_resp),
        ):
            result = omk_add_comment(comment="중요한 결정")

        assert result["success"] is True
        assert result["results"][0]["success"] is True

    def test_httpx_HTTP_오류_results에_error_포함(self):
        """httpx가 4xx/5xx를 반환하면 results에 error 정보가 포함되어야 한다."""
        state = _make_session(work_item_ids=[VALID_UUID], project_id="00000000-0000-0000-0000-000000000001")
        cfg = self._make_cfg()

        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.load_config", return_value=cfg),
            patch("oh_my_kanban.mcp.server.plane_http_client", return_value=mock_client),
            patch("oh_my_kanban.mcp.server.plane_request", return_value=mock_resp),
        ):
            result = omk_add_comment(comment="댓글")

        assert result["results"][0]["success"] is False
        assert "error" in result["results"][0]

    def test_httpx_타임아웃_results에_error_포함(self):
        """httpx TimeoutException 발생 시 results에 타임아웃 error가 포함되어야 한다."""
        import httpx as _httpx

        state = _make_session(work_item_ids=[VALID_UUID], project_id="00000000-0000-0000-0000-000000000001")
        cfg = self._make_cfg()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.load_config", return_value=cfg),
            patch("oh_my_kanban.mcp.server.plane_http_client", return_value=mock_client),
            patch("oh_my_kanban.mcp.server.plane_request", side_effect=_httpx.TimeoutException("timeout")),
        ):
            result = omk_add_comment(comment="댓글")

        assert result["results"][0]["success"] is False
        assert "시간 초과" in result["results"][0]["error"]

    def test_api_키_없으면_error_반환(self):
        """API 키가 없으면 error를 반환해야 한다."""
        from oh_my_kanban.config import Config
        state = _make_session(work_item_ids=[VALID_UUID], project_id="00000000-0000-0000-0000-000000000001")
        cfg = Config()
        cfg.api_key = ""
        cfg.workspace_slug = "ws"

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.load_config", return_value=cfg),
        ):
            result = omk_add_comment(comment="댓글")

        assert "error" in result

    def test_특정_work_item_id_지정시_해당_WI에만_댓글(self):
        """work_item_id를 명시하면 해당 WI에만 댓글을 추가해야 한다."""
        state = _make_session(work_item_ids=[VALID_UUID, VALID_UUID_2], project_id="00000000-0000-0000-0000-000000000001")
        cfg = self._make_cfg()

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with (
            patch("oh_my_kanban.mcp.server._find_active_session_id", return_value="s001"),
            patch("oh_my_kanban.mcp.server.load_session", return_value=state),
            patch("oh_my_kanban.mcp.server.load_config", return_value=cfg),
            patch("oh_my_kanban.mcp.server.plane_http_client", return_value=mock_client),
            patch("oh_my_kanban.mcp.server.plane_request", return_value=mock_resp),
        ):
            result = omk_add_comment(comment="댓글", work_item_id=VALID_UUID)

        # 지정한 WI 1개에만 댓글 추가
        assert len(result["results"]) == 1
        assert result["results"][0]["work_item_id"] == VALID_UUID

    def test_활성_세션_없을때_error_반환(self):
        """활성 세션이 없으면 error를 반환해야 한다."""
        with patch("oh_my_kanban.mcp.server._find_active_session_id", return_value=None):
            result = omk_add_comment(comment="댓글")

        assert "error" in result


# ════════════════════════════════════════════════════════════════════════════
# 6. _find_active_session_id (내부 헬퍼)
# ════════════════════════════════════════════════════════════════════════════

class TestFindActiveSessionId:
    """_find_active_session_id 헬퍼 테스트."""

    def test_활성_세션_있을때_최신_session_id_반환(self):
        """활성 세션이 있으면 가장 최근 updated_at 세션의 ID를 반환해야 한다."""
        older = _make_session(session_id="old-sess", status=STATUS_ACTIVE)
        older.updated_at = "2024-01-01T00:00:00+00:00"
        newer = _make_session(session_id="new-sess", status=STATUS_ACTIVE)
        newer.updated_at = "2024-01-02T00:00:00+00:00"

        with patch("oh_my_kanban.mcp.server.list_sessions", return_value=[older, newer]):
            result = _find_active_session_id()

        assert result == "new-sess"

    def test_활성_세션_없을때_None_반환(self):
        """활성 세션이 없으면 None을 반환해야 한다."""
        from oh_my_kanban.session.state import STATUS_COMPLETED
        completed = _make_session(session_id="done-sess", status=STATUS_COMPLETED)

        with patch("oh_my_kanban.mcp.server.list_sessions", return_value=[completed]):
            result = _find_active_session_id()

        assert result is None

    def test_세션_목록_비어있으면_None_반환(self):
        """세션 목록이 비어있으면 None을 반환해야 한다."""
        with patch("oh_my_kanban.mcp.server.list_sessions", return_value=[]):
            result = _find_active_session_id()

        assert result is None
