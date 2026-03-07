# omk focus — 기존 WI에 세션 연결

현재 Claude Code 세션을 특정 Plane Work Item에 연결한다.

## 실행 조건

사용자가 "/oh-my-kanban:focus", "/omk:f" 또는 "WI 연결해줘", "YCF-123에 연결해줘" 등을 요청한 경우.

## 절차

### 1. WI 식별자 확인

사용자가 WI 식별자(예: OMK-5, YCF-123)를 제공했는지 확인한다.
제공하지 않은 경우, 활성 WI 목록을 보여주고 선택을 유도한다:

```
mcp__plane__list_work_items(project_id="<project_id>", state="진행 중")
```

### 2. WI 조회

사용자가 제공한 식별자로 WI를 조회한다:

```
mcp__plane__retrieve_work_item_by_identifier(identifier="OMK-5")
```

또는 직접 UUID가 있으면:

```
mcp__plane__retrieve_work_item(work_item_id="<uuid>")
```

### 3. PlaneContext 업데이트

세션 파일에서 현재 PlaneContext를 읽고 work_item_ids, focused_work_item_id를 업데이트한다:

```python
# ~/.local/share/oh-my-kanban/sessions/<session_id>.json 에서
# plane_context.work_item_ids 에 WI UUID 추가
# plane_context.focused_work_item_id 를 해당 UUID로 설정
```

실제 업데이트는 `omk` CLI 또는 직접 세션 파일 수정으로 처리한다.

### 4. 세션 시작 댓글 추가

연결된 WI에 구조화 댓글을 추가한다:

```
mcp__plane__create_work_item_comment(
  work_item_id="<wi_uuid>",
  comment_html="## omk 세션 연결\n\n**세션 ID**: `<session_id[:8]>...`\n**연결 시각**: <timestamp>\n**목표**: 사용자 요청에 의한 수동 연결"
)
```

### 5. 사용자에게 확인 알림

```
[omk] Task가 연결되었습니다.
  WI: <identifier> — <wi_name>
  URL: <plane_url>
  이 세션에서 작업 진행 상황이 자동으로 기록됩니다.
```

## 현재 PlaneContext 읽기

현재 세션의 PlaneContext 정보는 세션 파일에서 확인한다:
- `state.plane_context.work_item_ids` — 연결된 WI UUID 목록
- `state.plane_context.focused_work_item_id` — 현재 집중 WI
- `state.plane_context.project_id` — 연결된 프로젝트

## 주의사항

- 이미 연결된 WI가 있으면 사용자에게 확인 후 교체한다
- WI 조회 실패 시 사용자에게 명확한 에러 메시지를 출력한다
- 연결 후 HUD가 갱신되어야 한다 (`update_hud()` 호출)
