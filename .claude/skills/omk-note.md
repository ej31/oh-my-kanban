# omk note — 현재 Task에 메모 추가

현재 세션에 연결된 Plane Work Item에 메모/댓글을 추가한다.

## 실행 조건

사용자가 "/oh-my-kanban:note", "/omk:n" 또는 "메모 남겨줘", "댓글 추가해줘", "이거 기록해줘" 등을 요청한 경우.

## 절차

### 1. 현재 WI 확인

현재 세션의 PlaneContext에서 연결된 WI를 확인한다:
- `state.plane_context.focused_work_item_id` — 집중 WI (우선)
- `state.plane_context.work_item_ids[0]` — 첫 번째 연결 WI (폴백)

WI가 없으면:
```
연결된 Task가 없습니다. /oh-my-kanban:focus로 Task에 연결하거나
/oh-my-kanban:create-task로 새 Task를 생성하세요.
```

### 2. 메모 내용 확인

사용자가 제공한 텍스트를 메모로 사용한다. 제공하지 않은 경우 요청한다:
```
어떤 내용을 기록할까요?
```

### 3. 댓글 형식 선택

메모 유형에 따라 적절한 형식을 사용한다:

**일반 메모:**
```html
<p>[{timestamp}] {memo_text}</p>
```

**결정 사항:**
```html
<h3>결정 사항</h3>
<ul>
  <li>결정: {decision}</li>
  <li>이유: {reason}</li>
  <li>검토한 대안: {alternatives}</li>
</ul>
```

**진행 상황 업데이트:**
```html
<h3>진행 상황</h3>
<p>{status_update}</p>
```

### 4. 댓글 추가

```
mcp__plane__create_work_item_comment(
  work_item_id="<focused_work_item_id>",
  comment_html="<formatted_comment>"
)
```

### 5. 완료 확인

```
[omk] 메모가 기록되었습니다.
  WI: <identifier> — <wi_name>
  내용: <memo_summary>
```

## 현재 PlaneContext 읽기

- `state.plane_context.focused_work_item_id` — 메모를 추가할 WI UUID
- `state.plane_context.project_id` — 프로젝트 ID

## 주의사항

- 민감한 정보(API 키, 비밀번호 등)는 메모에 포함하지 않는다
- 댓글 추가 실패 시 사용자에게 명확한 에러와 함께 Plane 웹 링크를 제공한다
- 긴 메모는 HTML 형식으로 구조화하여 가독성을 높인다
