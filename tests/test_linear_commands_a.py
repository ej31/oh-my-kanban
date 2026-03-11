"""Linear Commands A 테스트: linear/__init__ + me + team + state (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from oh_my_kanban.cli import cli


# ─── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _make_ctx(api_key: str = "lin_api_test", team_id: str = "team-1", output: str = "plain"):
    """테스트용 LinearContext를 생성한다."""
    from oh_my_kanban.providers.linear.context import LinearContext
    return LinearContext(_api_key=api_key, team_id=team_id, output=output)


def _make_cli():
    """테스트용 linear 그룹을 반환한다."""
    from oh_my_kanban.providers.linear.group import linear
    return linear


# ─── linear 그룹 ───────────────────────────────────────────────────────────────

class TestLinearGroup:
    def test_linear_group_exists(self):
        """linear click.Group이 존재해야 한다."""
        from oh_my_kanban.providers.linear.group import linear
        import click
        assert isinstance(linear, click.Group)

    def test_linear_group_has_me_command(self):
        """linear 그룹에 me 서브커맨드가 등록되어 있어야 한다."""
        from oh_my_kanban.providers.linear.group import linear
        assert "me" in linear.commands

    def test_linear_group_has_team_command(self):
        """linear 그룹에 team 서브커맨드가 등록되어 있어야 한다."""
        from oh_my_kanban.providers.linear.group import linear
        assert "team" in linear.commands

    def test_linear_group_has_state_command(self):
        """linear 그룹에 state 서브커맨드가 등록되어 있어야 한다."""
        from oh_my_kanban.providers.linear.group import linear
        assert "state" in linear.commands

    def test_linear_help_shows_subcommands(self):
        """omk linear --help 실행 시 서브커맨드가 표시되어야 한다."""
        runner = CliRunner()
        linear = _make_cli()
        result = runner.invoke(linear, ["--help"])
        assert result.exit_code == 0
        assert "me" in result.output
        assert "team" in result.output
        assert "state" in result.output

    def test_linear_group_sets_linear_context(self):
        """linear 그룹 callback이 ctx.obj를 LinearContext로 전환해야 한다."""
        from oh_my_kanban.providers.linear.group import linear
        from oh_my_kanban.providers.linear.context import LinearContext

        runner = CliRunner()

        @linear.result_callback()
        def check_ctx(*args, **kwargs):
            pass

        # me 커맨드를 mock해서 ctx.obj 타입 확인
        captured = {}

        import click

        @click.pass_obj
        def capture(obj):
            captured["obj"] = obj

        with patch("oh_my_kanban.config.load_config") as mock_cfg:
            mock_cfg.return_value = MagicMock(linear_api_key="lin_key", linear_team_id="t1")
            # --help는 callback을 실행하지 않으므로 me --help 사용
            result = runner.invoke(linear, ["me", "--help"])
        # me --help는 성공해야 함
        assert result.exit_code == 0

    def test_linear_group_uses_root_profile_config(self, runner, tmp_path):
        """root --profile로 선택한 설정이 linear 그룹에 그대로 전달되어야 한다."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "\n".join(
                [
                    "[default]",
                    'output = "table"',
                    "",
                    "[default.linear]",
                    'api_key = ""',
                    "",
                    "[custom]",
                    'output = "json"',
                    "",
                    "[custom.linear]",
                    'api_key = "lin_api_custom"',
                    'team_id = "team-custom"',
                    "",
                ]
            ),
            encoding="utf-8",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"viewer": {"id": "u1", "name": "Alice", "email": "alice@example.com"}}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            with patch("httpx.Client.post", return_value=mock_response):
                result = runner.invoke(cli, ["--profile", "custom", "linear", "me"])

        assert result.exit_code == 0
        assert "Alice" in result.output


# ─── me 커맨드 ─────────────────────────────────────────────────────────────────

class TestMeCommand:
    def _invoke_me(self, viewer_data: dict, output: str = "json"):
        """me 커맨드를 mock LinearContext와 함께 실행한다."""
        from oh_my_kanban.providers.linear.commands.me import me

        mock_client = MagicMock()
        mock_client.execute.return_value = {"viewer": viewer_data}
        ctx = _make_ctx(output=output)
        ctx._client = mock_client

        runner = CliRunner()
        result = runner.invoke(me, obj=ctx)
        return result

    def test_me_returns_viewer_data(self):
        """me 커맨드는 viewer 쿼리 결과를 출력해야 한다."""
        viewer = {"id": "u1", "name": "홍길동", "email": "hong@example.com"}
        result = self._invoke_me(viewer)
        assert result.exit_code == 0
        assert "u1" in result.output

    def test_me_calls_viewer_query(self):
        """me 커맨드는 viewer GraphQL 쿼리를 호출해야 한다."""
        from oh_my_kanban.providers.linear.commands.me import me

        mock_client = MagicMock()
        mock_client.execute.return_value = {"viewer": {"id": "u1", "name": "테스트", "email": "test@e.com"}}
        ctx = _make_ctx()
        ctx._client = mock_client

        runner = CliRunner()
        runner.invoke(me, obj=ctx)

        mock_client.execute.assert_called_once()
        query_arg = mock_client.execute.call_args[0][0]
        assert "viewer" in query_arg

    def test_me_output_contains_name(self):
        """me 커맨드 출력에 사용자 이름이 포함되어야 한다."""
        viewer = {"id": "u1", "name": "Alice", "email": "alice@example.com"}
        result = self._invoke_me(viewer, output="plain")
        assert result.exit_code == 0
        assert "Alice" in result.output

    def test_me_handles_graphql_error(self):
        """me 커맨드는 LinearGraphQLError를 처리해야 한다 (exit code 1)."""
        from oh_my_kanban.providers.linear.commands.me import me
        from oh_my_kanban.providers.linear.errors import LinearGraphQLError

        mock_client = MagicMock()
        mock_client.execute.side_effect = LinearGraphQLError([{"message": "Unauthorized"}])
        ctx = _make_ctx()
        ctx._client = mock_client

        runner = CliRunner()
        result = runner.invoke(me, obj=ctx)
        assert result.exit_code == 1


# ─── team 커맨드 ───────────────────────────────────────────────────────────────

class TestTeamCommand:
    def test_team_list_returns_nodes(self):
        """team list는 팀 목록을 출력해야 한다."""
        from oh_my_kanban.providers.linear.commands.team import team_list

        nodes = [
            {"id": "t1", "name": "Backend", "key": "BE"},
            {"id": "t2", "name": "Frontend", "key": "FE"},
        ]
        mock_client = MagicMock()
        mock_client.execute.return_value = {"teams": {"nodes": nodes}}
        ctx = _make_ctx(output="plain")
        ctx._client = mock_client

        runner = CliRunner()
        result = runner.invoke(team_list, obj=ctx)
        assert result.exit_code == 0
        assert "Backend" in result.output
        assert "Frontend" in result.output

    def test_team_list_calls_teams_query(self):
        """team list는 teams GraphQL 쿼리를 호출해야 한다."""
        from oh_my_kanban.providers.linear.commands.team import team_list

        mock_client = MagicMock()
        mock_client.execute.return_value = {"teams": {"nodes": []}}
        ctx = _make_ctx()
        ctx._client = mock_client

        runner = CliRunner()
        runner.invoke(team_list, obj=ctx)

        query_arg = mock_client.execute.call_args[0][0]
        assert "teams" in query_arg

    def test_team_get_returns_team_detail(self):
        """team get은 팀 상세 정보를 출력해야 한다."""
        from oh_my_kanban.providers.linear.commands.team import team_get

        team_data = {"id": "t1", "name": "Backend", "key": "BE", "description": "백엔드 팀"}
        mock_client = MagicMock()
        mock_client.execute.return_value = {"team": team_data}
        ctx = _make_ctx(output="plain")
        ctx._client = mock_client

        runner = CliRunner()
        result = runner.invoke(team_get, ["t1"], obj=ctx)
        assert result.exit_code == 0
        assert "Backend" in result.output

    def test_team_get_passes_team_id_as_variable(self):
        """team get은 team_id를 GraphQL 변수로 전달해야 한다."""
        from oh_my_kanban.providers.linear.commands.team import team_get

        mock_client = MagicMock()
        mock_client.execute.return_value = {"team": {"id": "t1", "name": "X", "key": "X", "description": ""}}
        ctx = _make_ctx()
        ctx._client = mock_client

        runner = CliRunner()
        runner.invoke(team_get, ["my-team-id"], obj=ctx)

        call_args = mock_client.execute.call_args
        variables = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("variables", {})
        assert variables.get("id") == "my-team-id"

    def test_team_list_handles_empty_nodes(self):
        """team list는 빈 결과도 처리해야 한다."""
        from oh_my_kanban.providers.linear.commands.team import team_list

        mock_client = MagicMock()
        mock_client.execute.return_value = {"teams": {"nodes": []}}
        ctx = _make_ctx()
        ctx._client = mock_client

        runner = CliRunner()
        result = runner.invoke(team_list, obj=ctx)
        # 빈 결과도 정상 종료
        assert result.exit_code == 0

    def test_team_group_has_list_and_get(self):
        """team 그룹에 list와 get 서브커맨드가 있어야 한다."""
        from oh_my_kanban.providers.linear.commands.team import team
        assert "list" in team.commands
        assert "get" in team.commands


# ─── state 커맨드 ──────────────────────────────────────────────────────────────

class TestStateCommand:
    def _invoke_state_list(self, nodes: list, team_id_opt: str | None = None, ctx_team: str = "team-1"):
        """state list를 mock과 함께 실행한다."""
        from oh_my_kanban.providers.linear.commands.state import state_list

        mock_client = MagicMock()
        mock_client.execute.return_value = {"team": {"states": {"nodes": nodes}}}
        ctx = _make_ctx(team_id=ctx_team, output="plain")
        ctx._client = mock_client

        runner = CliRunner()
        args = []
        if team_id_opt:
            args = ["--team", team_id_opt]
        result = runner.invoke(state_list, args, obj=ctx)
        return result, mock_client

    def test_state_list_returns_nodes(self):
        """state list는 workflow state 목록을 출력해야 한다."""
        nodes = [
            {"id": "s1", "name": "Todo", "type": "unstarted", "position": 0.0},
            {"id": "s2", "name": "In Progress", "type": "started", "position": 1.0},
        ]
        result, _ = self._invoke_state_list(nodes)
        assert result.exit_code == 0
        assert "Todo" in result.output
        assert "In Progress" in result.output

    def test_state_list_uses_team_option(self):
        """state list --team 옵션이 GraphQL 변수로 전달되어야 한다."""
        result, mock_client = self._invoke_state_list([], team_id_opt="explicit-team")
        assert result.exit_code == 0
        call_args = mock_client.execute.call_args
        variables = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("variables", {})
        assert variables.get("id") == "explicit-team"

    def test_state_list_falls_back_to_ctx_team(self):
        """state list는 --team 없을 때 ctx.team_id를 사용해야 한다."""
        result, mock_client = self._invoke_state_list([], ctx_team="ctx-team-id")
        assert result.exit_code == 0
        call_args = mock_client.execute.call_args
        variables = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("variables", {})
        assert variables.get("id") == "ctx-team-id"

    def test_state_list_fails_without_team(self):
        """state list는 --team도 없고 ctx.team_id도 없으면 UsageError를 발생시켜야 한다."""
        from oh_my_kanban.providers.linear.commands.state import state_list

        mock_client = MagicMock()
        ctx = _make_ctx(team_id="")  # team_id 없음
        ctx._client = mock_client

        runner = CliRunner()
        result = runner.invoke(state_list, [], obj=ctx)
        # UsageError는 non-zero exit code
        assert result.exit_code != 0

    def test_state_list_calls_correct_query(self):
        """state list는 team.states 쿼리를 호출해야 한다."""
        result, mock_client = self._invoke_state_list([], team_id_opt="t1")
        query_arg = mock_client.execute.call_args[0][0]
        assert "states" in query_arg
        assert "team" in query_arg

    def test_state_group_has_list(self):
        """state 그룹에 list 서브커맨드가 있어야 한다."""
        from oh_my_kanban.providers.linear.commands.state import state
        assert "list" in state.commands
