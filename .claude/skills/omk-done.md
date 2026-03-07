# omk done — 현재 WI를 완료 처리

현재 세션의 Work Item 상태를 "완료"로 변경한다.

## 실행 조건

사용자가 "/oh-my-kanban:done", "/omk:d" 또는 "태스크 완료했어", "WI 닫아줘", "완료 처리해줘" 등을 요청한 경우.

## 절차

### 1. 현재 WI 확인

세션의 focused_work_item_id를 확인한다. 없으면:
```
[omk] 현재 세션에 연결된 Task가 없습니다.
  /omk focus로 먼저 Task를 연결하세요.
```

### 2. 완료 상태 조회

프로젝트의 "완료" 상태 ID를 동적으로 조회한다:
```
mcp__plane__list_states(project_id="<project_id>")
```

아래 순서로 완료 상태를 찾는다:
1. `group="completed"` 중 첫 번째
2. 이름이 "완료", "Done", "Completed"인 상태

### 3. 완료 처리

```
mcp__plane__update_work_item(
  work_item_id="<focused_wi_id>",
  state_id="<completed_state_id>"
)
```

### 4. 완료 댓글 추가

```
mcp__plane__create_work_item_comment(
  work_item_id="<focused_wi_id>",
  comment_html="## omk 세션 완료\n\n**세션 ID**: `<session_id[:8]>...`\n**완료 시각**: <timestamp>\n**요약**: <scope_summary>"
)
```

### 5. 확인 알림

```
[omk] Task를 완료 처리했습니다.
  WI: <identifier> — <wi_name>
  상태: <previous_state> → 완료
  URL: <plane_url>
```

## 주의사항

- 완료 처리 전 사용자에게 확인을 받는다 ("OMK-5를 완료 처리할까요?")
- Sub-task가 있고 미완료 항목이 있으면 경고를 표시한다
- 완료 상태를 찾지 못하면 사용자에게 수동 처리를 안내한다
- 상태 변경 실패 시 명확한 에러 메시지를 출력한다
