---
name: omk-context-injection
description: 현재 세션에 연결된 Plane Work Item의 정보를 Claude의 컨텍스트에 명시적으로 주입한다.
---

# omk context-injection — Plane WI 컨텍스트 수동 주입

현재 세션에 연결된 Plane Work Item의 정보를 Claude의 컨텍스트에 명시적으로 주입한다.
compact 이후 맥락 복원 또는 새 세션에서 이전 작업 맥락이 필요할 때 사용한다.

## 실행 조건

사용자가 "/oh-my-kanban:context-injection" 또는 "WI 내용 불러와줘", "이전 작업 내용 복원해줘", "Plane 내용 주입해줘" 등을 요청한 경우.

## 절차

### 1. 현재 PlaneContext 읽기

현재 세션의 PlaneContext에서 연결된 WI를 확인한다:
- `state.plane_context.work_item_ids` — 연결된 WI UUID 목록
- `state.plane_context.focused_work_item_id` — 집중 WI
- `state.plane_context.project_id` — 프로젝트 ID

### 2. WI 정보 수집

각 연결된 WI에 대해:

```
mcp__plane__retrieve_work_item(work_item_id="<wi_id>")
mcp__plane__list_work_item_comments(work_item_id="<wi_id>")
mcp__plane__list_work_items(project_id="<project_id>", parent="<wi_id>")
```

### 3. 컨텍스트 구조화

수집된 정보를 아래 형식으로 구조화한다:

```
[omk: Plane Work Item 컨텍스트]

### <identifier>: <wi_name>
상태: <state_name> | 우선순위: <priority>
설명: <description_preview (최대 500자)>

최근 댓글 (최신 10개):
  [<date>] <author>: <comment_text>
  ...

Sub-tasks:
  - [완료] <sub_task_name>
  - [진행 중] <sub_task_name>
  ...
```

### 4. 자동 주입 시나리오 (세션 재개)

`/compact` 발생 후 `SessionStart(compact)` 훅이 자동으로 `build_plane_context()`를 호출하여 WI 정보를 `additionalContext`로 주입한다.

수동 주입이 필요한 경우:
- compact 이후에도 WI 정보가 없는 경우
- 새 세션에서 이전 WI의 맥락을 명시적으로 복원하려는 경우

### 5. 주입 결과 확인

```
[omk] WI 컨텍스트가 주입되었습니다.
  📋 <identifier>: <wi_name>
  포함 정보: 제목, 상태, 설명, 댓글 <n>개, Sub-task <n>개
  이제 WI 맥락을 바탕으로 작업을 계속할 수 있습니다.
```

## 두 가지 주입 모드

### 자동 주입 (SessionStart compact)

`/compact` 발생 시 `session_start.py`의 `_handle_compact()` 함수가:
1. 세션 파일에서 `work_item_ids` 읽기
2. `build_plane_context()` 호출 (ThreadPoolExecutor로 병렬 조회)
3. 결과를 `additionalContext`로 Claude에 주입

### 수동 주입 (이 스킬)

1. 사용자가 명시적으로 요청
2. MCP tool로 WI 정보 수집
3. 구조화된 텍스트를 현재 대화에 직접 삽입

## 현재 PlaneContext 읽기

- `state.plane_context.work_item_ids` — 컨텍스트를 주입할 WI 목록
- `state.plane_context.focused_work_item_id` — 우선 대상 WI
- `state.scope.summary` — 현재 세션 목표 (컨텍스트 보완)

## 주의사항

- API 실패 시 세션 파일에 저장된 기존 정보라도 활용한다
- 민감한 정보(API 키 등)는 댓글에서 `[REDACTED]`로 마스킹한다
- 컨텍스트가 너무 길면 3000자로 잘라 Claude 컨텍스트 오염을 방지한다
