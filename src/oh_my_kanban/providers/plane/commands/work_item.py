"""작업 항목(Work Item) 관련 커맨드."""

from __future__ import annotations

import click
from datetime import date

from oh_my_kanban.providers.plane.context import PlaneContext as CliContext
from oh_my_kanban.providers.plane.errors import handle_api_error
from oh_my_kanban.output import click_echo_err, format_output, format_pagination_hint
from oh_my_kanban.utils import confirm_delete, fetch_all_pages, parse_work_item_ref

# ---------------------------------------------------------------------------
# 출력 컬럼 상수
# ---------------------------------------------------------------------------

# 목록 출력 컬럼
_LIST_COLUMNS = ["id", "name", "priority", "state", "assignees"]

# 상세 출력 컬럼
_DETAIL_COLUMNS = [
    "id",
    "name",
    "priority",
    "state",
    "assignees",
    "labels",
    "start_date",
    "target_date",
]

# 우선순위 선택지
_PRIORITY_CHOICES = click.Choice(["urgent", "high", "medium", "low", "none"])

# 관계 유형 선택지
_RELATION_TYPE_CHOICES = click.Choice(
    [
        "blocking",
        "blocked_by",
        "duplicate",
        "relates_to",
        "start_before",
        "start_after",
        "finish_before",
        "finish_after",
    ]
)


def _validate_date(ctx: click.Context, param: click.Parameter, value: str | None) -> str | None:
    """날짜 형식(YYYY-MM-DD)을 CLI 경계에서 검증한다.

    date.fromisoformat()을 사용해 zero-padding 없는 입력(2026-3-6 등)을 거부한다.
    """
    if value is None:
        return None
    try:
        date.fromisoformat(value)
        return value
    except ValueError:
        raise click.BadParameter(f"날짜 형식은 YYYY-MM-DD여야 합니다: {value}")


# ---------------------------------------------------------------------------
# work-item 그룹
# ---------------------------------------------------------------------------


@click.group("work-item")
def work_item() -> None:
    """작업 항목 관리."""
    pass


# ---------------------------------------------------------------------------
# 기본 CRUD + search
# ---------------------------------------------------------------------------


@work_item.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지 당 항목 수.")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회.")
@click.option("--cursor", default=None, help="페이지네이션 커서.")
@click.option("--order-by", default=None, help="정렬 기준 필드.")
@click.option("--priority", type=_PRIORITY_CHOICES, default=None, help="우선순위 필터.")
@click.pass_obj
@handle_api_error
def work_item_list(
    ctx: CliContext,
    per_page: int,
    fetch_all: bool,
    cursor: str | None,
    order_by: str | None,
    priority: str | None,
) -> None:
    """작업 항목 목록을 조회한다."""
    from plane.models.query_params import WorkItemQueryParams

    project_id = ctx.require_project()

    # 쿼리 파라미터 구성 (None 값은 제외)
    params_kwargs: dict = {"per_page": per_page}
    if cursor:
        params_kwargs["cursor"] = cursor
    if order_by:
        params_kwargs["order_by"] = order_by
    if priority:
        params_kwargs["priority"] = priority

    params = WorkItemQueryParams(**params_kwargs)

    if fetch_all:
        # 모든 페이지 자동 순회
        results = fetch_all_pages(
            ctx.client.work_items.list,
            ctx.workspace,
            project_id,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_LIST_COLUMNS)
    else:
        response = ctx.client.work_items.list(ctx.workspace, project_id, params=params)
        format_output(response.results, ctx.output, columns=_LIST_COLUMNS)
        format_pagination_hint(response, ctx.output)


@work_item.command("get")
@click.argument("ref")
@click.pass_obj
@handle_api_error
def work_item_get(ctx: CliContext, ref: str) -> None:
    """작업 항목 상세 정보를 조회한다.

    REF는 UUID 또는 'PROJECT-123' 형식을 모두 지원한다.
    """
    parsed = parse_work_item_ref(ref)
    if parsed:
        # PROJECT-123 형식
        proj_id, issue_num = parsed
        result = ctx.client.work_items.retrieve_by_identifier(
            workspace_slug=ctx.workspace,
            project_identifier=proj_id,
            issue_identifier=issue_num,
        )
    else:
        # UUID 형식
        project_id = ctx.require_project()
        result = ctx.client.work_items.retrieve(ctx.workspace, project_id, ref)

    format_output(result, ctx.output, columns=_DETAIL_COLUMNS)


@work_item.command("create")
@click.option("--name", required=True, help="작업 항목 이름.")
@click.option("--priority", type=_PRIORITY_CHOICES, default=None, help="우선순위.")
@click.option("--state", "state_id", default=None, help="상태 UUID.")
@click.option("--assignee", "assignees", multiple=True, help="담당자 UUID (여러 번 지정 가능).")
@click.option("--label", "labels", multiple=True, help="레이블 UUID (여러 번 지정 가능).")
@click.option("--parent", default=None, help="부모 작업 항목 UUID.")
@click.option("--start-date", default=None, callback=_validate_date, help="시작 날짜 (YYYY-MM-DD).")
@click.option("--target-date", default=None, callback=_validate_date, help="목표 날짜 (YYYY-MM-DD).")
@click.option("--description", default=None, help="설명 (평문, <p> 태그로 자동 래핑).")
@click.option("--point", type=int, default=None, help="스토리 포인트.")
@click.pass_obj
@handle_api_error
def work_item_create(
    ctx: CliContext,
    name: str,
    priority: str | None,
    state_id: str | None,
    assignees: tuple[str, ...],
    labels: tuple[str, ...],
    parent: str | None,
    start_date: str | None,
    target_date: str | None,
    description: str | None,
    point: int | None,
) -> None:
    """새 작업 항목을 생성한다."""
    from plane.models.work_items import CreateWorkItem

    project_id = ctx.require_project()

    # 평문 설명을 HTML로 래핑
    description_html = f"<p>{description}</p>" if description else None

    data = CreateWorkItem(
        name=name,
        priority=priority,
        state=state_id,
        assignees=list(assignees) if assignees else None,
        labels=list(labels) if labels else None,
        parent=parent,
        start_date=start_date,
        target_date=target_date,
        description_html=description_html,
        point=point,
    )

    result = ctx.client.work_items.create(ctx.workspace, project_id, data=data)
    format_output(result, ctx.output, columns=_DETAIL_COLUMNS)


@work_item.command("update")
@click.argument("work_item_id")
@click.option("--name", default=None, help="새 이름.")
@click.option("--priority", type=_PRIORITY_CHOICES, default=None, help="우선순위.")
@click.option("--state", "state_id", default=None, help="상태 UUID.")
@click.option("--assignee", "assignees", multiple=True, help="담당자 UUID (여러 번 지정 가능).")
@click.option("--label", "labels", multiple=True, help="레이블 UUID (여러 번 지정 가능).")
@click.option("--parent", default=None, help="부모 작업 항목 UUID.")
@click.option("--start-date", default=None, callback=_validate_date, help="시작 날짜 (YYYY-MM-DD).")
@click.option("--target-date", default=None, callback=_validate_date, help="목표 날짜 (YYYY-MM-DD).")
@click.option("--description", default=None, help="설명 (평문, <p> 태그로 자동 래핑).")
@click.option("--point", type=int, default=None, help="스토리 포인트.")
@click.pass_obj
@handle_api_error
def work_item_update(
    ctx: CliContext,
    work_item_id: str,
    name: str | None,
    priority: str | None,
    state_id: str | None,
    assignees: tuple[str, ...],
    labels: tuple[str, ...],
    parent: str | None,
    start_date: str | None,
    target_date: str | None,
    description: str | None,
    point: int | None,
) -> None:
    """기존 작업 항목을 수정한다."""
    from plane.models.work_items import UpdateWorkItem

    project_id = ctx.require_project()

    description_html = f"<p>{description}</p>" if description else None

    data = UpdateWorkItem(
        name=name,
        priority=priority,
        state=state_id,
        assignees=list(assignees) if assignees else None,
        labels=list(labels) if labels else None,
        parent=parent,
        start_date=start_date,
        target_date=target_date,
        description_html=description_html,
        point=point,
    )

    result = ctx.client.work_items.update(ctx.workspace, project_id, work_item_id, data=data)
    format_output(result, ctx.output, columns=_DETAIL_COLUMNS)


@work_item.command("delete")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def work_item_delete(ctx: CliContext, work_item_id: str) -> None:
    """작업 항목을 삭제한다."""
    project_id = ctx.require_project()

    if not confirm_delete("작업 항목", work_item_id):
        raise click.Abort()

    ctx.client.work_items.delete(ctx.workspace, project_id, work_item_id)
    click.echo(f"작업 항목 '{work_item_id}' 삭제 완료.")


@work_item.command("search")
@click.option("--query", required=True, help="검색어.")
@click.pass_obj
@handle_api_error
def work_item_search(ctx: CliContext, query: str) -> None:
    """작업 항목을 검색한다."""
    result = ctx.client.work_items.search(workspace_slug=ctx.workspace, query=query)
    # WorkItemSearch.issues 리스트 출력
    format_output(
        result.issues,
        ctx.output,
        columns=["id", "name", "sequence_id", "project__identifier"],
    )


# ---------------------------------------------------------------------------
# comment 서브그룹
# ---------------------------------------------------------------------------


@work_item.group("comment")
def comment() -> None:
    """댓글 관리."""
    pass


@comment.command("list")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def comment_list(ctx: CliContext, work_item_id: str) -> None:
    """작업 항목의 댓글 목록을 조회한다."""
    project_id = ctx.require_project()
    response = ctx.client.work_items.comments.list(ctx.workspace, project_id, work_item_id)
    format_output(
        response.results,
        ctx.output,
        columns=["id", "comment_stripped", "created_by", "created_at"],
    )
    format_pagination_hint(response, ctx.output)


@comment.command("get")
@click.argument("work_item_id")
@click.argument("comment_id")
@click.pass_obj
@handle_api_error
def comment_get(ctx: CliContext, work_item_id: str, comment_id: str) -> None:
    """특정 댓글을 조회한다."""
    project_id = ctx.require_project()
    result = ctx.client.work_items.comments.retrieve(
        ctx.workspace, project_id, work_item_id, comment_id
    )
    format_output(result, ctx.output)


@comment.command("create")
@click.argument("work_item_id")
@click.option("--body", required=True, help="댓글 내용 (평문).")
@click.pass_obj
@handle_api_error
def comment_create(ctx: CliContext, work_item_id: str, body: str) -> None:
    """댓글을 생성한다."""
    from plane.models.work_items import CreateWorkItemComment

    project_id = ctx.require_project()
    data = CreateWorkItemComment(comment_html=f"<p>{body}</p>")
    result = ctx.client.work_items.comments.create(
        ctx.workspace, project_id, work_item_id, data=data
    )
    format_output(result, ctx.output)


@comment.command("update")
@click.argument("work_item_id")
@click.argument("comment_id")
@click.option("--body", required=True, help="수정할 댓글 내용 (평문).")
@click.pass_obj
@handle_api_error
def comment_update(ctx: CliContext, work_item_id: str, comment_id: str, body: str) -> None:
    """댓글을 수정한다."""
    from plane.models.work_items import UpdateWorkItemComment

    project_id = ctx.require_project()
    data = UpdateWorkItemComment(comment_html=f"<p>{body}</p>")
    result = ctx.client.work_items.comments.update(
        ctx.workspace, project_id, work_item_id, comment_id, data=data
    )
    format_output(result, ctx.output)


@comment.command("delete")
@click.argument("work_item_id")
@click.argument("comment_id")
@click.pass_obj
@handle_api_error
def comment_delete(ctx: CliContext, work_item_id: str, comment_id: str) -> None:
    """댓글을 삭제한다."""
    project_id = ctx.require_project()

    if not confirm_delete("댓글", comment_id):
        raise click.Abort()

    ctx.client.work_items.comments.delete(ctx.workspace, project_id, work_item_id, comment_id)
    click.echo(f"댓글 '{comment_id}' 삭제 완료.")


# ---------------------------------------------------------------------------
# link 서브그룹
# ---------------------------------------------------------------------------


@work_item.group("link")
def link() -> None:
    """링크 관리."""
    pass


@link.command("list")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def link_list(ctx: CliContext, work_item_id: str) -> None:
    """작업 항목의 링크 목록을 조회한다."""
    project_id = ctx.require_project()
    response = ctx.client.work_items.links.list(ctx.workspace, project_id, work_item_id)
    format_output(response.results, ctx.output, columns=["id", "title", "url", "created_by"])
    format_pagination_hint(response, ctx.output)


@link.command("get")
@click.argument("work_item_id")
@click.argument("link_id")
@click.pass_obj
@handle_api_error
def link_get(ctx: CliContext, work_item_id: str, link_id: str) -> None:
    """특정 링크를 조회한다."""
    project_id = ctx.require_project()
    result = ctx.client.work_items.links.retrieve(ctx.workspace, project_id, work_item_id, link_id)
    format_output(result, ctx.output)


@link.command("create")
@click.argument("work_item_id")
@click.option("--url", required=True, help="링크 URL.")
@click.pass_obj
@handle_api_error
def link_create(ctx: CliContext, work_item_id: str, url: str) -> None:
    """링크를 추가한다.

    \b
    참고: SDK가 title 필드를 지원하지 않아 URL만 저장됩니다.
    """
    from plane.models.work_items import CreateWorkItemLink

    project_id = ctx.require_project()
    data = CreateWorkItemLink(url=url)
    result = ctx.client.work_items.links.create(ctx.workspace, project_id, work_item_id, data=data)
    format_output(result, ctx.output)


@link.command("update")
@click.argument("work_item_id")
@click.argument("link_id")
@click.option("--url", default=None, help="새 URL.")
@click.pass_obj
@handle_api_error
def link_update(ctx: CliContext, work_item_id: str, link_id: str, url: str | None) -> None:
    """링크를 수정한다."""
    from plane.models.work_items import UpdateWorkItemLink

    project_id = ctx.require_project()
    data = UpdateWorkItemLink(url=url)
    result = ctx.client.work_items.links.update(
        ctx.workspace, project_id, work_item_id, link_id, data=data
    )
    format_output(result, ctx.output)


@link.command("delete")
@click.argument("work_item_id")
@click.argument("link_id")
@click.pass_obj
@handle_api_error
def link_delete(ctx: CliContext, work_item_id: str, link_id: str) -> None:
    """링크를 삭제한다."""
    project_id = ctx.require_project()

    if not confirm_delete("링크", link_id):
        raise click.Abort()

    ctx.client.work_items.links.delete(ctx.workspace, project_id, work_item_id, link_id)
    click.echo(f"링크 '{link_id}' 삭제 완료.")


# ---------------------------------------------------------------------------
# relation 서브그룹
# ---------------------------------------------------------------------------


@work_item.group("relation")
def relation() -> None:
    """관계 관리."""
    pass


@relation.command("list")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def relation_list(ctx: CliContext, work_item_id: str) -> None:
    """작업 항목의 관계 목록을 조회한다.

    blocking, blocked_by, duplicate, relates_to 등 유형별로 출력한다.
    """
    project_id = ctx.require_project()
    result = ctx.client.work_items.relations.list(ctx.workspace, project_id, work_item_id)

    # WorkItemRelationResponse는 유형별 ID 목록을 담은 dict 구조
    if ctx.output == "json":
        import json
        import sys

        data = result.model_dump(exclude_none=True) if hasattr(result, "model_dump") else vars(result)
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        # 테이블/plain: 유형 + ID 목록 형태로 출력
        rows = []
        relation_data = (
            result.model_dump() if hasattr(result, "model_dump") else vars(result)
        )
        for rel_type, ids in relation_data.items():
            if ids:
                for item_id in ids:
                    rows.append({"relation_type": rel_type, "related_work_item_id": item_id})
        if rows:
            format_output(rows, ctx.output, columns=["relation_type", "related_work_item_id"])
        else:
            click_echo_err("관계 없음")


@relation.command("create")
@click.argument("work_item_id")
@click.option("--related-work-item", "related_work_item", required=True, help="관련 작업 항목 UUID.")
@click.option(
    "--relation-type",
    "relation_type",
    required=True,
    type=_RELATION_TYPE_CHOICES,
    help="관계 유형.",
)
@click.pass_obj
@handle_api_error
def relation_create(
    ctx: CliContext, work_item_id: str, related_work_item: str, relation_type: str
) -> None:
    """작업 항목 간 관계를 생성한다."""
    from plane.models.work_items import CreateWorkItemRelation

    project_id = ctx.require_project()
    data = CreateWorkItemRelation(relation_type=relation_type, issues=[related_work_item])
    ctx.client.work_items.relations.create(ctx.workspace, project_id, work_item_id, data=data)
    click.echo(f"관계 생성 완료: {work_item_id} --[{relation_type}]--> {related_work_item}")


@relation.command("delete")
@click.argument("work_item_id")
@click.option("--related-work-item", "related_work_item", required=True, help="제거할 관련 작업 항목 UUID.")
@click.pass_obj
@handle_api_error
def relation_delete(ctx: CliContext, work_item_id: str, related_work_item: str) -> None:
    """작업 항목 관계를 제거한다."""
    from plane.models.work_items import RemoveWorkItemRelation

    project_id = ctx.require_project()

    if not confirm_delete("관계 (related_issue)", related_work_item):
        raise click.Abort()

    data = RemoveWorkItemRelation(related_issue=related_work_item)
    ctx.client.work_items.relations.delete(ctx.workspace, project_id, work_item_id, data=data)
    click.echo(f"관계 '{related_work_item}' 제거 완료.")


# ---------------------------------------------------------------------------
# activity 서브그룹 (읽기 전용)
# ---------------------------------------------------------------------------


@work_item.group("activity")
def activity() -> None:
    """활동 내역 조회 (읽기 전용)."""
    pass


@activity.command("list")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def activity_list(ctx: CliContext, work_item_id: str) -> None:
    """작업 항목의 활동 내역 목록을 조회한다."""
    project_id = ctx.require_project()
    response = ctx.client.work_items.activities.list(ctx.workspace, project_id, work_item_id)
    format_output(
        response.results,
        ctx.output,
        columns=["id", "verb", "field", "old_value", "new_value", "actor", "created_at"],
    )
    format_pagination_hint(response, ctx.output)


@activity.command("get")
@click.argument("work_item_id")
@click.argument("activity_id")
@click.pass_obj
@handle_api_error
def activity_get(ctx: CliContext, work_item_id: str, activity_id: str) -> None:
    """특정 활동 내역을 조회한다."""
    project_id = ctx.require_project()
    result = ctx.client.work_items.activities.retrieve(
        ctx.workspace, project_id, work_item_id, activity_id
    )
    format_output(result, ctx.output)


# ---------------------------------------------------------------------------
# attachment 서브그룹
# ---------------------------------------------------------------------------


@work_item.group("attachment")
def attachment() -> None:
    """첨부파일 관리."""
    pass


@attachment.command("list")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def attachment_list(ctx: CliContext, work_item_id: str) -> None:
    """작업 항목의 첨부파일 목록을 조회한다."""
    project_id = ctx.require_project()
    results = ctx.client.work_items.attachments.list(ctx.workspace, project_id, work_item_id)
    format_output(results, ctx.output, columns=["id", "asset", "size", "created_by", "created_at"])


@attachment.command("get")
@click.argument("work_item_id")
@click.argument("attachment_id")
@click.pass_obj
@handle_api_error
def attachment_get(ctx: CliContext, work_item_id: str, attachment_id: str) -> None:
    """특정 첨부파일을 조회한다."""
    project_id = ctx.require_project()
    result = ctx.client.work_items.attachments.retrieve(
        ctx.workspace, project_id, work_item_id, attachment_id
    )
    format_output(result, ctx.output)


@attachment.command("create")
@click.argument("work_item_id")
@click.option("--name", required=True, help="파일 이름.")
@click.option("--size", required=True, type=int, help="파일 크기 (바이트).")
@click.option("--mime-type", "mime_type", default=None, help="MIME 타입 (예: image/png).")
@click.pass_obj
@handle_api_error
def attachment_create(
    ctx: CliContext,
    work_item_id: str,
    name: str,
    size: int,
    mime_type: str | None,
) -> None:
    """첨부파일 업로드 요청을 생성한다.

    실제 파일 업로드는 반환된 upload URL을 통해 별도로 수행해야 한다.
    """
    from plane.models.work_items import WorkItemAttachmentUploadRequest

    project_id = ctx.require_project()
    data = WorkItemAttachmentUploadRequest(name=name, size=size, type=mime_type)
    result = ctx.client.work_items.attachments.create(
        ctx.workspace, project_id, work_item_id, data=data
    )
    format_output(result, ctx.output)


@attachment.command("delete")
@click.argument("work_item_id")
@click.argument("attachment_id")
@click.pass_obj
@handle_api_error
def attachment_delete(ctx: CliContext, work_item_id: str, attachment_id: str) -> None:
    """첨부파일을 삭제한다."""
    project_id = ctx.require_project()

    if not confirm_delete("첨부파일", attachment_id):
        raise click.Abort()

    ctx.client.work_items.attachments.delete(ctx.workspace, project_id, work_item_id, attachment_id)
    click.echo(f"첨부파일 '{attachment_id}' 삭제 완료.")


# ---------------------------------------------------------------------------
# worklog 서브그룹
# ---------------------------------------------------------------------------


@work_item.group("worklog")
def worklog() -> None:
    """작업 로그 관리."""
    pass


@worklog.command("list")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def worklog_list(ctx: CliContext, work_item_id: str) -> None:
    """작업 항목의 작업 로그 목록을 조회한다."""
    project_id = ctx.require_project()
    results = ctx.client.work_items.work_logs.list(ctx.workspace, project_id, work_item_id)
    format_output(
        results,
        ctx.output,
        columns=["id", "duration", "description", "logged_by", "created_at"],
    )


@worklog.command("create")
@click.argument("work_item_id")
@click.option("--duration", required=True, type=int, help="작업 시간 (분).")
@click.option("--description", default=None, help="작업 내용 설명.")
@click.pass_obj
@handle_api_error
def worklog_create(
    ctx: CliContext,
    work_item_id: str,
    duration: int,
    description: str | None,
) -> None:
    """작업 로그를 기록한다."""
    from plane.models.work_items import CreateWorkItemWorkLog

    project_id = ctx.require_project()
    data = CreateWorkItemWorkLog(duration=duration, description=description)
    result = ctx.client.work_items.work_logs.create(
        ctx.workspace, project_id, work_item_id, data.model_dump(exclude_none=True)
    )
    format_output(result, ctx.output)


@worklog.command("update")
@click.argument("work_item_id")
@click.argument("worklog_id")
@click.option("--duration", type=int, default=None, help="새 작업 시간 (분).")
@click.option("--description", default=None, help="새 작업 내용 설명.")
@click.pass_obj
@handle_api_error
def worklog_update(
    ctx: CliContext,
    work_item_id: str,
    worklog_id: str,
    duration: int | None,
    description: str | None,
) -> None:
    """작업 로그를 수정한다."""
    from plane.models.work_items import UpdateWorkItemWorkLog

    project_id = ctx.require_project()
    data = UpdateWorkItemWorkLog(duration=duration, description=description)
    result = ctx.client.work_items.work_logs.update(
        ctx.workspace, project_id, work_item_id, worklog_id, data.model_dump(exclude_none=True)
    )
    format_output(result, ctx.output)


@worklog.command("delete")
@click.argument("work_item_id")
@click.argument("worklog_id")
@click.pass_obj
@handle_api_error
def worklog_delete(ctx: CliContext, work_item_id: str, worklog_id: str) -> None:
    """작업 로그를 삭제한다."""
    project_id = ctx.require_project()

    if not confirm_delete("작업 로그", worklog_id):
        raise click.Abort()

    ctx.client.work_items.work_logs.delete(ctx.workspace, project_id, work_item_id, worklog_id)
    click.echo(f"작업 로그 '{worklog_id}' 삭제 완료.")
