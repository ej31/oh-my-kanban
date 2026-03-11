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


def test_pl_subcommand_work_item_help(runner):
    """omk pl work-item --help는 정상 동작해야 한다 (alias + 서브커맨드 조합)."""
    result = runner.invoke(cli, ["pl", "work-item", "--help"])
    assert result.exit_code == 0
    # work-item 커맨드의 도움말이 출력되어야 함
    output_lower = result.output.lower()
    assert "work-item" in output_lower or "work_item" in output_lower
    assert "usage" in output_lower or "options" in output_lower or "commands" in output_lower


def test_plane_and_pl_exit_codes_match(runner):
    """omk plane --help와 omk pl --help의 종료 코드가 동일해야 한다."""
    plane_result = runner.invoke(cli, ["plane", "--help"])
    pl_result = runner.invoke(cli, ["pl", "--help"])

    assert plane_result.exit_code == pl_result.exit_code == 0
