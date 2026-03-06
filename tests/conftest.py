"""테스트 공통 픽스처."""

from collections.abc import Callable

import pytest
from click.testing import CliRunner, Result

from oh_my_kanban.cli import cli


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
