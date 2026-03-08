# omk status — 현재 세션 WI 상태 표시

현재 Claude Code 세션에 연결된 Plane Work Item 정보를 표시한다.

## 표시 정보

1. **연결된 WI 목록** — `state.plane_context.work_item_ids`
2. **집중 WI** — `state.plane_context.focused_work_item_id`
3. **메인 태스크** — `state.plane_context.main_task_id`
4. **외부 삭제된 WI** — `state.plane_context.stale_work_item_ids`
5. **세션 통계** — 요청 횟수, 수정 파일 수

## 현재 상태 조회 방법

MCP tool을 사용한다:

```python
omk_get_session_status()
```

또는 세션 파일에서 직접 읽는다:

```bash
cat ~/.local/share/oh-my-kanban/sessions/<session_id>.json | python3 -m json.tool
```

## PlaneContext 읽기

세션 상태에서 다음을 확인한다:

- `plane_context.project_id` — 프로젝트 UUID
- `plane_context.work_item_ids` — 추적 중인 WI UUID 목록
- `plane_context.focused_work_item_id` — 현재 집중 작업 WI
- `plane_context.last_comment_check` — 마지막 댓글 폴링 시각

WI가 연결되지 않은 경우: `/oh-my-kanban:focus <WI-ID>` 또는 `/oh-my-kanban:create-task`로 연결한다.
