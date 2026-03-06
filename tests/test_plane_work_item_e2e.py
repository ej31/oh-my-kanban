"""Plane work-item E2E 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from oh_my_kanban.context import CliContext


def _paginated(items: list) -> MagicMock:
    resp = MagicMock()
    resp.results = items
    resp.next_page_results = False
    return resp


@pytest.fixture
def ctx() -> CliContext:
    context = CliContext(
        _base_url="https://api.plane.so",
        _api_key="test-api-key",
        workspace="test-workspace",
        project="test-project-id",
        output="json",
    )
    context._client = MagicMock()
    return context


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ─── work-item list ────────────────────────────────────────────────────────────


class TestWorkItemList:
    def test_list_returns_items(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        item = MagicMock()
        item.id = "wi-001"
        item.name = "Fix login bug"
        ctx.client.work_items.list.return_value = _paginated([item])
        result = runner.invoke(work_item, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.work_items.list.assert_called_once()

    def test_list_empty_returns_ok(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_items.list.return_value = _paginated([])
        result = runner.invoke(work_item, ["list"], obj=ctx)
        assert result.exit_code == 0

    def test_list_with_per_page_option(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_items.list.return_value = _paginated([])
        result = runner.invoke(work_item, ["list", "--per-page", "10"], obj=ctx)
        assert result.exit_code == 0

    def test_list_with_priority_filter(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        item = MagicMock()
        item.id = "wi-urgent"
        ctx.client.work_items.list.return_value = _paginated([item])
        result = runner.invoke(work_item, ["list", "--priority", "urgent"], obj=ctx)
        assert result.exit_code == 0
        ctx.client.work_items.list.assert_called_once()

    def test_list_with_invalid_priority_fails(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(work_item, ["list", "--priority", "INVALID"], obj=ctx)
        assert result.exit_code != 0

    def test_list_without_project_fails(self, runner):
        from oh_my_kanban.commands.work_item import work_item

        no_proj_ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-api-key",
            workspace="test-workspace",
            project="",
            output="json",
        )
        no_proj_ctx._client = MagicMock()
        result = runner.invoke(work_item, ["list"], obj=no_proj_ctx)
        assert result.exit_code != 0

    def test_list_with_order_by(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_items.list.return_value = _paginated([])
        result = runner.invoke(work_item, ["list", "--order-by", "created_at"], obj=ctx)
        assert result.exit_code == 0


# ─── work-item get ─────────────────────────────────────────────────────────────


class TestWorkItemGet:
    def test_get_by_uuid_returns_detail(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        item = MagicMock()
        item.id = "12345678-0000-0000-0000-000000000001"
        item.name = "Fix login"
        ctx.client.work_items.retrieve.return_value = item
        result = runner.invoke(work_item, ["get", "12345678-0000-0000-0000-000000000001"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.work_items.retrieve.assert_called_once()

    def test_get_by_identifier_uses_retrieve_by_identifier(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        item = MagicMock()
        item.id = "12345678-0000-0000-0000-000000000002"
        ctx.client.work_items.retrieve_by_identifier.return_value = item
        result = runner.invoke(work_item, ["get", "PROJ-123"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.work_items.retrieve_by_identifier.assert_called_once()


# ─── work-item create ──────────────────────────────────────────────────────────


class TestWorkItemCreate:
    def test_create_minimal(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        created = MagicMock()
        created.id = "wi-new"
        ctx.client.work_items.create.return_value = created
        result = runner.invoke(work_item, ["create", "--name", "New Task"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.work_items.create.assert_called_once()

    def test_create_with_all_options(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        created = MagicMock()
        ctx.client.work_items.create.return_value = created
        result = runner.invoke(
            work_item,
            [
                "create",
                "--name", "Full Task",
                "--priority", "high",
                "--state", "state-uuid",
                "--assignee", "user-uuid",
                "--label", "label-uuid",
                "--start-date", "2026-01-01",
                "--target-date", "2026-06-01",
                "--description", "Some description",
                "--point", "5",
            ],
            obj=ctx,
        )
        assert result.exit_code == 0, result.output

    def test_create_invalid_date_fails(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(
            work_item, ["create", "--name", "Task", "--target-date", "not-a-date"], obj=ctx
        )
        assert result.exit_code != 0

    def test_create_without_name_fails(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(work_item, ["create"], obj=ctx)
        assert result.exit_code != 0

    def test_create_with_invalid_priority_fails(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(
            work_item, ["create", "--name", "Task", "--priority", "SUPER"], obj=ctx
        )
        assert result.exit_code != 0


# ─── work-item update ──────────────────────────────────────────────────────────


class TestWorkItemUpdate:
    def test_update_name(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        updated = MagicMock()
        ctx.client.work_items.update.return_value = updated
        result = runner.invoke(
            work_item, ["update", "wi-001", "--name", "Updated Name"], obj=ctx
        )
        assert result.exit_code == 0, result.output
        ctx.client.work_items.update.assert_called_once()

    def test_update_priority(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_items.update.return_value = MagicMock()
        result = runner.invoke(
            work_item, ["update", "wi-001", "--priority", "low"], obj=ctx
        )
        assert result.exit_code == 0, result.output

    def test_update_invalid_date_fails(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(
            work_item, ["update", "wi-001", "--start-date", "bad-date"], obj=ctx
        )
        assert result.exit_code != 0


# ─── work-item delete ──────────────────────────────────────────────────────────


class TestWorkItemDelete:
    def test_delete_confirmed(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_items.delete.return_value = None
        result = runner.invoke(work_item, ["delete", "wi-001"], obj=ctx, input="y\n")
        assert result.exit_code == 0, result.output
        ctx.client.work_items.delete.assert_called_once()

    def test_delete_aborted(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(work_item, ["delete", "wi-001"], obj=ctx, input="n\n")
        assert result.exit_code != 0
        ctx.client.work_items.delete.assert_not_called()


# ─── work-item search ──────────────────────────────────────────────────────────


class TestWorkItemSearch:
    def test_search_returns_results(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        search_result = MagicMock()
        search_result.issues = [MagicMock(id="wi-found", name="Login bug")]
        ctx.client.work_items.search.return_value = search_result
        result = runner.invoke(work_item, ["search", "--query", "login bug"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.work_items.search.assert_called_once()

    def test_search_empty_returns_ok(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        search_result = MagicMock()
        search_result.issues = []
        ctx.client.work_items.search.return_value = search_result
        result = runner.invoke(work_item, ["search", "--query", "nonexistent"], obj=ctx)
        assert result.exit_code == 0


# ─── work-item comment ─────────────────────────────────────────────────────────


class TestWorkItemComment:
    def test_comment_list(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        comment = MagicMock()
        comment.id = "cmt-001"
        ctx.client.work_item_comments.list.return_value = _paginated([comment])
        result = runner.invoke(work_item, ["comment", "list", "wi-001"], obj=ctx)
        assert result.exit_code == 0, result.output

    def test_comment_create(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_item_comments.create.return_value = MagicMock()
        result = runner.invoke(
            work_item, ["comment", "create", "wi-001", "--body", "Test comment"], obj=ctx
        )
        assert result.exit_code == 0, result.output

    def test_comment_update(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_item_comments.update.return_value = MagicMock()
        result = runner.invoke(
            work_item,
            ["comment", "update", "wi-001", "cmt-001", "--body", "Updated comment"],
            obj=ctx,
        )
        assert result.exit_code == 0, result.output

    def test_comment_delete_confirmed(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_item_comments.delete.return_value = None
        result = runner.invoke(
            work_item, ["comment", "delete", "wi-001", "cmt-001"], obj=ctx, input="y\n"
        )
        assert result.exit_code == 0, result.output


# ─── work-item link ────────────────────────────────────────────────────────────


class TestWorkItemLink:
    def test_link_list(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        lnk = MagicMock()
        lnk.id = "lnk-001"
        ctx.client.work_item_links.list.return_value = _paginated([lnk])
        result = runner.invoke(work_item, ["link", "list", "wi-001"], obj=ctx)
        assert result.exit_code == 0, result.output

    def test_link_create(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_item_links.create.return_value = MagicMock()
        result = runner.invoke(
            work_item,
            ["link", "create", "wi-001", "--url", "https://example.com"],
            obj=ctx,
        )
        assert result.exit_code == 0, result.output

    def test_link_delete_confirmed(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_item_links.delete.return_value = None
        result = runner.invoke(
            work_item, ["link", "delete", "wi-001", "lnk-001"], obj=ctx, input="y\n"
        )
        assert result.exit_code == 0, result.output


# ─── work-item relation ────────────────────────────────────────────────────────


class TestWorkItemRelation:
    def test_relation_list(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        rel_result = MagicMock()
        rel_result.model_dump.return_value = {"blocking": [], "blocked_by": []}
        ctx.client.work_items.relations.list.return_value = rel_result
        result = runner.invoke(work_item, ["relation", "list", "wi-001"], obj=ctx)
        assert result.exit_code == 0, result.output

    def test_relation_create(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_items.relations.create.return_value = MagicMock()
        result = runner.invoke(
            work_item,
            [
                "relation",
                "create",
                "wi-001",
                "--related-work-item", "wi-002",
                "--relation-type", "blocking",
            ],
            obj=ctx,
        )
        assert result.exit_code == 0, result.output

    def test_relation_delete_confirmed(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_items.relations.delete.return_value = None
        result = runner.invoke(
            work_item,
            ["relation", "delete", "wi-001", "--related-work-item", "wi-002"],
            obj=ctx,
            input="y\n",
        )
        assert result.exit_code == 0, result.output


# ─── work-item activity ────────────────────────────────────────────────────────


class TestWorkItemActivity:
    def test_activity_list(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        act = MagicMock()
        act.id = "act-001"
        ctx.client.work_item_activities.list.return_value = _paginated([act])
        result = runner.invoke(work_item, ["activity", "list", "wi-001"], obj=ctx)
        assert result.exit_code == 0, result.output


# ─── work-item worklog ─────────────────────────────────────────────────────────


class TestWorkItemWorklog:
    def test_worklog_list(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        wl = MagicMock()
        wl.id = "wl-001"
        ctx.client.work_item_worklogs.list.return_value = _paginated([wl])
        result = runner.invoke(work_item, ["worklog", "list", "wi-001"], obj=ctx)
        assert result.exit_code == 0, result.output

    def test_worklog_create(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_item_worklogs.create.return_value = MagicMock()
        result = runner.invoke(
            work_item,
            ["worklog", "create", "wi-001", "--duration", "60"],
            obj=ctx,
        )
        assert result.exit_code == 0, result.output

    def test_worklog_delete_confirmed(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_item_worklogs.delete.return_value = None
        result = runner.invoke(
            work_item, ["worklog", "delete", "wi-001", "wl-001"], obj=ctx, input="y\n"
        )
        assert result.exit_code == 0, result.output
