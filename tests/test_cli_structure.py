"""CLI 커맨드 구조 테스트."""

from oh_my_kanban.cli import cli


def extract_top_level_commands(help_output: str) -> list[str]:
    """--help 출력에서 최상위 커맨드 목록을 파싱한다."""
    commands: list[str] = []
    in_commands_section = False
    for line in help_output.splitlines():
        if "Commands:" in line:
            in_commands_section = True
            continue
        if in_commands_section:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                cmd_name = stripped.split()[0] if stripped.split() else ""
                if cmd_name:
                    commands.append(cmd_name)
    return commands


# ---------------------------------------------------------------------------
# 최상위 커맨드 구조
# ---------------------------------------------------------------------------


def test_top_level_shows_plane_subgroup(runner):
    """최상위 --help에 plane 서브그룹이 보여야 한다."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "plane" in result.output


def test_top_level_shows_github_subgroup(runner):
    """최상위 --help에 github 서브그룹이 보여야 한다."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "github" in result.output


def test_top_level_shows_config_subgroup(runner):
    """최상위 --help에 config 서브그룹이 보여야 한다."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "config" in result.output


def test_top_level_does_not_show_work_item_directly(runner):
    """최상위 --help에 work-item이 직접 노출되면 안 된다. plane 하위에 있어야 한다."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    top_level_commands = extract_top_level_commands(result.output)
    assert "work-item" not in top_level_commands


def test_top_level_does_not_show_cycle_directly(runner):
    """최상위 --help에 cycle이 직접 노출되면 안 된다."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    top_level_commands = extract_top_level_commands(result.output)
    assert "cycle" not in top_level_commands


# ---------------------------------------------------------------------------
# plane 서브그룹 커맨드 구조
# ---------------------------------------------------------------------------


def test_plane_subgroup_shows_work_item(runner):
    """omk plane --help에 work-item 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "work-item" in result.output


def test_plane_subgroup_shows_cycle(runner):
    """omk plane --help에 cycle 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "cycle" in result.output


def test_plane_subgroup_shows_module(runner):
    """omk plane --help에 module 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "module" in result.output


def test_plane_subgroup_shows_milestone(runner):
    """omk plane --help에 milestone 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "milestone" in result.output


def test_plane_subgroup_shows_epic(runner):
    """omk plane --help에 epic 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "epic" in result.output


def test_plane_subgroup_shows_page(runner):
    """omk plane --help에 page 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "page" in result.output


def test_plane_subgroup_shows_intake(runner):
    """omk plane --help에 intake 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "intake" in result.output


def test_plane_subgroup_shows_initiative(runner):
    """omk plane --help에 initiative 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "initiative" in result.output


def test_plane_subgroup_shows_teamspace(runner):
    """omk plane --help에 teamspace 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "teamspace" in result.output


def test_plane_subgroup_shows_state(runner):
    """omk plane --help에 state 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "state" in result.output


def test_plane_subgroup_shows_label(runner):
    """omk plane --help에 label 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "label" in result.output


def test_plane_subgroup_shows_user(runner):
    """omk plane --help에 user 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "user" in result.output


def test_plane_subgroup_shows_workspace(runner):
    """omk plane --help에 workspace 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "workspace" in result.output


def test_plane_subgroup_shows_customer(runner):
    """omk plane --help에 customer 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "customer" in result.output


def test_plane_subgroup_shows_work_item_type(runner):
    """omk plane --help에 work-item-type 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "work-item-type" in result.output


def test_plane_subgroup_shows_work_item_property(runner):
    """omk plane --help에 work-item-property 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "--help"])
    assert result.exit_code == 0
    assert "work-item-property" in result.output


# ---------------------------------------------------------------------------
# work-item 서브커맨드 구조
# ---------------------------------------------------------------------------


def test_work_item_shows_list(runner):
    """omk plane work-item --help에 list 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "work-item", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output


def test_work_item_shows_get(runner):
    """omk plane work-item --help에 get 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "work-item", "--help"])
    assert result.exit_code == 0
    assert "get" in result.output


def test_work_item_shows_create(runner):
    """omk plane work-item --help에 create 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "work-item", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output


def test_work_item_shows_update(runner):
    """omk plane work-item --help에 update 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "work-item", "--help"])
    assert result.exit_code == 0
    assert "update" in result.output


def test_work_item_shows_delete(runner):
    """omk plane work-item --help에 delete 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "work-item", "--help"])
    assert result.exit_code == 0
    assert "delete" in result.output


def test_work_item_shows_search(runner):
    """omk plane work-item --help에 search 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "work-item", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output


def test_work_item_shows_relation(runner):
    """omk plane work-item --help에 relation 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["plane", "work-item", "--help"])
    assert result.exit_code == 0
    assert "relation" in result.output


# ---------------------------------------------------------------------------
# github 서브그룹
# ---------------------------------------------------------------------------


def test_github_subgroup_exits_ok(runner):
    """omk github --help가 에러 없이 종료되어야 한다."""
    result = runner.invoke(cli, ["github", "--help"])
    assert result.exit_code == 0


def test_github_alias_gh_exits_ok(runner):
    """omk gh --help (github의 alias)가 에러 없이 종료되어야 한다."""
    result = runner.invoke(cli, ["gh", "--help"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# config 서브그룹 커맨드 구조
# ---------------------------------------------------------------------------


def test_config_shows_init(runner):
    """omk config --help에 init 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["config", "--help"])
    assert result.exit_code == 0
    assert "init" in result.output


def test_config_shows_show(runner):
    """omk config --help에 show 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["config", "--help"])
    assert result.exit_code == 0
    assert "show" in result.output


def test_config_shows_set(runner):
    """omk config --help에 set 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["config", "--help"])
    assert result.exit_code == 0
    assert "set" in result.output


def test_config_shows_profile(runner):
    """omk config --help에 profile 서브커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["config", "--help"])
    assert result.exit_code == 0
    assert "profile" in result.output


# ---------------------------------------------------------------------------
# plane alias (pl)
# ---------------------------------------------------------------------------


def test_plane_alias_pl_shows_work_item(runner):
    """omk pl --help (plane의 alias)에 work-item 커맨드가 보여야 한다."""
    result = runner.invoke(cli, ["pl", "--help"])
    assert result.exit_code == 0
    assert "work-item" in result.output


def test_plane_alias_pl_exits_ok(runner):
    """omk pl --help가 에러 없이 종료되어야 한다."""
    result = runner.invoke(cli, ["pl", "--help"])
    assert result.exit_code == 0
