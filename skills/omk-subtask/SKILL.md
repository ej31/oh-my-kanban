---
name: omk-subtask
description: 현재 세션의 메인 Work Item에 Sub-task를 생성한다.
---

# omk subtask — 현재 WI에 하위 태스크 생성

현재 세션의 메인 Work Item에 Sub-task를 생성한다.

## 실행 조건

사용자가 "/oh-my-kanban:subtask", "/omk:st" 또는 "서브태스크 추가해줘", "하위 태스크 만들어줘" 등을 요청한 경우.

## 절차

### 1. 현재 WI 확인

세션 파일에서 현재 메인 WI를 확인한다:

- `state.plane_context.main_task_id` — 있으면 이것을 `parent_id`로 사용
- `state.plane_context.focused_work_item_id` — `main_task_id`가 없을 때만 폴백으로 사용

연결된 WI가 없으면:

```text
[omk] 현재 세션에 연결된 Task가 없습니다.
  /oh-my-kanban:focus 또는 /oh-my-kanban:create-task로 먼저 Task를 연결하세요.
```

### 2. Sub-task 정보 수집

사용자에게 Sub-task 이름을 확인한다. 대화 맥락에서 추론 가능하면 추론하고 확인을 요청한다.

### 3. Sub-task 생성

```python
# parent_id 결정 규칙:
# 1. main_task_id가 있으면 main_task_id
# 2. 없으면 focused_work_item_id
mcp__plane__create_work_item(
  project_id="<project_id>",
  name="<subtask_name>",
  parent_id="<parent_wi_id>",
  state_id="<in_progress_state_id>",
  label_ids=["<omk:type:sub 라벨 ID>"]
)
```

상태(State) ID와 라벨 ID는 하드코딩하지 않고 동적 조회한다:

```python
mcp__plane__list_states(project_id="<project_id>")
mcp__plane__list_labels(project_id="<project_id>")
```

### 4. 확인 알림

```text
[omk] Sub-task가 생성되었습니다.
  WI: <identifier> — <subtask_name>
  상위: <parent_identifier> — <parent_name>
  URL: <plane_url>
```

## 주의사항

- Sub-task 생성 전 이름을 사용자에게 확인받는다
- Sub-task에는 `omk:type:sub` 라벨을 자동으로 적용한다
- 생성 실패 시 명확한 에러 메시지를 출력한다
