"""US-003: GitHub CLI wrapper 테스트.

gh CLI를 통한 GitHub 이슈/PR 관리 기능을 검증한다.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from oh_my_kanban.cli import cli
from oh_my_kanban.commands.github_stub import _check_gh_available, _run_gh


# ── _check_gh_available ───────────────────────────────────────────────────────


class TestCheckGhAvailable:
    """gh CLI 존재 여부 검증 테스트."""

    def test_gh_not_found_raises(self) -> None:
        """gh가 없으면 ClickException이 발생해야 한다."""
        import click

        with patch("oh_my_kanban.commands.github_stub.shutil.which", return_value=None):
            with pytest.raises(click.ClickException, match="gh CLI를 찾을 수 없습니다"):
                _check_gh_available()

    def test_gh_found_no_error(self) -> None:
        """gh가 있으면 예외 없이 통과해야 한다."""
        with patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"):
            _check_gh_available()  # 예외 없음


# ── _run_gh ───────────────────────────────────────────────────────────────────


class TestRunGh:
    """_run_gh 함수 테스트."""

    def test_successful_command(self) -> None:
        """정상 실행 시 stdout을 반환해야 한다."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "issue #1\nissue #2\n"
        mock_result.stderr = ""

        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch("oh_my_kanban.commands.github_stub.subprocess.run", return_value=mock_result),
        ):
            output = _run_gh("issue", "list")
            assert "issue #1" in output

    def test_auth_error_detected(self) -> None:
        """인증 오류 시 auth login 안내가 포함되어야 한다."""
        import click

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "gh auth login required"

        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch("oh_my_kanban.commands.github_stub.subprocess.run", return_value=mock_result),
        ):
            with pytest.raises(click.ClickException, match="GitHub 인증이 필요합니다"):
                _run_gh("issue", "list")

    def test_timeout_raises(self) -> None:
        """타임아웃 시 적절한 에러 메시지가 나와야 한다."""
        import click

        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch(
                "oh_my_kanban.commands.github_stub.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=30),
            ),
        ):
            with pytest.raises(click.ClickException, match="완료되지 않았습니다"):
                _run_gh("issue", "list")

    def test_oserror_raises_click_exception(self) -> None:
        """OSError 발생 시 gh 실행 실패 메시지가 나와야 한다."""
        import click

        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch(
                "oh_my_kanban.commands.github_stub.subprocess.run",
                side_effect=OSError("Permission denied"),
            ),
        ):
            with pytest.raises(click.ClickException, match="gh 실행 실패"):
                _run_gh("issue", "list")

    def test_generic_command_failure(self) -> None:
        """일반 명령 실패 시 에러 메시지가 나와야 한다."""
        import click

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "repository not found"

        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch("oh_my_kanban.commands.github_stub.subprocess.run", return_value=mock_result),
        ):
            with pytest.raises(click.ClickException, match="repository not found"):
                _run_gh("issue", "list")


# ── CLI 커맨드 통합 테스트 (subprocess mock) ──────────────────────────────────


class TestGitHubCLICommands:
    """GitHub CLI 커맨드 통합 테스트."""

    def _mock_run(self, stdout: str = "") -> MagicMock:
        """subprocess.run mock을 생성한다."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = stdout
        mock_result.stderr = ""
        return mock_result

    def test_issue_list_command(self) -> None:
        """omk github issue list 명령이 정상 실행되어야 한다."""
        runner = CliRunner()
        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch(
                "oh_my_kanban.commands.github_stub.subprocess.run",
                return_value=self._mock_run("issue #1\n"),
            ),
        ):
            result = runner.invoke(cli, ["github", "issue", "list", "--repo", "owner/repo"])
            assert result.exit_code == 0

    def test_issue_view_command(self) -> None:
        """omk github issue view 명령이 정상 실행되어야 한다."""
        runner = CliRunner()
        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch(
                "oh_my_kanban.commands.github_stub.subprocess.run",
                return_value=self._mock_run("Title: Fix bug\n"),
            ),
        ):
            result = runner.invoke(cli, ["github", "issue", "view", "42", "--repo", "owner/repo"])
            assert result.exit_code == 0

    def test_issue_view_non_positive_number_fails(self) -> None:
        """0 이하의 이슈 번호는 에러가 발생해야 한다."""
        runner = CliRunner()
        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
        ):
            result = runner.invoke(cli, ["github", "issue", "view", "0"])
            assert result.exit_code != 0

    def test_pr_list_command(self) -> None:
        """omk github pr list 명령이 정상 실행되어야 한다."""
        runner = CliRunner()
        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch(
                "oh_my_kanban.commands.github_stub.subprocess.run",
                return_value=self._mock_run("PR #1\n"),
            ),
        ):
            result = runner.invoke(cli, ["github", "pr", "list", "--repo", "owner/repo"])
            assert result.exit_code == 0

    def test_gh_alias_works(self) -> None:
        """omk gh (alias)가 정상 동작해야 한다."""
        runner = CliRunner()
        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch(
                "oh_my_kanban.commands.github_stub.subprocess.run",
                return_value=self._mock_run("PR #1\n"),
            ),
        ):
            result = runner.invoke(cli, ["gh", "pr", "list"])
            assert result.exit_code == 0

    def test_gh_not_installed_error_message(self) -> None:
        """gh가 설치되지 않았을 때 안내 메시지가 나와야 한다."""
        runner = CliRunner()
        with patch("oh_my_kanban.commands.github_stub.shutil.which", return_value=None):
            result = runner.invoke(cli, ["github", "issue", "list"])
            assert result.exit_code != 0
            assert "cli.github.com" in result.output

    def test_issue_create_command(self) -> None:
        """omk github issue create 명령이 정상 실행되어야 한다."""
        runner = CliRunner()
        with (
            patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"),
            patch(
                "oh_my_kanban.commands.github_stub.subprocess.run",
                return_value=self._mock_run("https://github.com/owner/repo/issues/1\n"),
            ),
        ):
            result = runner.invoke(
                cli,
                ["github", "issue", "create", "--repo", "owner/repo", "--title", "Bug fix"],
            )
            assert result.exit_code == 0

    def test_invalid_repo_format_fails(self) -> None:
        """잘못된 레포지토리 형식은 에러가 발생해야 한다."""
        runner = CliRunner()
        with patch("oh_my_kanban.commands.github_stub.shutil.which", return_value="/usr/bin/gh"):
            result = runner.invoke(cli, ["github", "issue", "list", "--repo", "../malicious/repo"])
            assert result.exit_code != 0
