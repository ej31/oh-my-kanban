"""Linear 핵심 인프라 테스트: LinearClient, LinearContext, LinearErrors, Config."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

# ─── LinearErrors ─────────────────────────────────────────────────────────────

def test_linear_graphql_error_stores_errors():
    """LinearGraphQLError는 errors 목록을 저장해야 한다."""
    from oh_my_kanban.providers.linear.errors import LinearGraphQLError

    errs = [{"message": "Not found"}]
    exc = LinearGraphQLError(errs)
    assert exc.errors == errs


def test_linear_http_error_stores_status_code():
    """LinearHttpError는 status_code를 저장해야 한다."""
    from oh_my_kanban.providers.linear.errors import LinearHttpError

    exc = LinearHttpError(404, "Not Found")
    assert exc.status_code == 404


def test_format_graphql_error_returns_korean():
    """format_linear_error는 GraphQL 에러를 한글 메시지로 변환해야 한다."""
    from oh_my_kanban.providers.linear.errors import LinearGraphQLError, format_linear_error

    exc = LinearGraphQLError([{"message": "Some error"}])
    result = format_linear_error(exc)
    assert "오류" in result
    assert "Some error" in result


def test_format_http_error_401():
    """format_linear_error는 401을 인증 실패 메시지로 변환해야 한다."""
    from oh_my_kanban.providers.linear.errors import LinearHttpError, format_linear_error

    exc = LinearHttpError(401, "Unauthorized")
    result = format_linear_error(exc)
    assert "인증" in result


def test_format_http_error_403():
    """format_linear_error는 403을 권한 부족 메시지로 변환해야 한다."""
    from oh_my_kanban.providers.linear.errors import LinearHttpError, format_linear_error

    exc = LinearHttpError(403, "Forbidden")
    result = format_linear_error(exc)
    assert "권한" in result


def test_format_http_error_404():
    """format_linear_error는 404를 리소스 없음 메시지로 변환해야 한다."""
    from oh_my_kanban.providers.linear.errors import LinearHttpError, format_linear_error

    exc = LinearHttpError(404, "Not Found")
    result = format_linear_error(exc)
    assert "찾을 수 없" in result


def test_format_timeout_error():
    """format_linear_error는 TimeoutException을 시간 초과 메시지로 변환해야 한다."""
    from oh_my_kanban.providers.linear.errors import format_linear_error

    exc = httpx.TimeoutException("timeout")
    result = format_linear_error(exc)
    assert "시간" in result


def test_handle_linear_error_decorator_passes_through():
    """handle_linear_error는 정상 함수 결과를 그대로 반환해야 한다."""
    from oh_my_kanban.providers.linear.errors import handle_linear_error

    @handle_linear_error
    def good_func():
        return "ok"

    assert good_func() == "ok"


def test_handle_linear_error_decorator_catches_graphql_error(capsys):
    """handle_linear_error는 LinearGraphQLError를 잡아 stderr에 출력하고 sys.exit(1)해야 한다."""
    import sys
    from oh_my_kanban.providers.linear.errors import LinearGraphQLError, handle_linear_error

    @handle_linear_error
    def bad_func():
        raise LinearGraphQLError([{"message": "boom"}])

    with pytest.raises(SystemExit) as exc_info:
        bad_func()
    assert exc_info.value.code == 1


def test_handle_linear_error_reraises_click_usage_error():
    """handle_linear_error는 click.UsageError를 다시 올려야 한다."""
    import click
    from oh_my_kanban.providers.linear.errors import handle_linear_error

    @handle_linear_error
    def bad_func():
        raise click.UsageError("bad usage")

    with pytest.raises(click.UsageError):
        bad_func()


# ─── LinearClient ──────────────────────────────────────────────────────────────

def test_linear_client_rejects_empty_api_key():
    """LinearClient는 빈 api_key로 생성 시 ValueError를 발생시켜야 한다."""
    from oh_my_kanban.providers.linear.client import LinearClient

    with pytest.raises(ValueError, match="api_key"):
        LinearClient("")


def test_linear_client_execute_sends_correct_request():
    """execute()는 POST 요청에 query와 variables를 포함해야 한다."""
    from oh_my_kanban.providers.linear.client import LinearClient

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"viewer": {"id": "u1"}}}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        client = LinearClient("lin_api_test")
        result = client.execute("{ viewer { id } }")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["json"]["query"] == "{ viewer { id } }"
        assert result == {"viewer": {"id": "u1"}}


def test_linear_client_execute_raises_graphql_error_on_errors_field():
    """execute()는 errors 필드가 있으면 LinearGraphQLError를 발생시켜야 한다."""
    from oh_my_kanban.providers.linear.client import LinearClient
    from oh_my_kanban.providers.linear.errors import LinearGraphQLError

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errors": [{"message": "Unauthorized"}]}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.post", return_value=mock_response):
        client = LinearClient("lin_api_test")
        with pytest.raises(LinearGraphQLError) as exc_info:
            client.execute("{ viewer { id } }")
        assert exc_info.value.errors[0]["message"] == "Unauthorized"


def test_linear_client_execute_raises_http_error_on_http_failure():
    """execute()는 HTTP 에러 시 LinearHttpError를 발생시켜야 한다."""
    from oh_my_kanban.providers.linear.client import LinearClient
    from oh_my_kanban.providers.linear.errors import LinearHttpError

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_request = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401", request=mock_request, response=mock_response
    )

    with patch("httpx.Client.post", return_value=mock_response):
        client = LinearClient("lin_api_test")
        with pytest.raises(LinearHttpError) as exc_info:
            client.execute("{ viewer { id } }")
        assert exc_info.value.status_code == 401


def test_linear_client_paginate_relay_single_page():
    """paginate_relay()는 단일 페이지 결과를 올바르게 수집해야 한다."""
    from oh_my_kanban.providers.linear.client import LinearClient

    nodes = [{"id": "i1"}, {"id": "i2"}]
    data = {"issues": {"nodes": nodes, "pageInfo": {"hasNextPage": False, "endCursor": None}}}

    with patch.object(LinearClient, "execute", return_value=data):
        client = LinearClient("lin_api_test")
        result = client.paginate_relay("query", {}, "issues")
        assert result == nodes


def test_linear_client_paginate_relay_multi_page():
    """paginate_relay()는 여러 페이지를 순회하여 모든 노드를 수집해야 한다."""
    from oh_my_kanban.providers.linear.client import LinearClient

    page1 = {"issues": {"nodes": [{"id": "i1"}], "pageInfo": {"hasNextPage": True, "endCursor": "c1"}}}
    page2 = {"issues": {"nodes": [{"id": "i2"}], "pageInfo": {"hasNextPage": False, "endCursor": None}}}

    with patch.object(LinearClient, "execute", side_effect=[page1, page2]):
        client = LinearClient("lin_api_test")
        result = client.paginate_relay("query", {}, "issues")
        assert result == [{"id": "i1"}, {"id": "i2"}]


def test_linear_client_paginate_relay_max_pages_warning(capsys):
    """paginate_relay()는 max_pages 초과 시 경고를 출력해야 한다."""
    from oh_my_kanban.providers.linear.client import LinearClient

    always_next = {"issues": {"nodes": [{"id": "x"}], "pageInfo": {"hasNextPage": True, "endCursor": "cx"}}}

    with patch.object(LinearClient, "execute", return_value=always_next):
        client = LinearClient("lin_api_test")
        result = client.paginate_relay("query", {}, "issues", max_pages=3)
        assert len(result) == 3
        captured = capsys.readouterr()
        assert "경고" in captured.err


# ─── LinearContext ─────────────────────────────────────────────────────────────

def test_linear_context_client_raises_without_api_key():
    """LinearContext.client는 api_key 없으면 click.UsageError를 발생시켜야 한다."""
    import click
    from oh_my_kanban.providers.linear.context import LinearContext

    ctx = LinearContext(_api_key="", team_id="")
    with pytest.raises(click.UsageError):
        _ = ctx.client


def test_linear_context_client_lazy_init():
    """LinearContext.client는 처음 접근 시 LinearClient를 생성해야 한다."""
    from oh_my_kanban.providers.linear.client import LinearClient
    from oh_my_kanban.providers.linear.context import LinearContext

    ctx = LinearContext(_api_key="lin_api_test", team_id="team1")
    assert ctx._client is None
    with patch.object(LinearClient, "__init__", return_value=None):
        _ = ctx.client
    assert ctx._client is not None


def test_linear_context_require_team_raises_without_team_id():
    """LinearContext.require_team()은 team_id 없으면 click.UsageError를 발생시켜야 한다."""
    import click
    from oh_my_kanban.providers.linear.context import LinearContext

    ctx = LinearContext(_api_key="lin_api_test", team_id="")
    with pytest.raises(click.UsageError):
        ctx.require_team()


def test_linear_context_require_team_returns_team_id():
    """LinearContext.require_team()은 team_id를 반환해야 한다."""
    from oh_my_kanban.providers.linear.context import LinearContext

    ctx = LinearContext(_api_key="lin_api_test", team_id="team-abc")
    assert ctx.require_team() == "team-abc"


# ─── Config ────────────────────────────────────────────────────────────────────

def test_config_has_linear_api_key_field():
    """Config에 linear_api_key 필드가 있어야 한다."""
    from oh_my_kanban.config import Config

    cfg = Config()
    assert hasattr(cfg, "linear_api_key")
    assert cfg.linear_api_key == ""


def test_config_has_linear_team_id_field():
    """Config에 linear_team_id 필드가 있어야 한다."""
    from oh_my_kanban.config import Config

    cfg = Config()
    assert hasattr(cfg, "linear_team_id")
    assert cfg.linear_team_id == ""


def test_load_config_reads_linear_api_key_from_env():
    """load_config()는 LINEAR_API_KEY 환경변수를 cfg.linear_api_key에 반영해야 한다."""
    from oh_my_kanban.config import load_config

    with patch.dict(os.environ, {"LINEAR_API_KEY": "lin_api_env_value"}):
        cfg = load_config()
    assert cfg.linear_api_key == "lin_api_env_value"


def test_load_config_reads_linear_team_id_from_env():
    """load_config()는 LINEAR_TEAM_ID 환경변수를 cfg.linear_team_id에 반영해야 한다."""
    from oh_my_kanban.config import load_config

    with patch.dict(os.environ, {"LINEAR_TEAM_ID": "team-from-env"}):
        cfg = load_config()
    assert cfg.linear_team_id == "team-from-env"


def test_load_config_reads_linear_keys_from_toml(tmp_path):
    """load_config()는 TOML 설정 파일의 Linear 키를 읽어야 한다."""
    from oh_my_kanban.config import load_config

    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '\n'.join(
            [
                "[default]",
                'linear_api_key = "lin_api_from_toml"',
                'linear_team_id = "team-from-toml"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.linear_api_key == "lin_api_from_toml"
    assert cfg.linear_team_id == "team-from-toml"


def test_save_config_writes_namespaced_provider_sections(tmp_path):
    """save_config()는 provider별 namespaced TOML 섹션으로 저장해야 한다."""
    from oh_my_kanban.config import save_config

    config_file = tmp_path / "config.toml"
    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        save_config(
            {
                "output": "json",
                "plane.api_key": "pl_key",
                "plane.workspace_slug": "team-a",
                "linear.api_key": "lin_key",
                "linear.team_id": "lin-team",
            }
        )

    saved = config_file.read_text(encoding="utf-8")
    assert "[default]" in saved
    assert "[default.plane]" in saved
    assert "[default.linear]" in saved
    assert 'workspace_slug = "team-a"' in saved
    assert 'team_id = "lin-team"' in saved


def test_save_config_migrates_legacy_flat_section_to_namespaced(tmp_path):
    """save_config()는 기존 flat profile을 namespaced profile로 재저장해야 한다."""
    from oh_my_kanban.config import save_config

    config_file = tmp_path / "config.toml"
    config_file.write_text(
        "\n".join(
            [
                "[default]",
                'base_url = "https://api.plane.so"',
                'api_key = "pl_key"',
                'workspace_slug = "team-a"',
                'linear_api_key = "lin_key"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        save_config({}, profile="default")

    saved = config_file.read_text(encoding="utf-8")
    assert "[default.plane]" in saved
    assert "[default.linear]" in saved
    assert "linear_api_key" not in saved
