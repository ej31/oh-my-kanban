---
name: omk-decision
description: 현재 작업 중 내린 중요한 결정을 Work Item 댓글로 기록한다.
---

# omk decision — 결정 사항을 WI에 기록

현재 작업 중 내린 중요한 결정을 Work Item 댓글로 기록한다.

## 실행 조건

사용자가 "/oh-my-kanban:decision", "/omk:dec" 또는 "결정 기록해줘",
"이 결정을 WI에 남겨줘", "결정 사항 저장해줘" 등을 요청한 경우.

## 절차

### 1. 현재 WI 확인

`state.plane_context.focused_work_item_id`를 확인한다. 없으면:

```text
[omk] 현재 세션에 연결된 Task가 없습니다.
  /oh-my-kanban:focus로 먼저 Task를 연결하세요.
```

### 2. 결정 내용 수집

사용자가 결정 내용을 제공하지 않은 경우, 현재 대화 맥락에서 결정 사항을 추론하고 사용자에게 확인을 요청한다:

- 무엇을 결정했는가?
- 왜 그 결정을 내렸는가?
- 검토한 대안은 무엇인가?

### 3. 결정 댓글 추가

```python
# 사용자 입력은 sanitize_comment() 또는 동등한 escaping 처리 후 삽입한다
mcp__plane__create_work_item_comment(
  work_item_id="<focused_wi_id>",
  comment_html=(
    "## 결정 사항\n\n"
    "**결정**: <sanitized_decision_summary>\n\n"
    "**이유**: <sanitized_rationale>\n\n"
    "**검토한 대안**: <sanitized_alternatives>\n\n"
    "---\n"
    "*omk에 의해 <sanitized_timestamp>에 기록됨*"
  )
)
```

### 4. 확인 알림

```text
[omk] 결정 사항이 기록되었습니다.
  WI: <identifier> — <wi_name>
  결정: <decision_summary>
  URL: <plane_url>
```

## 주의사항

- 결정 내용이 불명확하면 사용자에게 구체적인 내용을 요청한다
- 보안/인증 관련 결정은 민감 정보를 포함하지 않도록 주의한다
- 기록 실패 시 명확한 에러 메시지를 출력한다
