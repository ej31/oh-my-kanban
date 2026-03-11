"""config 커맨드 독립성 및 구조 테스트."""

from oh_my_kanban.cli import cli


def test_config_help_shows_subcommands(runner):
    """omk config --help는 init, show, set, profile 서브커맨드를 보여야 한다."""
    result = runner.invoke(cli, ["config", "--help"])

    assert result.exit_code == 0
    assert "init" in result.output
    assert "show" in result.output
    assert "set" in result.output
    assert "profile" in result.output


def test_config_is_top_level_command(runner):
    """config는 최상위(top-level) 커맨드여야 한다."""
    result = runner.invoke(cli, ["config", "--help"])

    assert result.exit_code == 0


def test_config_accessible_without_provider_prefix(runner):
    """omk config는 provider prefix 없이 직접 접근 가능해야 한다."""
    result = runner.invoke(cli, ["config", "--help"])

    assert result.exit_code == 0
    # provider 하위가 아닌 최상위에서 접근 가능
    assert result.output.strip()


def test_config_profile_help_shows_subcommands(runner):
    """omk config profile --help는 list, use 서브커맨드를 보여야 한다."""
    result = runner.invoke(cli, ["config", "profile", "--help"])

    assert result.exit_code == 0
    assert "list" in result.output
    assert "use" in result.output


def test_config_is_not_subcommand_of_plane(runner):
    """omk plane config는 실패해야 한다 (config는 plane 하위 커맨드가 아님)."""
    result = runner.invoke(cli, ["plane", "config", "--help"])

    # plane 하위에 config가 없으므로 에러 종료여야 함
    assert result.exit_code != 0


def test_config_is_not_subcommand_of_pl_alias(runner):
    """omk pl config도 실패해야 한다 (pl은 plane의 alias이며 config를 포함하지 않음)."""
    result = runner.invoke(cli, ["pl", "config", "--help"])

    # pl(plane) 하위에 config가 없으므로 에러 종료여야 함
    assert result.exit_code != 0


def test_config_init_help(runner):
    """omk config init --help는 정상 동작해야 한다."""
    result = runner.invoke(cli, ["config", "init", "--help"])

    assert result.exit_code == 0
    assert "init" in result.output


def test_config_show_help(runner):
    """omk config show --help는 정상 동작해야 한다."""
    result = runner.invoke(cli, ["config", "show", "--help"])

    assert result.exit_code == 0
    assert "show" in result.output


def test_config_set_help(runner):
    """omk config set --help는 정상 동작해야 한다."""
    result = runner.invoke(cli, ["config", "set", "--help"])

    assert result.exit_code == 0
    assert "set" in result.output


def test_config_profile_list_help(runner):
    """omk config profile list --help는 정상 동작해야 한다."""
    result = runner.invoke(cli, ["config", "profile", "list", "--help"])

    assert result.exit_code == 0


def test_config_profile_use_help(runner):
    """omk config profile use --help는 정상 동작해야 한다."""
    result = runner.invoke(cli, ["config", "profile", "use", "--help"])

    assert result.exit_code == 0
