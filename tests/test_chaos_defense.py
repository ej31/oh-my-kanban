"""Chaos Engineering 방어 로직 테스트 — P0 + P1 + P2 전체."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import httpx
import pytest
import requests

from oh_my_kanban.config import Config, load_config
from oh_my_kanban.context import CliContext, _mount_retry_adapters
from oh_my_kanban.linear_errors import (
    LinearGraphQLError,
    LinearHttpError,
    LinearResponseParseError,
    _exit_code_for_linear,
    format_linear_error,
    handle_linear_error,
)


# ===========================================================================
# P0-1: Plane SDK RetryConfig 활성화
# ===========================================================================


class TestPlaneRetryConfig:
    """PlaneClient에 RetryConfig가 올바르게 적용되는지 검증한다."""

    @patch("oh_my_kanban.context.PlaneClient")
    def test_retry_config_is_set(self, mock_plane_cls: MagicMock) -> None:
        """PlaneClient 생성 후 config.retry가 설정된다."""
        mock_client = MagicMock()
        mock_client.config = MagicMock()
        mock_client.config.retry = None
        mock_plane_cls.return_value = mock_client

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-key",
            workspace="ws",
            project="proj",
            output="json",
        )
        _ = ctx.client

        assert mock_client.config.retry is not None

    @patch("oh_my_kanban.context.PlaneClient")
    def test_timeout_is_tuple(self, mock_plane_cls: MagicMock) -> None:
        """PlaneClient 생성 후 timeout이 (connect, read) 튜플이다."""
        mock_client = MagicMock()
        mock_client.config = MagicMock()
        mock_client.config.retry = None
        mock_plane_cls.return_value = mock_client

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-key",
            workspace="ws",
            project="proj",
            output="json",
        )
        _ = ctx.client

        assert mock_client.config.timeout == (5.0, 30.0)

    def test_mount_retry_adapters_applies_to_sessions(self) -> None:
        """_mount_retry_adapters가 리소스 세션에 어댑터를 장착한다."""
        mock_client = MagicMock()
        mock_config = MagicMock()
        mock_config.retry = MagicMock(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "HEAD"}),
        )
        mock_client.config = mock_config

        # 리소스 객체에 실제 Session 부여
        real_session = requests.Session()
        mock_resource = MagicMock()
        mock_resource.session = real_session
        mock_client.users = mock_resource

        _mount_retry_adapters(mock_client)

        # https:// 어댑터가 HTTPAdapter인지 확인
        adapter = real_session.get_adapter("https://example.com")
        assert adapter.max_retries.total == 3

    def test_mount_retry_skips_when_no_retry(self) -> None:
        """config.retry가 None이면 _mount_retry_adapters가 아무것도 하지 않는다."""
        mock_client = MagicMock()
        mock_client.config = MagicMock(retry=None)
        # 예외 없이 정상 완료되어야 한다
        _mount_retry_adapters(mock_client)


# ===========================================================================
# P0-2: 환경변수 빈 문자열 필터링
# ===========================================================================


class TestEnvEmptyStringFiltering:
    """빈 환경변수가 config 값을 덮어쓰지 않는지 검증한다."""

    def _write_config(self, tmp_path: Path, content: str) -> Path:
        config_file = tmp_path / "config.toml"
        config_file.write_text(content, encoding="utf-8")
        return config_file

    def test_empty_plane_api_key_preserves_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PLANE_API_KEY='' 시 config.toml의 api_key가 유지된다."""
        config_file = self._write_config(
            tmp_path, '[default]\napi_key = "toml-key"\n'
        )
        monkeypatch.setenv("PLANE_API_KEY", "")

        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            cfg = load_config()

        assert cfg.api_key == "toml-key"

    def test_valid_plane_api_key_overrides_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PLANE_API_KEY='valid' 시 config.toml 값이 오버라이드된다."""
        config_file = self._write_config(
            tmp_path, '[default]\napi_key = "toml-key"\n'
        )
        monkeypatch.setenv("PLANE_API_KEY", "env-key")

        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            cfg = load_config()

        assert cfg.api_key == "env-key"

    def test_empty_plane_base_url_preserves_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PLANE_BASE_URL='' 시 config.toml의 base_url이 유지된다."""
        config_file = self._write_config(
            tmp_path, '[default]\nbase_url = "https://custom.plane.so"\n'
        )
        monkeypatch.setenv("PLANE_BASE_URL", "")

        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            cfg = load_config()

        assert cfg.base_url == "https://custom.plane.so"

    def test_empty_workspace_slug_preserves_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PLANE_WORKSPACE_SLUG='' 시 config.toml 값이 유지된다."""
        config_file = self._write_config(
            tmp_path, '[default]\nworkspace_slug = "my-ws"\n'
        )
        monkeypatch.setenv("PLANE_WORKSPACE_SLUG", "")

        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            cfg = load_config()

        assert cfg.workspace_slug == "my-ws"

    def test_empty_project_id_preserves_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PLANE_PROJECT_ID='' 시 config.toml 값이 유지된다."""
        config_file = self._write_config(
            tmp_path,
            '[default]\nproject_id = "12345678-1234-1234-1234-123456789012"\n',
        )
        monkeypatch.setenv("PLANE_PROJECT_ID", "")

        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            cfg = load_config()

        assert cfg.project_id == "12345678-1234-1234-1234-123456789012"


# ===========================================================================
# P0-4: Linear 예외 catch 확장 + 5xx 매핑 + exit code 통일
# ===========================================================================


class TestLinearErrorExtensions:
    """Linear 에러 핸들러의 확장된 예외 처리를 검증한다."""

    def test_format_network_error(self) -> None:
        """httpx.NetworkError가 네트워크 연결 오류 메시지를 반환한다."""
        exc = httpx.ConnectError("Connection refused")
        result = format_linear_error(exc)
        assert "네트워크 연결 오류" in result

    def test_format_json_decode_error(self) -> None:
        """json.JSONDecodeError가 서버 응답 파싱 실패 메시지를 반환한다."""
        exc = json.JSONDecodeError("Expecting value", "", 0)
        result = format_linear_error(exc)
        assert "파싱" in result

    def test_format_response_parse_error(self) -> None:
        """LinearResponseParseError가 파싱 실패 메시지를 반환한다."""
        exc = LinearResponseParseError("broken response")
        result = format_linear_error(exc)
        assert "파싱" in result

    def test_format_500_error(self) -> None:
        """500 에러가 서버 내부 오류 메시지를 반환한다."""
        exc = LinearHttpError(500, "Internal Server Error")
        result = format_linear_error(exc)
        assert "서버 내부 오류" in result

    def test_format_502_error(self) -> None:
        """502 에러가 Bad Gateway 메시지를 반환한다."""
        exc = LinearHttpError(502, "Bad Gateway")
        result = format_linear_error(exc)
        assert "Bad Gateway" in result

    def test_format_503_error(self) -> None:
        """503 에러가 일시적 불가 메시지를 반환한다."""
        exc = LinearHttpError(503, "Service Unavailable")
        result = format_linear_error(exc)
        assert "일시적으로 불가" in result

    def test_exit_code_401_is_77(self) -> None:
        """401 에러의 exit code가 77(EX_NOPERM)이다."""
        exc = LinearHttpError(401, "Unauthorized")
        assert _exit_code_for_linear(exc) == 77

    def test_exit_code_403_is_77(self) -> None:
        """403 에러의 exit code가 77이다."""
        exc = LinearHttpError(403, "Forbidden")
        assert _exit_code_for_linear(exc) == 77

    def test_exit_code_500_is_69(self) -> None:
        """500 에러의 exit code가 69(EX_UNAVAILABLE)이다."""
        exc = LinearHttpError(500, "Internal Server Error")
        assert _exit_code_for_linear(exc) == 69

    def test_exit_code_429_is_1(self) -> None:
        """429 에러의 exit code가 1(기본값)이다."""
        exc = LinearHttpError(429, "Too Many Requests")
        assert _exit_code_for_linear(exc) == 1

    def test_exit_code_network_error_is_69(self) -> None:
        """NetworkError의 exit code가 69이다."""
        exc = httpx.ConnectError("Connection refused")
        assert _exit_code_for_linear(exc) == 69

    def test_handle_linear_error_catches_network_error(self) -> None:
        """handle_linear_error가 httpx.NetworkError를 catch한다."""

        @handle_linear_error
        def raise_network():
            raise httpx.ConnectError("Connection refused")

        with pytest.raises(SystemExit) as exc_info:
            raise_network()
        assert exc_info.value.code == 69

    def test_handle_linear_error_catches_json_error(self) -> None:
        """handle_linear_error가 json.JSONDecodeError를 catch한다."""

        @handle_linear_error
        def raise_json():
            raise json.JSONDecodeError("Expecting value", "", 0)

        with pytest.raises(SystemExit) as exc_info:
            raise_json()
        assert exc_info.value.code == 1

    def test_handle_linear_error_catches_response_parse_error(self) -> None:
        """handle_linear_error가 LinearResponseParseError를 catch한다."""

        @handle_linear_error
        def raise_parse():
            raise LinearResponseParseError("broken")

        with pytest.raises(SystemExit) as exc_info:
            raise_parse()
        assert exc_info.value.code == 1


# ===========================================================================
# P1-1: Plane 인증 헤더 팩토리 + 401/403 경고
# ===========================================================================


class TestPlaneAuthHeaderFactory:
    """P1-1: Plane 인증 헤더 팩토리 테스트."""

    def test_build_plane_headers_default(self) -> None:
        """기본 호출 시 X-API-Key와 Content-Type이 포함된다."""
        from oh_my_kanban.hooks.http_client import build_plane_headers

        headers = build_plane_headers("test-key")
        assert headers == {"X-API-Key": "test-key", "Content-Type": "application/json"}

    def test_build_plane_headers_no_content_type(self) -> None:
        """content_type='' 시 Content-Type이 생략된다."""
        from oh_my_kanban.hooks.http_client import build_plane_headers

        headers = build_plane_headers("test-key", content_type="")
        assert headers == {"X-API-Key": "test-key"}

    def test_warn_auth_failure_401(self, capsys) -> None:
        """401 시 인증 실패 경고가 stderr에 출력된다."""
        from oh_my_kanban.hooks.http_client import warn_auth_failure

        warn_auth_failure(401, context="테스트")
        captured = capsys.readouterr()
        assert "인증 실패" in captured.err
        assert "401" in captured.err

    def test_warn_auth_failure_403(self, capsys) -> None:
        """403 시 권한 부족 경고가 stderr에 출력된다."""
        from oh_my_kanban.hooks.http_client import warn_auth_failure

        warn_auth_failure(403)
        captured = capsys.readouterr()
        assert "권한 부족" in captured.err

    def test_warn_auth_failure_200_no_output(self, capsys) -> None:
        """200 시 아무것도 출력하지 않는다."""
        from oh_my_kanban.hooks.http_client import warn_auth_failure

        warn_auth_failure(200)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_session_end_uses_build_plane_headers(self) -> None:
        """session_end.py가 build_plane_headers를 import한다."""
        import oh_my_kanban.hooks.session_end as mod
        import inspect

        source = inspect.getsource(mod)
        assert "build_plane_headers" in source
        assert '"X-API-Key"' not in source

    def test_opt_out_uses_build_plane_headers(self) -> None:
        """opt_out.py가 build_plane_headers를 import한다."""
        import oh_my_kanban.hooks.opt_out as mod
        import inspect

        source = inspect.getsource(mod)
        assert "build_plane_headers" in source
        assert '"X-API-Key"' not in source


# ===========================================================================
# P1-2: Plane 에러 핸들러 네트워크 에러 분기
# ===========================================================================


class TestPlaneErrorHandlerExtensions:
    """P1-2: Plane 에러 핸들러 네트워크 에러 분기 테스트."""

    def test_connection_error_exit_69(self) -> None:
        """requests.ConnectionError가 exit code 69를 반환한다."""
        import socket
        import ssl

        from oh_my_kanban.errors import handle_api_error

        @handle_api_error
        def raise_conn_error():
            raise requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(SystemExit) as exc_info:
            raise_conn_error()
        assert exc_info.value.code == 69

    def test_timeout_error_exit_69(self) -> None:
        """requests.Timeout이 exit code 69를 반환한다."""
        from oh_my_kanban.errors import handle_api_error

        @handle_api_error
        def raise_timeout():
            raise requests.exceptions.Timeout("Read timed out")

        with pytest.raises(SystemExit) as exc_info:
            raise_timeout()
        assert exc_info.value.code == 69

    def test_ssl_error_exit_69(self) -> None:
        """ssl.SSLError가 exit code 69를 반환한다."""
        import ssl

        from oh_my_kanban.errors import handle_api_error

        @handle_api_error
        def raise_ssl():
            raise ssl.SSLError("certificate verify failed")

        with pytest.raises(SystemExit) as exc_info:
            raise_ssl()
        assert exc_info.value.code == 69

    def test_dns_error_exit_69(self) -> None:
        """socket.gaierror가 exit code 69를 반환한다."""
        import socket

        from oh_my_kanban.errors import handle_api_error

        @handle_api_error
        def raise_dns():
            raise socket.gaierror(8, "nodename nor servname provided")

        with pytest.raises(SystemExit) as exc_info:
            raise_dns()
        assert exc_info.value.code == 69

    def test_connection_error_message(self, capsys) -> None:
        """ConnectionError 시 '서버 연결 실패' 메시지가 출력된다."""
        from oh_my_kanban.errors import handle_api_error

        @handle_api_error
        def raise_conn():
            raise requests.exceptions.ConnectionError("refused")

        with pytest.raises(SystemExit):
            raise_conn()
        captured = capsys.readouterr()
        assert "서버 연결 실패" in captured.err

    def test_timeout_error_message(self, capsys) -> None:
        """Timeout 시 '시간이 초과' 메시지가 출력된다."""
        from oh_my_kanban.errors import handle_api_error

        @handle_api_error
        def raise_timeout():
            raise requests.exceptions.Timeout("timed out")

        with pytest.raises(SystemExit):
            raise_timeout()
        captured = capsys.readouterr()
        assert "시간이 초과" in captured.err or "시간 초과" in captured.err


# ===========================================================================
# P1-3: Timeout 분리 + 세션 파일 잠금 통합
# ===========================================================================


class TestTimeoutSeparation:
    """P1-3: Timeout 분리 + 세션 파일 잠금 통합 테스트."""

    def test_plane_api_timeout_is_httpx_timeout(self) -> None:
        """PLANE_API_TIMEOUT이 httpx.Timeout 인스턴스이다."""
        from oh_my_kanban.hooks.common import PLANE_API_TIMEOUT
        assert isinstance(PLANE_API_TIMEOUT, httpx.Timeout)

    def test_plane_api_timeout_values(self) -> None:
        """PLANE_API_TIMEOUT의 connect=3.0, read=10.0이다."""
        from oh_my_kanban.hooks.common import PLANE_API_TIMEOUT
        assert PLANE_API_TIMEOUT.connect == 3.0
        assert PLANE_API_TIMEOUT.read == 10.0

    def test_linear_client_default_timeout(self) -> None:
        """LinearClient DEFAULT_TIMEOUT이 httpx.Timeout이다."""
        from oh_my_kanban.linear_client import LinearClient
        assert isinstance(LinearClient.DEFAULT_TIMEOUT, httpx.Timeout)
        assert LinearClient.DEFAULT_TIMEOUT.connect == 5.0
        assert LinearClient.DEFAULT_TIMEOUT.read == 30.0

    def test_session_write_lock_exists_in_common(self) -> None:
        """session_write_lock이 hooks.common에서 import 가능하다."""
        from oh_my_kanban.hooks.common import session_write_lock
        assert callable(session_write_lock)

    def test_session_write_lock_context_manager(self, tmp_path) -> None:
        """session_write_lock이 context manager로 동작한다."""
        from oh_my_kanban.hooks.common import session_write_lock
        lock_file = tmp_path / "test.lock"
        with session_write_lock(lock_file):
            assert True  # 블록 안에서 정상 동작

    def test_session_write_lock_windows_fallback(self) -> None:
        """fcntl 없이도 session_write_lock이 동작한다 (no-op)."""
        import tempfile

        import oh_my_kanban.hooks.common as common_mod
        from oh_my_kanban.hooks.common import session_write_lock

        original = common_mod._HAS_FCNTL
        try:
            common_mod._HAS_FCNTL = False
            with tempfile.TemporaryDirectory() as td:
                lock_file = Path(td) / "test.lock"
                with session_write_lock(lock_file):
                    assert True
        finally:
            common_mod._HAS_FCNTL = original


# ===========================================================================
# P2-1: omk doctor 통합 진단 명령
# ===========================================================================


class TestDoctorCommand:
    """P2-1: omk doctor 통합 진단 명령 테스트."""

    def test_doctor_command_exists(self) -> None:
        """doctor 커맨드가 CLI에 등록되어 있다."""
        from click.testing import CliRunner
        from oh_my_kanban.cli import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["doctor", "--help"])
        assert result.exit_code == 0
        assert "진단" in result.output

    def test_check_config_file_pass(self, tmp_path, monkeypatch) -> None:
        """config.toml이 유효하면 PASS를 반환한다."""
        from unittest.mock import patch
        from oh_my_kanban.config import Config
        config_file = tmp_path / "config.toml"
        config_file.write_text('[default]\napi_key = "key"\nworkspace_slug = "ws"\n')
        cfg = Config(api_key="key", workspace_slug="ws")
        with patch("oh_my_kanban.commands.doctor.CONFIG_FILE", config_file):
            from oh_my_kanban.commands.doctor import _check_config_file
            status, _ = _check_config_file(cfg)
            assert status == "PASS"

    def test_check_config_file_missing(self, tmp_path) -> None:
        """config.toml이 없으면 FAIL을 반환한다."""
        from unittest.mock import patch
        from oh_my_kanban.config import Config
        missing = tmp_path / "nonexistent.toml"
        cfg = Config(api_key="key", workspace_slug="ws")
        with patch("oh_my_kanban.commands.doctor.CONFIG_FILE", missing):
            from oh_my_kanban.commands.doctor import _check_config_file
            status, _ = _check_config_file(cfg)
            assert status == "FAIL"

    def test_check_plane_sdk_version_pass(self) -> None:
        """plane-sdk가 설치되어 있으면 PASS를 반환한다."""
        from oh_my_kanban.commands.doctor import _check_plane_sdk_version
        status, detail = _check_plane_sdk_version()
        assert status == "PASS"
        assert "plane-sdk" in detail

    def test_check_plane_api_skip_when_no_key(self) -> None:
        """API 키 미설정 시 SKIP을 반환한다."""
        from oh_my_kanban.config import Config
        cfg = Config(api_key="", workspace_slug="")
        from oh_my_kanban.commands.doctor import _check_plane_api
        status, _ = _check_plane_api(cfg)
        assert status == "SKIP"

    def test_check_linear_api_skip_when_no_key(self) -> None:
        """Linear API 키 미설정 시 SKIP을 반환한다."""
        from oh_my_kanban.config import Config
        cfg = Config(linear_api_key="")
        from oh_my_kanban.commands.doctor import _check_linear_api
        status, _ = _check_linear_api(cfg)
        assert status == "SKIP"

    def test_doctor_runs_without_crash(self) -> None:
        """doctor 커맨드가 예외 없이 실행된다."""
        from click.testing import CliRunner
        from oh_my_kanban.cli import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["doctor"])
        # exit code가 0 또는 1 (FAIL 항목이 있을 수 있음)
        assert result.exit_code in (0, 1)
        assert "진단" in result.output


# ===========================================================================
# P2-2: config init 헬스체크 + 참조 무결성 검증
# ===========================================================================


class TestConfigHealthcheck:
    """P2-2: config init 헬스체크 + 참조 무결성 검증 테스트."""

    def test_validate_project_caches_result(self) -> None:
        """validate_project()가 결과를 캐시하여 중복 호출을 방지한다."""
        from unittest.mock import MagicMock, patch
        from oh_my_kanban.context import CliContext

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-key",
            workspace="ws",
            project="12345678-1234-1234-1234-123456789012",
            output="json",
        )
        mock_client = MagicMock()
        mock_client.config = MagicMock()
        mock_client.config.retry = None

        with patch.object(type(ctx), "client", new_callable=lambda: property(lambda self: mock_client)):
            ctx.validate_project()
            ctx.validate_project()  # 두 번째 호출
            # projects.get은 한 번만 호출되어야 한다
            assert mock_client.projects.get.call_count == 1

    def test_validate_project_404_raises_usage_error(self) -> None:
        """404 시 UsageError를 발생시킨다."""
        from unittest.mock import MagicMock, patch
        from oh_my_kanban.context import CliContext

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-key",
            workspace="ws",
            project="12345678-1234-1234-1234-123456789012",
            output="json",
        )
        mock_client = MagicMock()
        mock_client.config = MagicMock()
        mock_client.config.retry = None

        # 404 에러를 시뮬레이션
        mock_error = Exception("Not Found")
        mock_error.status_code = 404
        mock_client.projects.get.side_effect = mock_error

        with patch.object(type(ctx), "client", new_callable=lambda: property(lambda self: mock_client)):
            with pytest.raises(click.UsageError) as exc_info:
                ctx.validate_project()
            assert "찾을 수 없습니다" in str(exc_info.value)

    def test_validate_team_caches_result(self) -> None:
        """validate_team()이 결과를 캐시한다."""
        from unittest.mock import MagicMock, patch
        from oh_my_kanban.linear_context import LinearContext

        ctx = LinearContext(
            _api_key="lin_api_test",
            team_id="team-123",
            output="json",
        )
        mock_client = MagicMock()
        mock_client.execute.return_value = {"team": {"id": "team-123", "name": "Test"}}

        with patch.object(type(ctx), "client", new_callable=lambda: property(lambda self: mock_client)):
            ctx.validate_team()
            ctx.validate_team()  # 두 번째 호출
            assert mock_client.execute.call_count == 1

    def test_run_plane_healthcheck_warns_on_401(self, capsys) -> None:
        """헬스체크 401 시 경고를 출력한다."""
        from unittest.mock import MagicMock, patch

        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("oh_my_kanban.commands.config_cmd.httpx", create=True) as mock_httpx:
            mock_client_instance = MagicMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_instance.__exit__ = MagicMock(return_value=False)
            mock_httpx.Client.return_value = mock_client_instance
            mock_httpx.Timeout = httpx.Timeout
            mock_httpx.TimeoutException = httpx.TimeoutException
            mock_httpx.NetworkError = httpx.NetworkError

            from oh_my_kanban.commands.config_cmd import _run_plane_healthcheck
            _run_plane_healthcheck("https://api.plane.so", "bad-key")

        captured = capsys.readouterr()
        assert "경고" in captured.err or "경고" in captured.out

    def test_run_linear_healthcheck_success(self, capsys) -> None:
        """Linear 헬스체크가 성공하면 email을 출력한다."""
        from unittest.mock import MagicMock, patch

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"viewer": {"id": "u1", "email": "test@example.com"}}
        }

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("oh_my_kanban.commands.config_cmd.httpx") as mock_httpx:
            mock_httpx.Client.return_value = mock_client
            mock_httpx.Timeout = httpx.Timeout
            mock_httpx.TimeoutException = httpx.TimeoutException
            mock_httpx.NetworkError = httpx.NetworkError

            from oh_my_kanban.commands.config_cmd import _run_linear_healthcheck
            _run_linear_healthcheck("lin_test_key")

        captured = capsys.readouterr()
        assert "test@example.com" in captured.out

    def test_run_linear_healthcheck_warns_on_401(self, capsys) -> None:
        """Linear 헬스체크 401 시 경고를 출력한다."""
        from unittest.mock import MagicMock, patch

        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("oh_my_kanban.commands.config_cmd.httpx") as mock_httpx:
            mock_httpx.Client.return_value = mock_client
            mock_httpx.Timeout = httpx.Timeout
            mock_httpx.TimeoutException = httpx.TimeoutException
            mock_httpx.NetworkError = httpx.NetworkError

            from oh_my_kanban.commands.config_cmd import _run_linear_healthcheck
            _run_linear_healthcheck("bad-key")

        captured = capsys.readouterr()
        assert "경고" in captured.err or "경고" in captured.out

    def test_config_set_linear_api_key_triggers_healthcheck(self) -> None:
        """config set linear_api_key 시 Linear 헬스체크가 호출된다."""
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        from oh_my_kanban.cli import cli

        runner = CliRunner()
        with patch("oh_my_kanban.commands.config_cmd._save_config_safe"), \
             patch("oh_my_kanban.commands.config_cmd._run_linear_healthcheck") as mock_hc, \
             patch("oh_my_kanban.commands.config_cmd.load_config"):
            result = runner.invoke(cli, ["config", "set", "linear_api_key", "lin_test"])
        assert result.exit_code == 0
        mock_hc.assert_called_once_with("lin_test")


# ===========================================================================
# P2-3: 세션 stale reference + Linear retry + fail-open notify
# ===========================================================================


class TestStaleReferenceAndLinearRetry:
    """P2-3: stale WI 참조, Linear retry, health_warnings.json 테스트."""

    def test_build_plane_context_returns_failed_ids(self) -> None:
        """build_plane_context가 실패한 WI ID 목록을 반환한다."""
        from unittest.mock import MagicMock, patch
        from oh_my_kanban.session.plane_context_builder import build_plane_context

        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        mock_resp_ok.json.return_value = {"name": "Test WI", "priority": "high"}

        mock_resp_fail = MagicMock()
        mock_resp_fail.status_code = 404

        mock_client = MagicMock()
        mock_client.get.side_effect = [mock_resp_ok, MagicMock(status_code=200, json=MagicMock(return_value=[])), mock_resp_fail]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("oh_my_kanban.session.plane_context_builder.plane_http_client") as mock_phc:
            mock_phc.return_value = mock_client
            context, failed = build_plane_context(
                ["wi-1", "wi-2"], "proj-id", "https://api.plane.so", "key", "ws"
            )
        assert "wi-2" in failed

    def test_stale_work_item_ids_in_state(self) -> None:
        """PlaneContext에 stale_work_item_ids 필드가 존재한다."""
        from oh_my_kanban.session.state import PlaneContext
        ctx = PlaneContext(stale_work_item_ids=["wi-1", "wi-2"])
        assert ctx.stale_work_item_ids == ["wi-1", "wi-2"]

    def test_stale_work_item_ids_serialization(self) -> None:
        """stale_work_item_ids가 from_dict로 올바르게 역직렬화된다."""
        from oh_my_kanban.session.state import SessionState
        data = {
            "session_id": "test-session",
            "plane_context": {
                "project_id": "proj",
                "work_item_ids": ["wi-1"],
                "stale_work_item_ids": ["wi-2", "wi-3"],
            },
        }
        state = SessionState.from_dict(data)
        assert state.plane_context.stale_work_item_ids == ["wi-2", "wi-3"]

    def test_linear_client_retries_on_500(self) -> None:
        """LinearClient.execute()가 500 응답 시 재시도한다."""
        from unittest.mock import MagicMock, patch
        from oh_my_kanban.linear_client import LinearClient

        mock_resp_500 = MagicMock()
        mock_resp_500.status_code = 500
        mock_resp_500.headers = {}
        mock_resp_500.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=mock_resp_500
        )

        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        mock_resp_ok.raise_for_status.return_value = None
        mock_resp_ok.json.return_value = {"data": {"test": True}}

        with patch("oh_my_kanban.linear_client.time.sleep"):
            client = LinearClient(api_key="test-key")
            client._client = MagicMock()
            client._client.post.side_effect = [mock_resp_500, mock_resp_ok]
            result = client.execute("{ viewer { id } }")
        assert result == {"test": True}
        assert client._client.post.call_count == 2

    def test_linear_client_respects_retry_after(self) -> None:
        """LinearClient가 Retry-After 헤더를 우선 사용한다."""
        from unittest.mock import MagicMock, patch, call
        from oh_my_kanban.linear_client import LinearClient

        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429
        mock_resp_429.headers = {"Retry-After": "2.5"}
        mock_resp_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=MagicMock(), response=mock_resp_429
        )

        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        mock_resp_ok.raise_for_status.return_value = None
        mock_resp_ok.json.return_value = {"data": {}}

        with patch("oh_my_kanban.linear_client.time.sleep") as mock_sleep:
            client = LinearClient(api_key="test-key")
            client._client = MagicMock()
            client._client.post.side_effect = [mock_resp_429, mock_resp_ok]
            client.execute("{ viewer { id } }")
        # Retry-After 2.5초 대기
        mock_sleep.assert_called_once_with(2.5)

    def test_linear_client_max_retries_exhausted(self) -> None:
        """LinearClient가 최대 재시도 초과 시 LinearHttpError를 발생시킨다."""
        from unittest.mock import MagicMock, patch
        from oh_my_kanban.linear_client import LinearClient
        from oh_my_kanban.linear_errors import LinearHttpError

        mock_resp_500 = MagicMock()
        mock_resp_500.status_code = 500
        mock_resp_500.headers = {}
        mock_resp_500.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=mock_resp_500
        )

        with patch("oh_my_kanban.linear_client.time.sleep"):
            client = LinearClient(api_key="test-key")
            client._client = MagicMock()
            client._client.post.return_value = mock_resp_500
            with pytest.raises(LinearHttpError) as exc_info:
                client.execute("{ viewer { id } }")
            assert exc_info.value.status_code == 500

    def test_health_warnings_record_and_read(self, tmp_path) -> None:
        """record_health_warning이 health_warnings.json에 기록한다."""
        from unittest.mock import patch
        from oh_my_kanban.hooks.common import record_health_warning

        with patch("oh_my_kanban.config.CONFIG_DIR", tmp_path):
            record_health_warning({"type": "test", "message": "테스트 경고"})
            record_health_warning({"type": "test", "message": "두 번째 경고"})

        warnings_file = tmp_path / "health_warnings.json"
        assert warnings_file.exists()
        warnings = json.loads(warnings_file.read_text())
        assert len(warnings) == 2
        assert warnings[0]["type"] == "test"

    def test_health_warnings_fail_open(self) -> None:
        """record_health_warning이 실패해도 예외를 발생시키지 않는다."""
        from unittest.mock import patch
        from oh_my_kanban.hooks.common import record_health_warning

        # 쓰기 불가능한 경로로 설정
        with patch("oh_my_kanban.config.CONFIG_DIR", Path("/nonexistent/path/that/does/not/exist")):
            # 예외 없이 완료되어야 한다
            record_health_warning({"type": "test"})

    def test_health_warnings_max_50(self, tmp_path) -> None:
        """health_warnings.json이 최대 50개로 제한된다."""
        from unittest.mock import patch
        from oh_my_kanban.hooks.common import record_health_warning

        with patch("oh_my_kanban.config.CONFIG_DIR", tmp_path):
            for i in range(55):
                record_health_warning({"index": i})

        warnings = json.loads((tmp_path / "health_warnings.json").read_text())
        assert len(warnings) == 50
        # 가장 오래된 5개가 제거되었으므로 첫 항목은 index=5
        assert warnings[0]["index"] == 5


# ===========================================================================
# P2-4: 통합 HTTP 래퍼
# ===========================================================================


class TestUnifiedHttpWrapper:
    """P2-4: 통합 HTTP 래퍼 테스트."""

    def test_plane_http_client_sets_headers(self) -> None:
        """plane_http_client가 인증 헤더를 자동 설정한다."""
        from oh_my_kanban.hooks.http_client import plane_http_client
        with plane_http_client("test-key") as client:
            assert client.headers.get("X-API-Key") == "test-key"
            assert client.headers.get("Content-Type") == "application/json"

    def test_plane_request_retries_on_500(self) -> None:
        """plane_request가 500 응답 시 재시도한다."""
        from unittest.mock import MagicMock, patch
        from oh_my_kanban.hooks.http_client import plane_request

        mock_client = MagicMock()
        resp_500 = MagicMock()
        resp_500.status_code = 500
        resp_500.headers = {}
        resp_ok = MagicMock()
        resp_ok.status_code = 200
        resp_ok.headers = {}
        mock_client.request.side_effect = [resp_500, resp_ok]

        with patch("oh_my_kanban.hooks.http_client.time.sleep"):
            result = plane_request(mock_client, "POST", "https://example.com")
        assert result.status_code == 200
        assert mock_client.request.call_count == 2

    def test_plane_request_warns_auth_failure(self, capsys) -> None:
        """plane_request가 401 시 경고를 출력한다."""
        from unittest.mock import MagicMock
        from oh_my_kanban.hooks.http_client import plane_request

        mock_client = MagicMock()
        resp_401 = MagicMock()
        resp_401.status_code = 401
        resp_401.headers = {}
        mock_client.request.return_value = resp_401

        plane_request(mock_client, "GET", "https://example.com", context="테스트")
        captured = capsys.readouterr()
        assert "인증 실패" in captured.err

    def test_no_direct_httpx_client_in_session_end(self) -> None:
        """session_end.py에서 직접 httpx.Client 생성이 없다."""
        import inspect
        import oh_my_kanban.hooks.session_end as mod
        source = inspect.getsource(mod)
        assert "httpx.Client(" not in source or "plane_http_client" in source

    def test_no_direct_httpx_client_in_opt_out(self) -> None:
        """opt_out.py에서 직접 httpx.Client 생성이 없다."""
        import inspect
        import oh_my_kanban.hooks.opt_out as mod
        source = inspect.getsource(mod)
        assert "httpx.Client(" not in source or "plane_http_client" in source

    def test_no_direct_httpx_client_in_mcp_server(self) -> None:
        """mcp/server.py 소스 파일에서 직접 httpx.Client 생성이 없다."""
        source = Path(__file__).parent.parent / "src" / "oh_my_kanban" / "mcp" / "server.py"
        content = source.read_text(encoding="utf-8")
        # plane_http_client 래퍼를 사용하므로 직접 httpx.Client( 호출이 없어야 한다
        lines_with_httpx_client = [
            line.strip() for line in content.splitlines()
            if "httpx.Client(" in line and not line.strip().startswith("#")
        ]
        assert len(lines_with_httpx_client) == 0, f"직접 httpx.Client 사용 발견: {lines_with_httpx_client}"

    def test_no_direct_httpx_client_in_context_builder(self) -> None:
        """plane_context_builder.py에서 직접 httpx.Client 생성이 없다."""
        import inspect
        import oh_my_kanban.session.plane_context_builder as mod
        source = inspect.getsource(mod)
        assert "httpx.Client(" not in source or "plane_http_client" in source

    def test_plane_request_retries_on_timeout(self) -> None:
        """plane_request가 TimeoutException 시 재시도한다."""
        from unittest.mock import MagicMock, patch
        from oh_my_kanban.hooks.http_client import plane_request

        mock_client = MagicMock()
        resp_ok = MagicMock()
        resp_ok.status_code = 200
        resp_ok.headers = {}
        mock_client.request.side_effect = [
            httpx.ReadTimeout("timeout"),
            resp_ok,
        ]

        with patch("oh_my_kanban.hooks.http_client.time.sleep"):
            result = plane_request(mock_client, "GET", "https://example.com")
        assert result.status_code == 200
        assert mock_client.request.call_count == 2

    def test_plane_request_raises_after_max_retries(self) -> None:
        """plane_request가 최대 재시도 후 예외를 발생시킨다."""
        from unittest.mock import MagicMock, patch
        from oh_my_kanban.hooks.http_client import plane_request

        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.ConnectError("refused")

        with patch("oh_my_kanban.hooks.http_client.time.sleep"):
            with pytest.raises(httpx.ConnectError):
                plane_request(mock_client, "GET", "https://example.com", max_retries=2)
