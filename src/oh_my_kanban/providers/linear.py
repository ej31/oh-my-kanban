"""Linear ProviderClient 구현 (stub — 향후 완전 구현 예정)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from oh_my_kanban.provider import ProviderClient

if TYPE_CHECKING:
    from oh_my_kanban.config import Config
    from oh_my_kanban.provider import ProviderContext


class LinearProviderClient(ProviderClient):
    """Linear GraphQL API를 통해 Issue를 관리하는 클라이언트."""

    def __init__(self, cfg: "Config") -> None:
        self._cfg = cfg

    @property
    def name(self) -> str:
        return "linear"

    def build_compact_context(self, context: "ProviderContext") -> tuple[str, list[str]]:
        raise NotImplementedError("LinearProviderClient.build_compact_context는 아직 구현되지 않았습니다.")

    def post_comment(
        self,
        context: "ProviderContext",
        comment: str,
        work_item_id: str = "",
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("LinearProviderClient.post_comment는 아직 구현되지 않았습니다.")

    def poll_comments(
        self,
        context: "ProviderContext",
        known_ids: set[str],
    ) -> tuple[list[dict[str, Any]], list[str]]:
        raise NotImplementedError("LinearProviderClient.poll_comments는 아직 구현되지 않았습니다.")

    def check_subtask_completion(self, context: "ProviderContext") -> int | None:
        raise NotImplementedError("LinearProviderClient.check_subtask_completion는 아직 구현되지 않았습니다.")

    def create_work_item(
        self,
        context: "ProviderContext",
        title: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Linear GraphQL API로 새 Issue를 생성하고 id를 포함한 dict를 반환한다."""
        from oh_my_kanban.linear_client import LinearClient

        cfg = self._cfg
        if not cfg.linear_api_key:
            raise RuntimeError("Linear WI 생성에 필요한 linear_api_key가 누락되었습니다.")
        team_id = cfg.linear_team_id or context.project_id
        if not team_id:
            raise RuntimeError("Linear WI 생성에 필요한 linear_team_id 또는 project_id가 누락되었습니다.")

        client = LinearClient(api_key=cfg.linear_api_key)
        query = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                }
            }
        }
        """
        variables: dict[str, Any] = {
            "input": {
                "teamId": team_id,
                "title": title,
            }
        }
        if description:
            variables["input"]["description"] = description

        data: dict[str, Any] = {}
        try:
            data = client.execute(query, variables)
        finally:
            client.close()
        issue = data.get("issueCreate", {}).get("issue", {})
        return {"id": issue.get("id", ""), "raw": issue}

    def switch_task(
        self,
        context: "ProviderContext",
        new_task_title: str,
        reason: str = "",
    ) -> dict[str, Any]:
        raise NotImplementedError("LinearProviderClient.switch_task는 아직 구현되지 않았습니다.")
