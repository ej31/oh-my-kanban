# omk context-sync — Plane WI 최신 상태 동기화

현재 세션에 연결된 Plane Work Item의 최신 상태를 조회하여 컨텍스트를 업데이트한다.

## 실행 조건

사용자가 "/oh-my-kanban:context-sync" 또는 "WI 상태 동기화해줘", "최신 댓글 가져와줘" 등을 요청한 경우.

## 절차

### 1. 현재 PlaneContext 읽기

현재 세션의 PlaneContext에서 연결된 WI를 확인한다:

- `state.plane_context.focused_work_item_id` — 집중 WI (우선)
- `state.plane_context.work_item_ids` — 전체 연결 WI 목록
- `state.plane_context.project_id` — 프로젝트 ID

WI가 없으면 사용자에게 `/oh-my-kanban:focus`로 연결을 요청한다.

### 2. WI 최신 상태 조회

```python
mcp__plane__retrieve_work_item(work_item_id="<focused_work_item_id>")
```

조회 결과에서 추출:

- WI 이름, 상태, 우선순위
- 담당자, 마감일
- 라벨 목록

### 3. 최근 댓글 조회

```python
mcp__plane__list_work_item_comments(work_item_id="<focused_work_item_id>")
```

최근 10개 댓글을 가져오고 `last_comment_check` 이후 새 댓글을 필터링한다.

### 4. Sub-task 목록 조회

```python
mcp__plane__list_work_items(project_id="<project_id>", parent="<focused_work_item_id>")
```

### 5. 동기화 결과 요약 출력

```text
[omk] WI 동기화 완료
  📋 <identifier>: <wi_name>
  상태: <state_name> | 우선순위: <priority>

  최근 댓글 (<n>개):
    [<date>] <author>: <comment_preview>
    ...

  Sub-tasks (<n>개):
    ✓ <sub_task_1_name> (완료)
    ○ <sub_task_2_name> (진행 중)
    ...
```

### 6. PlaneContext 업데이트

`last_comment_check`를 현재 시각으로 업데이트한다.
새로 확인한 댓글 ID를 `known_comment_ids`에 추가한다.

## 현재 PlaneContext 읽기

- `state.plane_context.focused_work_item_id` — 동기화 대상 WI
- `state.plane_context.last_comment_check` — 마지막 동기화 시각
- `state.plane_context.known_comment_ids` — 이미 확인한 댓글 ID 목록

## 주의사항

- API 실패 시 사용자에게 명확한 에러와 함께 `/oh-my-kanban:doctor` 실행을 안내한다
- 동기화는 Plane WI 자체를 수정하지 않는다. 다만 세션의
  `last_comment_check`와 `known_comment_ids`는 갱신할 수 있다
- 새 댓글이 없으면 "새로운 댓글 없음"을 명시한다
