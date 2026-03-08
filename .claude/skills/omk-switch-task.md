# omk switch-task — 다른 WI로 전환

현재 세션을 다른 Work Item으로 전환한다. 기존 WI는 "On Hold" 상태가 된다.

## 실행 조건

사용자가 "/oh-my-kanban:switch-task", "/omk:sw" 또는 "다른 태스크로 바꿔줘", "WI 전환해줘" 등을 요청한 경우.

## 절차

### 1. 현재 WI 확인

`state.plane_context.focused_work_item_id`를 확인한다.

### 2. 새 WI 선택

사용자가 새 WI를 지정하지 않은 경우, 활성 WI 목록을 보여주고 선택을 유도한다:

```python
mcp__plane__list_work_items(project_id="<project_id>")
```

새로운 주제라면 새 WI를 생성할지 확인한다.

### 3. 기존 WI를 "On Hold"로 전환

아래 순서로 "On Hold" 상태를 동적 조회한다:

1. 이름이 "On Hold"인 상태 (정확 일치)
2. 이름이 "Paused"인 상태 (정확 일치)
3. `group="cancelled"` 중 첫 번째
4. 없으면 "Backlog" 폴백

```python
mcp__plane__update_work_item(
  work_item_id="<old_wi_id>",
  state_id="<on_hold_state_id>"
)
```

기존 WI에 댓글 추가:

```python
mcp__plane__create_work_item_comment(
  work_item_id="<old_wi_id>",
  comment_html=(
    "## omk 작업 일시 중단\n\n"
    "**세션 ID**: `<session_id[:8]>...`\n"
    "**전환 시각**: <timestamp>\n"
    "**전환 이유**: 사용자 요청으로 다른 Task로 전환"
  )
)
```

### 4. 새 WI에 세션 연결

새 WI에 세션 연결 댓글 추가:

```python
mcp__plane__create_work_item_comment(
  work_item_id="<new_wi_id>",
  comment_html=(
    "## omk 세션 전환\n\n"
    "**세션 ID**: `<session_id[:8]>...`\n"
    "**전환 시각**: <timestamp>\n"
    "**이전 Task**: <old_wi_identifier>"
  )
)
```

### 5. 세션 상태 업데이트

세션 파일의 `plane_context.focused_work_item_id`를 새 WI UUID로 업데이트한다.

### 6. 관계 설정 (선택)

두 WI 간 `relates_to` 관계를 설정한다:

```python
mcp__plane__create_work_item_relation(
  work_item_id="<old_wi_id>",
  related_work_item_id="<new_wi_id>",
  relation_type="relates_to"
)
```

### 7. 확인 알림

```text
[omk] Task가 전환되었습니다.
  이전: <old_identifier> — <old_wi_name> (On Hold)
  현재: <new_identifier> — <new_wi_name> (In Progress)
```

## 주의사항

- 전환 전 사용자에게 확인을 받는다
- "On Hold" 상태가 없으면 대체 상태를 사용하고 사용자에게 안내한다
- 상태 변경 실패 시 명확한 에러 메시지를 출력한다
