"""Linear 이슈 관리 커맨드."""
from __future__ import annotations

import click

from oh_my_kanban.providers.linear.context import LinearContext
from oh_my_kanban.providers.linear.errors import handle_linear_error
from oh_my_kanban.output import format_output
from oh_my_kanban.utils import confirm_delete

# ─── GraphQL 쿼리/뮤테이션 상수 ──────────────────────────────────────────────

_ISSUES_QUERY = """
query GetIssues($first: Int, $after: String, $filter: IssueFilter) {
  issues(first: $first, after: $after, filter: $filter) {
    nodes { id identifier title priority state { name } assignee { name } }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_ISSUE_QUERY = """
query GetIssue($id: String!) {
  issue(id: $id) {
    id identifier title description priority
    state { name } assignee { name } createdAt updatedAt
  }
}
"""

_ISSUE_CREATE_MUTATION = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue { id identifier title priority state { name } }
  }
}
"""

_ISSUE_UPDATE_MUTATION = """
mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue { id identifier title priority state { name } assignee { name } }
  }
}
"""

_ISSUE_DELETE_MUTATION = """
mutation IssueDelete($id: String!) {
  issueDelete(id: $id) { success }
}
"""

_COMMENTS_QUERY = """
query GetComments($id: String!) {
  issue(id: $id) {
    comments { nodes { id body createdAt user { name } } }
  }
}
"""

_COMMENT_CREATE_MUTATION = """
mutation CommentCreate($input: CommentCreateInput!) {
  commentCreate(input: $input) {
    success
    comment { id body createdAt }
  }
}
"""


# ─── issue 그룹 ───────────────────────────────────────────────────────────────

@click.group()
def issue() -> None:
    """Linear 이슈 관리."""
    pass


@issue.command("list")
@click.option("--team", "team_id", default=None, help="팀 ID로 필터링")
@click.option("--first", default=50, show_default=True, help="페이지당 결과 수")
@click.pass_obj
@handle_linear_error
def issue_list(ctx: LinearContext, team_id: str | None, first: int) -> None:
    """이슈 목록을 조회한다."""
    variables: dict = {"first": first}
    if team_id:
        variables["filter"] = {"team": {"id": {"eq": team_id}}}
    results = ctx.client.paginate_relay(_ISSUES_QUERY, variables, path="issues")
    format_output(results, ctx.output, columns=["id", "identifier", "title", "priority"])


@issue.command("get")
@click.argument("ref")
@click.pass_obj
@handle_linear_error
def issue_get(ctx: LinearContext, ref: str) -> None:
    """이슈 상세 정보를 조회한다. REF는 UUID 또는 KEY-123 형식."""
    data = ctx.client.execute(_ISSUE_QUERY, {"id": ref})
    format_output(data.get("issue", {}), ctx.output)


@issue.command("create")
@click.option("--title", required=True, help="이슈 제목")
@click.option("--team", "team_id", required=True, help="팀 ID")
@click.option("--description", default=None, help="이슈 설명")
@click.option("--priority", type=click.IntRange(0, 4), default=None, help="우선순위 (0=없음, 1=긴급, 2=높음, 3=중간, 4=낮음)")
@click.option("--state", "state_id", default=None, help="상태 ID")
@click.option("--assignee", "assignee_id", default=None, help="담당자 사용자 ID")
@click.pass_obj
@handle_linear_error
def issue_create(
    ctx: LinearContext,
    title: str,
    team_id: str,
    description: str | None,
    priority: int | None,
    state_id: str | None,
    assignee_id: str | None,
) -> None:
    """새 이슈를 생성한다."""
    input_data: dict = {"title": title, "teamId": team_id}
    if description:
        input_data["description"] = description
    if priority is not None:
        input_data["priority"] = priority
    if state_id:
        input_data["stateId"] = state_id
    if assignee_id:
        input_data["assigneeId"] = assignee_id

    data = ctx.client.execute(_ISSUE_CREATE_MUTATION, {"input": input_data})
    result = data.get("issueCreate", {})
    if not result.get("success"):
        raise click.UsageError("이슈 생성에 실패했습니다.")
    format_output(result.get("issue", {}), ctx.output)


@issue.command("update")
@click.argument("issue_id")
@click.option("--title", default=None, help="이슈 제목")
@click.option("--priority", type=click.IntRange(0, 4), default=None, help="우선순위")
@click.option("--state", "state_id", default=None, help="상태 ID")
@click.option("--assignee", "assignee_id", default=None, help="담당자 사용자 ID")
@click.option("--description", default=None, help="이슈 설명")
@click.pass_obj
@handle_linear_error
def issue_update(
    ctx: LinearContext,
    issue_id: str,
    title: str | None,
    priority: int | None,
    state_id: str | None,
    assignee_id: str | None,
    description: str | None,
) -> None:
    """이슈 정보를 수정한다."""
    input_data: dict = {}
    if title:
        input_data["title"] = title
    if priority is not None:
        input_data["priority"] = priority
    if state_id:
        input_data["stateId"] = state_id
    if assignee_id:
        input_data["assigneeId"] = assignee_id
    if description:
        input_data["description"] = description

    if not input_data:
        raise click.UsageError("수정할 내용을 하나 이상 지정하세요.")

    data = ctx.client.execute(_ISSUE_UPDATE_MUTATION, {"id": issue_id, "input": input_data})
    result = data.get("issueUpdate", {})
    if not result.get("success"):
        raise click.UsageError("이슈 수정에 실패했습니다.")
    format_output(result.get("issue", {}), ctx.output)


@issue.command("delete")
@click.argument("issue_id")
@click.pass_obj
@handle_linear_error
def issue_delete(ctx: LinearContext, issue_id: str) -> None:
    """이슈를 삭제한다."""
    if not confirm_delete("이슈", issue_id):
        raise click.Abort()
    data = ctx.client.execute(_ISSUE_DELETE_MUTATION, {"id": issue_id})
    if not data.get("issueDelete", {}).get("success"):
        raise click.UsageError("이슈 삭제에 실패했습니다.")
    click.echo(f"이슈 '{issue_id}'을(를) 삭제했습니다.")


# ─── comment 서브그룹 ─────────────────────────────────────────────────────────

@issue.group("comment")
def issue_comment() -> None:
    """이슈 댓글 관리."""
    pass


@issue_comment.command("list")
@click.argument("issue_id")
@click.pass_obj
@handle_linear_error
def comment_list(ctx: LinearContext, issue_id: str) -> None:
    """이슈의 댓글 목록을 조회한다."""
    data = ctx.client.execute(_COMMENTS_QUERY, {"id": issue_id})
    nodes = data.get("issue", {}).get("comments", {}).get("nodes", [])
    format_output(nodes, ctx.output, columns=["id", "body", "createdAt"])


@issue_comment.command("create")
@click.argument("issue_id")
@click.option("--body", required=True, help="댓글 내용")
@click.pass_obj
@handle_linear_error
def comment_create(ctx: LinearContext, issue_id: str, body: str) -> None:
    """이슈에 댓글을 추가한다."""
    data = ctx.client.execute(
        _COMMENT_CREATE_MUTATION,
        {"input": {"issueId": issue_id, "body": body}},
    )
    result = data.get("commentCreate", {})
    if not result.get("success"):
        raise click.UsageError("댓글 생성에 실패했습니다.")
    format_output(result.get("comment", {}), ctx.output)
