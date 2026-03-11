"""테스트 공통 픽스처."""

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner, Result

from oh_my_kanban.cli import cli
from oh_my_kanban.providers.plane.context import PlaneContext as CliContext

# ---------------------------------------------------------------------------
# 기본 픽스처
# ---------------------------------------------------------------------------


@pytest.fixture
def runner() -> CliRunner:
    """Click CLI 테스트용 CliRunner 픽스처."""
    return CliRunner()


@pytest.fixture
def invoke(runner: CliRunner) -> Callable[..., Result]:
    """CLI 커맨드를 실행하는 헬퍼 픽스처."""
    def _invoke(*args: str) -> Result:
        return runner.invoke(cli, list(args))
    return _invoke


@pytest.fixture
def ctx() -> CliContext:
    """기본 CliContext 픽스처 (API 키, workspace, project 모두 설정)."""
    context = CliContext(
        _base_url="https://api.plane.so",
        _api_key="test-api-key",
        workspace="test-workspace",
        project="test-project-id",
        output="json",
    )
    context._client = MagicMock()
    return context


@pytest.fixture
def no_project_ctx() -> CliContext:
    """project 없는 CliContext 픽스처."""
    context = CliContext(
        _base_url="https://api.plane.so",
        _api_key="test-api-key",
        workspace="test-workspace",
        project="",
        output="json",
    )
    context._client = MagicMock()
    return context


@pytest.fixture
def no_api_key_ctx() -> CliContext:
    """API 키 없는 CliContext 픽스처."""
    context = CliContext(
        _base_url="https://api.plane.so",
        _api_key="",
        workspace="test-workspace",
        project="test-project-id",
        output="json",
    )
    return context


@pytest.fixture
def no_workspace_ctx() -> CliContext:
    """workspace 없는 CliContext 픽스처."""
    context = CliContext(
        _base_url="https://api.plane.so",
        _api_key="test-api-key",
        workspace="",
        project="",
        output="json",
    )
    context._client = MagicMock()
    return context
