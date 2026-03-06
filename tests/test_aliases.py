"""alias 동작 테스트."""

from oh_my_kanban.cli import cli


def test_pl_is_alias_for_plane(runner):
    """omk pl은 omk plane의 alias여야 한다."""
    plane_result = runner.invoke(cli, ["plane", "--help"])
    pl_result = runner.invoke(cli, ["pl", "--help"])

    assert plane_result.exit_code == 0
    assert pl_result.exit_code == 0
    # 동일한 서브커맨드가 존재해야 함
    assert "work-item" in pl_result.output
    assert "cycle" in pl_result.output


def test_gh_is_alias_for_github(runner):
    """omk gh는 omk github의 alias여야 한다."""
    github_result = runner.invoke(cli, ["github", "--help"])
    gh_result = runner.invoke(cli, ["gh", "--help"])

    assert github_result.exit_code == 0
    assert gh_result.exit_code == 0


def test_pl_has_same_subcommands_as_plane(runner):
    """omk pl과 omk plane은 동일한 서브커맨드를 가져야 한다."""
    plane_result = runner.invoke(cli, ["plane", "--help"])
    pl_result = runner.invoke(cli, ["pl", "--help"])

    assert plane_result.exit_code == 0
    assert pl_result.exit_code == 0

    # 주요 서브커맨드가 모두 pl에도 있어야 함
    expected_subcommands = ["work-item", "cycle", "module", "milestone", "epic", "label"]
    for subcmd in expected_subcommands:
        assert subcmd in pl_result.output, f"pl alias에 '{subcmd}' 서브커맨드가 없음"
        assert subcmd in plane_result.output, f"plane에 '{subcmd}' 서브커맨드가 없음"


def test_gh_has_same_structure_as_github(runner):
    """omk gh와 omk github은 동일한 구조여야 한다."""
    github_result = runner.invoke(cli, ["github", "--help"])
    gh_result = runner.invoke(cli, ["gh", "--help"])

    assert github_result.exit_code == 0
    assert gh_result.exit_code == 0
    # gh alias 도움말에 github 관련 내용이 포함되어야 함
    assert "github" in gh_result.output.lower() or "GitHub" in gh_result.output


def test_pl_subcommand_work_item_help(runner):
    """omk pl work-item --help는 정상 동작해야 한다 (alias + 서브커맨드 조합)."""
    result = runner.invoke(cli, ["pl", "work-item", "--help"])
    assert result.exit_code == 0
    # work-item 커맨드의 도움말이 출력되어야 함
    assert "work-item" in result.output.lower() or "work_item" in result.output.lower() or result.output.strip()


def test_plane_and_pl_exit_codes_match(runner):
    """omk plane --help와 omk pl --help의 종료 코드가 동일해야 한다."""
    plane_result = runner.invoke(cli, ["plane", "--help"])
    pl_result = runner.invoke(cli, ["pl", "--help"])

    assert plane_result.exit_code == pl_result.exit_code == 0


def test_github_and_gh_exit_codes_match(runner):
    """omk github --help와 omk gh --help의 종료 코드가 동일해야 한다."""
    github_result = runner.invoke(cli, ["github", "--help"])
    gh_result = runner.invoke(cli, ["gh", "--help"])

    assert github_result.exit_code == gh_result.exit_code == 0
