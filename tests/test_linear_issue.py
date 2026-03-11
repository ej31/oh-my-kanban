"""Linear issue CRUD + comment 서브그룹 커맨드 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


def _make_ctx(api_key: str = "lin_api_test", team_id: str = "team-1", output: str = "json"):
    """테스트용 LinearContext를 생성한다."""
    from oh_my_kanban.linear_context import LinearContext
    return LinearContext(_api_key=api_key, team_id=team_id, output=output)


def _invoke(cmd, args: list, obj=None, input: str | None = None):
    """Click 커맨드를 CliRunner로 실행하고 Result를 반환한다."""
    runner = CliRunner()
    ctx_obj = obj if obj is not None else _make_ctx()
    return runner.invoke(cmd, args, obj=ctx_obj, catch_exceptions=False, input=input)


# ─── issue list ───────────────────────────────────────────────────────────────

def test_issue_list_calls_paginate_relay():
    """issue list는 paginate_relay를 호출해 이슈 목록을 반환해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_list

    nodes = [{"id": "i1", "identifier": "ENG-1", "title": "첫 번째 이슈", "priority": 2}]
    ctx = _make_ctx()
    with patch.object(ctx.client, "paginate_relay", return_value=nodes) as mock_pr:
        result = _invoke(issue_list, [], obj=ctx)
    assert result.exit_code == 0
    mock_pr.assert_called_once()


def test_issue_list_with_team_filter():
    """issue list --team TEAM_ID는 variables에 filter를 포함해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_list

    ctx = _make_ctx()
    captured_vars = {}

    def fake_paginate(query, variables, path, **kwargs):
        captured_vars.update(variables)
        return []

    with patch.object(ctx.client, "paginate_relay", side_effect=fake_paginate):
        result = _invoke(issue_list, ["--team", "team-abc"], obj=ctx)

    assert result.exit_code == 0
    assert "filter" in captured_vars
    assert captured_vars["filter"]["team"]["id"]["eq"] == "team-abc"


def test_issue_list_with_first_option():
    """issue list --first N은 variables에 first=N을 포함해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_list

    ctx = _make_ctx()
    captured_vars = {}

    def fake_paginate(query, variables, path, **kwargs):
        captured_vars.update(variables)
        return []

    with patch.object(ctx.client, "paginate_relay", side_effect=fake_paginate):
        result = _invoke(issue_list, ["--first", "10"], obj=ctx)

    assert result.exit_code == 0
    assert captured_vars["first"] == 10


# ─── issue get ────────────────────────────────────────────────────────────────

def test_issue_get_by_uuid():
    """issue get <UUID>는 execute를 호출해 이슈 상세를 반환해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_get

    ctx = _make_ctx()
    issue_data = {"id": "uuid-123", "identifier": "ENG-1", "title": "테스트"}
    with patch.object(ctx.client, "execute", return_value={"issue": issue_data}):
        result = _invoke(issue_get, ["uuid-123"], obj=ctx)

    assert result.exit_code == 0


def test_issue_get_by_key_format():
    """issue get KEY-123 형식도 execute에 그대로 전달해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_get

    ctx = _make_ctx()
    issue_data = {"id": "uuid-abc", "identifier": "ENG-42", "title": "키 형식 테스트"}
    captured = {}

    def fake_execute(query, variables):
        captured.update(variables)
        return {"issue": issue_data}

    with patch.object(ctx.client, "execute", side_effect=fake_execute):
        result = _invoke(issue_get, ["ENG-42"], obj=ctx)

    assert result.exit_code == 0
    assert captured["id"] == "ENG-42"


# ─── issue create ─────────────────────────────────────────────────────────────

def test_issue_create_success():
    """issue create --title --team은 issueCreate mutation을 실행해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_create

    ctx = _make_ctx()
    new_issue = {"id": "new-id", "identifier": "ENG-5", "title": "신규 이슈"}
    with patch.object(ctx.client, "execute", return_value={"issueCreate": {"success": True, "issue": new_issue}}):
        result = _invoke(issue_create, ["--title", "신규 이슈", "--team", "team-1"], obj=ctx)

    assert result.exit_code == 0


def test_issue_create_with_all_options():
    """issue create는 선택적 옵션(description, priority, state, assignee)을 input에 포함해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_create

    ctx = _make_ctx()
    captured = {}

    def fake_execute(query, variables):
        captured.update(variables.get("input", {}))
        return {"issueCreate": {"success": True, "issue": {"id": "x", "identifier": "ENG-6", "title": "풀옵션"}}}

    with patch.object(ctx.client, "execute", side_effect=fake_execute):
        result = _invoke(
            issue_create,
            ["--title", "풀옵션", "--team", "t1", "--description", "설명", "--priority", "2",
             "--state", "s-id", "--assignee", "u-id"],
            obj=ctx,
        )

    assert result.exit_code == 0
    assert captured["description"] == "설명"
    assert captured["priority"] == 2
    assert captured["stateId"] == "s-id"
    assert captured["assigneeId"] == "u-id"


def test_issue_create_failure_raises_usage_error():
    """issueCreate success=False이면 UsageError를 발생시켜야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_create

    ctx = _make_ctx()
    with patch.object(ctx.client, "execute", return_value={"issueCreate": {"success": False}}):
        runner = CliRunner()
        result = runner.invoke(
            issue_create,
            ["--title", "실패", "--team", "t1"],
            obj=ctx,
            catch_exceptions=True,
        )
    # UsageError는 exit_code 2
    assert result.exit_code != 0


# ─── issue update ─────────────────────────────────────────────────────────────

def test_issue_update_success():
    """issue update <ID> --priority 3은 issueUpdate mutation을 실행해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_update

    ctx = _make_ctx()
    updated = {"id": "i1", "identifier": "ENG-1", "title": "업데이트됨"}
    with patch.object(ctx.client, "execute", return_value={"issueUpdate": {"success": True, "issue": updated}}):
        result = _invoke(issue_update, ["i1", "--priority", "3"], obj=ctx)

    assert result.exit_code == 0


def test_issue_update_empty_input_raises_error():
    """수정 옵션 없이 issue update 호출 시 UsageError가 발생해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_update

    ctx = _make_ctx()
    runner = CliRunner()
    result = runner.invoke(issue_update, ["i1"], obj=ctx, catch_exceptions=True)
    assert result.exit_code != 0


def test_issue_update_failure_raises_usage_error():
    """issueUpdate success=False이면 UsageError를 발생시켜야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_update

    ctx = _make_ctx()
    with patch.object(ctx.client, "execute", return_value={"issueUpdate": {"success": False}}):
        runner = CliRunner()
        result = runner.invoke(issue_update, ["i1", "--title", "실패"], obj=ctx, catch_exceptions=True)
    assert result.exit_code != 0


# ─── issue delete ─────────────────────────────────────────────────────────────

def test_issue_delete_confirmed():
    """issue delete는 confirm_delete=True이면 issueDelete mutation을 실행해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_delete

    ctx = _make_ctx()
    with patch("oh_my_kanban.commands.linear.issue.confirm_delete", return_value=True), \
         patch.object(ctx.client, "execute", return_value={"issueDelete": {"success": True}}):
        result = _invoke(issue_delete, ["i1"], obj=ctx)

    assert result.exit_code == 0
    assert "i1" in result.output


def test_issue_delete_aborted():
    """issue delete는 confirm_delete=False이면 Abort하여 삭제하지 않아야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_delete

    ctx = _make_ctx()
    with patch("oh_my_kanban.commands.linear.issue.confirm_delete", return_value=False):
        runner = CliRunner()
        result = runner.invoke(issue_delete, ["i1"], obj=ctx, catch_exceptions=True)

    # click.Abort은 exit_code 1
    assert result.exit_code != 0


def test_issue_delete_failure_raises_usage_error():
    """issueDelete success=False이면 UsageError를 발생시켜야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_delete

    ctx = _make_ctx()
    with patch("oh_my_kanban.commands.linear.issue.confirm_delete", return_value=True), \
         patch.object(ctx.client, "execute", return_value={"issueDelete": {"success": False}}):
        runner = CliRunner()
        result = runner.invoke(issue_delete, ["i1"], obj=ctx, catch_exceptions=True)

    assert result.exit_code != 0


# ─── comment list ─────────────────────────────────────────────────────────────

def test_comment_list_returns_nodes():
    """comment list <ISSUE_ID>는 이슈의 댓글 목록을 반환해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_comment

    ctx = _make_ctx()
    nodes = [{"id": "c1", "body": "첫 댓글", "createdAt": "2024-01-01"}]
    data = {"issue": {"comments": {"nodes": nodes}}}
    with patch.object(ctx.client, "execute", return_value=data):
        runner = CliRunner()
        result = runner.invoke(issue_comment, ["list", "i1"], obj=ctx, catch_exceptions=False)

    assert result.exit_code == 0


def test_comment_list_empty():
    """comment list는 댓글이 없으면 빈 결과를 출력해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_comment

    ctx = _make_ctx()
    data = {"issue": {"comments": {"nodes": []}}}
    with patch.object(ctx.client, "execute", return_value=data):
        runner = CliRunner()
        result = runner.invoke(issue_comment, ["list", "i1"], obj=ctx, catch_exceptions=False)

    assert result.exit_code == 0


# ─── comment create ───────────────────────────────────────────────────────────

def test_comment_create_success():
    """comment create <ISSUE_ID> --body BODY는 commentCreate mutation을 실행해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_comment

    ctx = _make_ctx()
    comment = {"id": "c-new", "body": "새 댓글", "createdAt": "2024-01-01"}
    with patch.object(ctx.client, "execute", return_value={"commentCreate": {"success": True, "comment": comment}}):
        runner = CliRunner()
        result = runner.invoke(
            issue_comment, ["create", "i1", "--body", "새 댓글"], obj=ctx, catch_exceptions=False
        )

    assert result.exit_code == 0


def test_comment_create_sends_correct_input():
    """comment create는 issueId와 body를 input에 담아 전달해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_comment

    ctx = _make_ctx()
    captured = {}

    def fake_execute(query, variables):
        captured.update(variables.get("input", {}))
        return {"commentCreate": {"success": True, "comment": {"id": "c2", "body": "hi", "createdAt": "2024-01-01"}}}

    with patch.object(ctx.client, "execute", side_effect=fake_execute):
        runner = CliRunner()
        runner.invoke(issue_comment, ["create", "issue-abc", "--body", "hi"], obj=ctx, catch_exceptions=False)

    assert captured["issueId"] == "issue-abc"
    assert captured["body"] == "hi"


def test_comment_create_failure_raises_error():
    """commentCreate success=False이면 UsageError가 발생해야 한다."""
    from oh_my_kanban.commands.linear.issue import issue_comment

    ctx = _make_ctx()
    with patch.object(ctx.client, "execute", return_value={"commentCreate": {"success": False}}):
        runner = CliRunner()
        result = runner.invoke(
            issue_comment, ["create", "i1", "--body", "실패"], obj=ctx, catch_exceptions=True
        )

    assert result.exit_code != 0
