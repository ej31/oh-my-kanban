# omk comments — 현재 WI의 최근 댓글 조회

현재 세션과 연결된 Work Item의 최근 댓글을 보여준다.

## 실행 조건

사용자가 "/oh-my-kanban:comments", "/omk:cm" 또는 "댓글 보여줘",
"WI 코멘트 확인해줘", "팀원 코멘트 있어?" 등을 요청한 경우.

## 절차

### 1. 현재 WI 확인

`state.plane_context.focused_work_item_id`를 확인한다. 없으면:

```text
[omk] 현재 세션에 연결된 Task가 없습니다.
  /oh-my-kanban:focus로 먼저 Task를 연결하세요.
```

### 2. 댓글 조회

```python
mcp__plane__list_work_item_comments(
  work_item_id="<focused_wi_id>"
)
```

### 3. 결과 표시

최근 10개 댓글을 시간 역순으로 보여준다:

```text
[omk] WI: <identifier> — <wi_name>
  최근 댓글 (<count>개):

  📝 <author> (<timestamp>):
  <comment_text>

  📝 <author> (<timestamp>):
  <comment_text>

  ...
```

댓글이 없으면:

```text
[omk] <identifier>에 댓글이 없습니다.
  URL: <plane_url>
```

### 4. 새 댓글 처리

새 댓글(이전 폴링 이후 추가된 것)이 있으면 강조하여 표시한다.

세션의 `known_comment_ids`를 최신 댓글 ID 목록으로 업데이트한다.

## 주의사항

- 댓글 조회 실패 시 명확한 에러 메시지를 출력한다
- omk 자체가 달은 댓글(## omk로 시작)은 다른 색/형식으로 구분하면 좋다
- 연결된 WI가 여러 개인 경우, 각 WI의 댓글을 모두 보여준다
