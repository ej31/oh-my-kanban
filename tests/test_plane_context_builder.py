"""plane_context_builder 단위 테스트."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.session.plane_context_builder import (
    _build_wi_context,
    _fetch_comments,
    _fetch_sub_tasks,
    _fetch_work_item,
    _strip_html,
    _truncate,
    build_plane_context,
)


# ─── _strip_html ──────────────────────────────────────────────────────────────


class TestStripHtml:
    def test_removes_html_tags(self):
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_empty_string_returns_empty(self):
        assert _strip_html("") == ""

    def test_none_like_falsy_returns_empty(self):
        # 빈 문자열은 falsy이므로 early return
        assert _strip_html("") == ""

    def test_whitespace_normalization(self):
        result = _strip_html("<p>hello   world</p>")
        assert "  " not in result
        assert result == "hello world"

    def test_newlines_normalized(self):
        result = _strip_html("line1\n\nline2")
        assert result == "line1 line2"

    def test_plain_text_unchanged(self):
        assert _strip_html("plain text") == "plain text"

    def test_nested_tags(self):
        result = _strip_html("<div><span><a href='#'>link</a></span></div>")
        assert result == "link"


# ─── _truncate ────────────────────────────────────────────────────────────────


class TestTruncate:
    def test_within_limit_returns_unchanged(self):
        text = "hello"
        assert _truncate(text, 10) == "hello"

    def test_exactly_at_limit_returns_unchanged(self):
        text = "hello"
        assert _truncate(text, 5) == "hello"

    def test_exceeds_limit_adds_ellipsis(self):
        text = "hello world"
        result = _truncate(text, 5)
        assert result == "hello..."

    def test_ellipsis_appended_not_replacing(self):
        # max_chars=3 이면 앞 3글자 + '...'
        result = _truncate("abcdef", 3)
        assert result == "abc..."

    def test_empty_string(self):
        assert _truncate("", 10) == ""


# ─── _build_wi_context ────────────────────────────────────────────────────────


class TestBuildWiContext:
    def _make_wi(self, **kwargs) -> dict:
        defaults = {
            "name": "테스트 작업",
            "state__name": "In Progress",
            "priority": "high",
            "description_html": "<p>설명입니다</p>",
        }
        defaults.update(kwargs)
        return defaults

    def test_title_included(self):
        wi = self._make_wi()
        result = _build_wi_context(wi, [], "wi-001")
        assert "테스트 작업" in result

    def test_state_included(self):
        wi = self._make_wi()
        result = _build_wi_context(wi, [], "wi-001")
        assert "In Progress" in result

    def test_priority_included(self):
        wi = self._make_wi()
        result = _build_wi_context(wi, [], "wi-001")
        assert "high" in result

    def test_description_included(self):
        wi = self._make_wi()
        result = _build_wi_context(wi, [], "wi-001")
        assert "설명입니다" in result

    def test_no_comments_section_absent(self):
        wi = self._make_wi()
        result = _build_wi_context(wi, [], "wi-001")
        assert "최근 댓글" not in result

    def test_comments_included(self):
        wi = self._make_wi()
        comments = [
            {
                "comment_html": "<p>댓글 내용</p>",
                "actor_detail": {"display_name": "홍길동"},
                "created_at": "2026-03-01T10:00:00Z",
            }
        ]
        result = _build_wi_context(wi, comments, "wi-001")
        assert "댓글 내용" in result
        assert "홍길동" in result

    def test_state_as_dict(self):
        """state 필드가 dict 형태일 때 name을 추출한다."""
        wi = self._make_wi()
        wi.pop("state__name", None)
        wi["state"] = {"name": "Done"}
        result = _build_wi_context(wi, [], "wi-001")
        assert "Done" in result

    def test_state_as_string(self):
        """state__name 문자열 우선 사용."""
        wi = self._make_wi(state__name="Todo")
        result = _build_wi_context(wi, [], "wi-001")
        assert "Todo" in result

    def test_comment_actor_email_fallback(self):
        """display_name 없을 때 email을 표시한다."""
        wi = self._make_wi()
        comments = [
            {
                "comment_html": "내용",
                "actor_detail": {"email": "user@example.com"},
                "created_at": "2026-03-01T00:00:00Z",
            }
        ]
        result = _build_wi_context(wi, comments, "wi-001")
        assert "user@example.com" in result


# ─── _fetch_work_item ─────────────────────────────────────────────────────────


class TestFetchWorkItem:
    def _args(self, client):
        return (
            client,
            "https://api.plane.so",
            "my-workspace",
            "proj-123",
            "wi-abc",
            {"X-API-Key": "key"},
        )

    def test_http_200_returns_json(self):
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"name": "작업"}
        client.get.return_value = resp

        result = _fetch_work_item(*self._args(client))
        assert result == {"name": "작업"}

    def test_http_non200_returns_none(self, capsys):
        # 404/410은 __deleted__ 마커를 반환하므로 일반 non-200(예: 500)으로 테스트한다
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 500
        client.get.return_value = resp

        result = _fetch_work_item(*self._args(client))
        assert result is None
        captured = capsys.readouterr()
        assert "HTTP 500" in captured.err



    def test_http_404_returns_deleted_marker(self, capsys):
        """404 응답 시 __deleted__ 마커 dict를 반환한다."""
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 404
        client.get.return_value = resp

        result = _fetch_work_item(*self._args(client))
        assert result is not None
        assert result.get("__deleted__") is True
        assert result.get("__status__") == 404

    def test_http_410_returns_deleted_marker(self, capsys):
        """410 응답 시 __deleted__ 마커 dict를 반환한다."""
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 410
        client.get.return_value = resp

        result = _fetch_work_item(*self._args(client))
        assert result is not None
        assert result.get("__deleted__") is True
        assert result.get("__status__") == 410

    def test_exception_returns_none(self, capsys):
        client = MagicMock()
        client.get.side_effect = RuntimeError("연결 실패")

        result = _fetch_work_item(*self._args(client))
        assert result is None
        captured = capsys.readouterr()
        assert "RuntimeError" in captured.err


# ─── _fetch_comments ──────────────────────────────────────────────────────────


class TestFetchComments:
    def _args(self, client):
        return (
            client,
            "https://api.plane.so",
            "my-workspace",
            "proj-123",
            "wi-abc",
            {"X-API-Key": "key"},
        )

    def test_results_array_returned(self):
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"results": [{"comment_html": "댓글1"}]}
        client.get.return_value = resp

        result = _fetch_comments(*self._args(client))
        assert result == [{"comment_html": "댓글1"}]

    def test_list_directly_returned(self):
        """Plane API가 list를 직접 반환하는 경우."""
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"comment_html": "댓글A"}, {"comment_html": "댓글B"}]
        client.get.return_value = resp

        result = _fetch_comments(*self._args(client))
        assert len(result) == 2

    def test_empty_results_returns_empty_list(self):
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"results": []}
        client.get.return_value = resp

        result = _fetch_comments(*self._args(client))
        assert result == []

    def test_non200_returns_empty_list(self):
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 500
        client.get.return_value = resp

        result = _fetch_comments(*self._args(client))
        assert result == []

    def test_exception_returns_empty_list(self, capsys):
        client = MagicMock()
        client.get.side_effect = OSError("타임아웃")

        result = _fetch_comments(*self._args(client))
        assert result == []
        captured = capsys.readouterr()
        assert "OSError" in captured.err


# ─── build_plane_context ──────────────────────────────────────────────────────


class TestBuildPlaneContext:
    _BASE_PARAMS = dict(
        project_id="proj-001",
        base_url="https://api.plane.so",
        api_key="test-key",
        workspace_slug="my-ws",
    )

    def test_empty_work_item_ids_returns_empty(self):
        result = build_plane_context(work_item_ids=[], **self._BASE_PARAMS)
        assert result == ""

    def test_none_api_key_returns_empty(self):
        params = {**self._BASE_PARAMS, "api_key": None}
        result = build_plane_context(work_item_ids=["wi-1"], **params)
        assert result == ""

    def test_empty_api_key_returns_empty(self):
        params = {**self._BASE_PARAMS, "api_key": ""}
        result = build_plane_context(work_item_ids=["wi-1"], **params)
        assert result == ""

    def test_max_3_work_items_queried(self):
        """4개를 줘도 최대 3개만 조회한다."""
        mock_client_instance = MagicMock()

        # URL 패턴 기반으로 응답을 분기한다 (ThreadPoolExecutor 병렬 실행 시 순서 비결정적)
        def _route_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            if "/comments/" in url:
                resp.json.return_value = {"results": []}
            elif kwargs.get("params", {}).get("parent"):
                # sub-tasks 조회
                resp.json.return_value = {"results": []}
            else:
                # WI 상세 조회
                resp.json.return_value = {
                    "name": "작업",
                    "state__name": "Todo",
                    "priority": "none",
                    "description_html": "",
                }
            return resp

        mock_client_instance.get.side_effect = _route_get

        mock_client_ctx = MagicMock()
        mock_client_ctx.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_ctx.__exit__ = MagicMock(return_value=False)

        mock_httpx = MagicMock()
        mock_httpx.Client.return_value = mock_client_ctx

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            result = build_plane_context(
                work_item_ids=["wi-1", "wi-2", "wi-3", "wi-4"],
                **self._BASE_PARAMS,
            )

        # get 호출 횟수: WI 3개 x (WI조회1 + 댓글조회1 + sub-tasks조회1) = 9번
        # (4번째 WI는 조회하지 않아야 한다)
        assert mock_client_instance.get.call_count == 9

    def test_full_context_limited_to_3000_chars(self):
        """결과가 3000자를 초과하지 않는다."""
        mock_client_instance = MagicMock()

        long_text = "가" * 2000
        wi_resp = MagicMock()
        wi_resp.status_code = 200
        wi_resp.json.return_value = {
            "name": long_text,
            "state__name": "Todo",
            "priority": "urgent",
            "description_html": f"<p>{long_text}</p>",
        }

        comments_resp = MagicMock()
        comments_resp.status_code = 200
        comments_resp.json.return_value = {"results": []}

        mock_client_instance.get.side_effect = [
            wi_resp, comments_resp,
            wi_resp, comments_resp,
            wi_resp, comments_resp,
        ]

        mock_client_ctx = MagicMock()
        mock_client_ctx.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_ctx.__exit__ = MagicMock(return_value=False)

        mock_httpx = MagicMock()
        mock_httpx.Client.return_value = mock_client_ctx

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            result = build_plane_context(
                work_item_ids=["wi-1", "wi-2", "wi-3"],
                **self._BASE_PARAMS,
            )

        assert len(result) <= 3003  # 3000자 + '...' 3자

    def test_httpx_import_error_returns_empty(self):
        """httpx가 없으면 빈 문자열 반환 (fail-open)."""
        with patch.dict(sys.modules, {"httpx": None}):
            # sys.modules에 None을 넣으면 ImportError처럼 동작
            # 실제로는 import httpx 시점에 ImportError가 발생하도록 처리
            pass

        # importlib을 통해 실제 ImportError 시뮬레이션
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "httpx":
                raise ImportError("httpx not installed")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = build_plane_context(
                work_item_ids=["wi-1"],
                **self._BASE_PARAMS,
            )
        assert result == ""


# ─── _fetch_sub_tasks ─────────────────────────────────────────────────────────


class TestFetchSubTasks:
    def _args(self, client):
        return (
            client,
            "https://api.plane.so",
            "my-workspace",
            "proj-123",
            "wi-parent",
            {"X-API-Key": "key"},
        )

    def test_results_array_returned(self):
        """results 배열이 있으면 해당 리스트를 반환한다."""
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "results": [
                {"name": "하위 태스크 1", "state__name": "Todo"},
                {"name": "하위 태스크 2", "state__name": "Done"},
            ]
        }
        client.get.return_value = resp

        result = _fetch_sub_tasks(*self._args(client))
        assert len(result) == 2
        assert result[0]["name"] == "하위 태스크 1"

    def test_list_directly_returned(self):
        """Plane API가 list를 직접 반환하는 경우도 처리한다."""
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"name": "태스크A"}, {"name": "태스크B"}]
        client.get.return_value = resp

        result = _fetch_sub_tasks(*self._args(client))
        assert len(result) == 2

    def test_empty_results_returns_empty_list(self):
        """빈 결과이면 빈 리스트를 반환한다."""
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"results": []}
        client.get.return_value = resp

        result = _fetch_sub_tasks(*self._args(client))
        assert result == []

    def test_non200_returns_empty_list(self):
        """HTTP 200이 아니면 빈 리스트를 반환한다."""
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 403
        client.get.return_value = resp

        result = _fetch_sub_tasks(*self._args(client))
        assert result == []

    def test_exception_returns_empty_list(self, capsys):
        """예외 발생 시 빈 리스트를 반환한다 (fail-open)."""
        client = MagicMock()
        client.get.side_effect = RuntimeError("연결 실패")

        result = _fetch_sub_tasks(*self._args(client))
        assert result == []
        captured = capsys.readouterr()
        assert "RuntimeError" in captured.err

    def test_parent_param_sent(self):
        """parent=wi_id 쿼리 파라미터를 함께 전송한다."""
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"results": []}
        client.get.return_value = resp

        _fetch_sub_tasks(*self._args(client))

        # params에 parent 파라미터가 있는지 확인
        _, kwargs = client.get.call_args
        assert kwargs.get("params", {}).get("parent") == "wi-parent"


# ─── _build_wi_context with sub_tasks ─────────────────────────────────────────


class TestBuildWiContextSubTasks:
    def _make_wi(self) -> dict:
        return {
            "name": "메인 태스크",
            "state__name": "In Progress",
            "priority": "high",
            "description_html": "<p>설명</p>",
        }

    def test_sub_tasks_section_shown(self):
        """sub_tasks가 있으면 'Sub-tasks' 섹션이 표시된다."""
        wi = self._make_wi()
        sub_tasks = [
            {"name": "하위 1", "state__name": "Done"},
            {"name": "하위 2", "state__name": "Todo"},
        ]
        result = _build_wi_context(wi, [], "wi-001", sub_tasks=sub_tasks)
        assert "Sub-tasks" in result
        assert "하위 1" in result
        assert "하위 2" in result

    def test_completed_subtask_shows_checkmark(self):
        """완료된 sub-task는 '✓' 기호로 표시된다."""
        wi = self._make_wi()
        sub_tasks = [{"name": "완료 태스크", "state__name": "Done"}]
        result = _build_wi_context(wi, [], "wi-001", sub_tasks=sub_tasks)
        assert "✓" in result

    def test_incomplete_subtask_shows_circle(self):
        """미완료 sub-task는 '○' 기호로 표시된다."""
        wi = self._make_wi()
        sub_tasks = [{"name": "미완료 태스크", "state__name": "In Progress"}]
        result = _build_wi_context(wi, [], "wi-001", sub_tasks=sub_tasks)
        assert "○" in result

    def test_sub_tasks_capped_at_display_max(self):
        """sub_tasks가 최대 표시 수(5)를 초과하면 잘라낸다."""
        wi = self._make_wi()
        sub_tasks = [
            {"name": f"태스크{i}", "state__name": "Todo"} for i in range(8)
        ]
        result = _build_wi_context(wi, [], "wi-001", sub_tasks=sub_tasks)
        # 초과분 안내 문구가 있어야 한다
        assert "...외" in result
        assert "3개" in result

    def test_no_sub_tasks_section_absent(self):
        """sub_tasks=None이면 'Sub-tasks' 섹션이 없다."""
        wi = self._make_wi()
        result = _build_wi_context(wi, [], "wi-001", sub_tasks=None)
        assert "Sub-tasks" not in result

    def test_empty_sub_tasks_section_absent(self):
        """sub_tasks=[]이면 'Sub-tasks' 섹션이 없다."""
        wi = self._make_wi()
        result = _build_wi_context(wi, [], "wi-001", sub_tasks=[])
        assert "Sub-tasks" not in result

    def test_complete_state_variations(self):
        """'complete' 또는 'done'이 포함된 상태는 완료(✓)로 표시한다."""
        wi = self._make_wi()
        for state_name in ["Complete", "Completed", "Done", "DONE"]:
            sub_tasks = [{"name": "태스크", "state__name": state_name}]
            result = _build_wi_context(wi, [], "wi-001", sub_tasks=sub_tasks)
            assert "✓" in result, f"state_name={state_name!r}에서 ✓가 없음"
