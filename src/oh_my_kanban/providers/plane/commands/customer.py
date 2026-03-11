"""고객(Customer) 관련 커맨드."""

from __future__ import annotations

import click
from plane.models.customers import CreateCustomer, CustomerRequest, UpdateCustomer, UpdateCustomerRequest

from oh_my_kanban.providers.plane.context import PlaneContext as CliContext
from oh_my_kanban.providers.plane.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint
from oh_my_kanban.utils import confirm_delete, fetch_all_pages

# 고객 출력 컬럼
_COLUMNS = ["id", "name", "email", "domain", "stage", "contract_status"]

# 고객 속성 출력 컬럼
_PROPERTY_COLUMNS = ["id", "name", "display_name", "property_type", "is_required", "is_active"]

# 고객 요청 출력 컬럼
_REQUEST_COLUMNS = ["id", "name", "link"]


@click.group()
def customer() -> None:
    """고객 관리 (워크스페이스 수준)."""
    pass


@customer.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def customer_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """고객 목록 조회."""
    ws = ctx.workspace

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.customers.list,
            ws,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_COLUMNS)
    else:
        response = ctx.client.customers.list(ws, params={"per_page": per_page})
        format_output(response.results, ctx.output, columns=_COLUMNS)
        format_pagination_hint(response, ctx.output)


@customer.command("get")
@click.argument("customer_id")
@click.pass_obj
@handle_api_error
def customer_get(ctx: CliContext, customer_id: str) -> None:
    """고객 상세 조회."""
    result = ctx.client.customers.retrieve(ctx.workspace, customer_id)
    format_output(result, ctx.output, columns=_COLUMNS)


@customer.command("create")
@click.option("--name", required=True, help="고객 이름")
@click.option("--email", default=None, help="이메일")
@click.option("--website-url", default=None, help="웹사이트 URL")
@click.option("--domain", default=None, help="도메인")
@click.option("--employees", type=int, default=None, help="직원 수")
@click.option("--stage", default=None, help="단계")
@click.option("--contract-status", default=None, help="계약 상태")
@click.option("--revenue", default=None, help="매출")
@click.pass_obj
@handle_api_error
def customer_create(
    ctx: CliContext,
    name: str,
    email: str | None,
    website_url: str | None,
    domain: str | None,
    employees: int | None,
    stage: str | None,
    contract_status: str | None,
    revenue: str | None,
) -> None:
    """새 고객 생성."""
    data = CreateCustomer(
        name=name,
        email=email,
        website_url=website_url,
        domain=domain,
        employees=employees,
        stage=stage,
        contract_status=contract_status,
        revenue=revenue,
    )
    result = ctx.client.customers.create(ctx.workspace, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@customer.command("update")
@click.argument("customer_id")
@click.option("--name", default=None, help="고객 이름")
@click.option("--email", default=None, help="이메일")
@click.option("--website-url", default=None, help="웹사이트 URL")
@click.option("--domain", default=None, help="도메인")
@click.option("--employees", type=int, default=None, help="직원 수")
@click.option("--stage", default=None, help="단계")
@click.option("--contract-status", default=None, help="계약 상태")
@click.option("--revenue", default=None, help="매출")
@click.pass_obj
@handle_api_error
def customer_update(
    ctx: CliContext,
    customer_id: str,
    name: str | None,
    email: str | None,
    website_url: str | None,
    domain: str | None,
    employees: int | None,
    stage: str | None,
    contract_status: str | None,
    revenue: str | None,
) -> None:
    """고객 수정."""
    data = UpdateCustomer(
        name=name,
        email=email,
        website_url=website_url,
        domain=domain,
        employees=employees,
        stage=stage,
        contract_status=contract_status,
        revenue=revenue,
    )
    result = ctx.client.customers.update(ctx.workspace, customer_id, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@customer.command("delete")
@click.argument("customer_id")
@click.pass_obj
@handle_api_error
def customer_delete(ctx: CliContext, customer_id: str) -> None:
    """고객 삭제."""
    if not confirm_delete("고객", customer_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.customers.delete(ctx.workspace, customer_id)
    click.echo(f"고객 '{customer_id}'을(를) 삭제했습니다.")


# ── 속성 서브그룹 ─────────────────────────────────────────────────────────

@customer.group("property")
def customer_property() -> None:
    """고객 속성 관리."""
    pass


@customer_property.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def customer_property_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """고객 속성 목록 조회."""
    ws = ctx.workspace

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.customers.properties.list,
            ws,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_PROPERTY_COLUMNS)
    else:
        response = ctx.client.customers.properties.list(ws, params={"per_page": per_page})
        format_output(response.results, ctx.output, columns=_PROPERTY_COLUMNS)
        format_pagination_hint(response, ctx.output)


@customer_property.command("get")
@click.argument("property_id")
@click.pass_obj
@handle_api_error
def customer_property_get(ctx: CliContext, property_id: str) -> None:
    """고객 속성 상세 조회."""
    result = ctx.client.customers.properties.retrieve(ctx.workspace, property_id)
    format_output(result, ctx.output, columns=_PROPERTY_COLUMNS)


@customer_property.command("create")
@click.option("--name", required=True, help="속성 내부 이름")
@click.option("--display-name", required=True, help="속성 표시 이름")
@click.option(
    "--property-type",
    required=True,
    type=click.Choice(
        ["text", "number", "checkbox", "select", "multi_select", "date", "member", "url", "email", "file"],
        case_sensitive=False,
    ),
    help="속성 타입",
)
@click.option("--description", default=None, help="설명")
@click.option("--is-required", is_flag=True, default=False, help="필수 여부")
@click.option("--is-active", is_flag=True, default=True, help="활성화 여부")
@click.pass_obj
@handle_api_error
def customer_property_create(
    ctx: CliContext,
    name: str,
    display_name: str,
    property_type: str,
    description: str | None,
    is_required: bool,
    is_active: bool,
) -> None:
    """새 고객 속성 생성."""
    from plane.models.customers import CreateCustomerProperty
    from plane.models.enums import PropertyType

    data = CreateCustomerProperty(
        name=name,
        display_name=display_name,
        property_type=PropertyType(property_type.lower()),
        description=description,
        is_required=is_required,
        is_active=is_active,
    )
    result = ctx.client.customers.properties.create(ctx.workspace, data)
    format_output(result, ctx.output, columns=_PROPERTY_COLUMNS)


@customer_property.command("update")
@click.argument("property_id")
@click.option("--display-name", default=None, help="속성 표시 이름")
@click.option("--description", default=None, help="설명")
@click.option("--is-required", default=None, type=bool, help="필수 여부")
@click.option("--is-active", default=None, type=bool, help="활성화 여부")
@click.pass_obj
@handle_api_error
def customer_property_update(
    ctx: CliContext,
    property_id: str,
    display_name: str | None,
    description: str | None,
    is_required: bool | None,
    is_active: bool | None,
) -> None:
    """고객 속성 수정."""
    from plane.models.customers import UpdateCustomerProperty

    data = UpdateCustomerProperty(
        display_name=display_name,
        description=description,
        is_required=is_required,
        is_active=is_active,
    )
    result = ctx.client.customers.properties.update(ctx.workspace, property_id, data)
    format_output(result, ctx.output, columns=_PROPERTY_COLUMNS)


@customer_property.command("delete")
@click.argument("property_id")
@click.pass_obj
@handle_api_error
def customer_property_delete(ctx: CliContext, property_id: str) -> None:
    """고객 속성 삭제."""
    if not confirm_delete("고객 속성", property_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.customers.properties.delete(ctx.workspace, property_id)
    click.echo(f"고객 속성 '{property_id}'을(를) 삭제했습니다.")


# ── 요청 서브그룹 ─────────────────────────────────────────────────────────

@customer.group("request")
def customer_request() -> None:
    """고객 요청 관리."""
    pass


@customer_request.command("list")
@click.argument("customer_id")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.pass_obj
@handle_api_error
def customer_request_list(ctx: CliContext, customer_id: str, per_page: int) -> None:
    """고객 요청 목록 조회."""
    results = ctx.client.customers.requests.list(
        ctx.workspace, customer_id, params={"per_page": per_page}
    )
    format_output(results, ctx.output, columns=_REQUEST_COLUMNS)


@customer_request.command("get")
@click.argument("customer_id")
@click.argument("request_id")
@click.pass_obj
@handle_api_error
def customer_request_get(ctx: CliContext, customer_id: str, request_id: str) -> None:
    """고객 요청 상세 조회."""
    result = ctx.client.customers.requests.retrieve(ctx.workspace, customer_id, request_id)
    format_output(result, ctx.output, columns=_REQUEST_COLUMNS)


@customer_request.command("create")
@click.argument("customer_id")
@click.option("--name", required=True, help="요청 이름")
@click.option("--description", default=None, help="설명")
@click.option("--link", default=None, help="관련 링크 URL")
@click.pass_obj
@handle_api_error
def customer_request_create(
    ctx: CliContext,
    customer_id: str,
    name: str,
    description: str | None,
    link: str | None,
) -> None:
    """새 고객 요청 생성."""
    data = CustomerRequest(
        name=name,
        description=description,
        link=link,
    )
    result = ctx.client.customers.requests.create(ctx.workspace, customer_id, data)
    format_output(result, ctx.output, columns=_REQUEST_COLUMNS)


@customer_request.command("update")
@click.argument("customer_id")
@click.argument("request_id")
@click.option("--name", default=None, help="요청 이름")
@click.option("--description", default=None, help="설명")
@click.option("--link", default=None, help="관련 링크 URL")
@click.pass_obj
@handle_api_error
def customer_request_update(
    ctx: CliContext,
    customer_id: str,
    request_id: str,
    name: str | None,
    description: str | None,
    link: str | None,
) -> None:
    """고객 요청 수정."""
    data = UpdateCustomerRequest(
        name=name,
        description=description,
        link=link,
    )
    result = ctx.client.customers.requests.update(ctx.workspace, customer_id, request_id, data)
    format_output(result, ctx.output, columns=_REQUEST_COLUMNS)


@customer_request.command("delete")
@click.argument("customer_id")
@click.argument("request_id")
@click.pass_obj
@handle_api_error
def customer_request_delete(ctx: CliContext, customer_id: str, request_id: str) -> None:
    """고객 요청 삭제."""
    if not confirm_delete("고객 요청", request_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.customers.requests.delete(ctx.workspace, customer_id, request_id)
    click.echo(f"고객 요청 '{request_id}'을(를) 삭제했습니다.")
