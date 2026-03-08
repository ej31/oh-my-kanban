---
name: omk-open
description: 현재 세션에 연결된 Plane Work Item의 웹 URL을 표시한다.
---

# omk open — 현재 Task 웹 링크 표시

현재 세션에 연결된 Plane Work Item의 웹 URL을 표시한다.

## 실행 조건

사용자가 "/oh-my-kanban:open", "/omk:o" 또는 "Task 링크 보여줘", "Plane에서 열어줘" 등을 요청한 경우.

## 절차

### 1. 현재 WI 확인

현재 세션의 PlaneContext에서 연결된 WI를 확인한다:

- `state.plane_context.focused_work_item_id` — 집중 WI (우선)
- `state.plane_context.work_item_ids` — 연결된 WI 목록

WI가 없으면:

```text
연결된 Task가 없습니다. /oh-my-kanban:focus로 Task에 연결하거나
/oh-my-kanban:create-task로 새 Task를 생성하세요.
```

### 2. WI 상세 조회

```python
mcp__plane__retrieve_work_item(work_item_id="<focused_work_item_id>")
```

응답에서 `sequence_id`와 WI 이름을 추출한다.

### 3. URL 생성

Plane URL 패턴:

```text
{base_url}/{workspace_slug}/projects/{project_id}/issues/{sequence_id}/
```

설정에서 값을 읽는다:

- `base_url`: `~/.config/oh-my-kanban/config.toml`의 `base_url`
- `workspace_slug`: 설정의 `workspace_slug`
- `project_id`: `state.plane_context.project_id`

### 4. URL 출력

```text
[omk] 현재 Task
  WI: <identifier> — <wi_name>
  상태: <state_name>
  URL: <plane_url>

  클릭하거나 브라우저에 붙여넣기 하세요.
```

### 5. 멀티 WI 처리

여러 WI가 연결된 경우 모두 표시한다:

```text
[omk] 연결된 Tasks
  1. <identifier1> — <name1>: <url1>
  2. <identifier2> — <name2>: <url2>
```

## 현재 PlaneContext 읽기

- `state.plane_context.focused_work_item_id` — 집중 WI UUID
- `state.plane_context.work_item_ids` — 전체 연결 WI 목록
- `state.plane_context.project_id` — URL 생성에 필요한 프로젝트 ID

## 주의사항

- URL은 클릭 가능한 하이퍼링크 형식으로 출력한다
- WI 조회 실패 시에도 세션 파일에 저장된 정보로 URL을 생성 시도한다
- base_url이 설정되지 않은 경우 plane.so 기본값을 사용한다
