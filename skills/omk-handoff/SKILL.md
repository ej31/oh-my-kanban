---
name: omk-handoff
description: 다음 세션 또는 팀원을 위한 핸드오프 메모를 Work Item 댓글로 기록한다.
---

# omk handoff — 핸드오프 메모를 WI에 기록

다음 세션 또는 팀원을 위한 핸드오프 메모를 Work Item 댓글로 기록한다.

## 실행 조건

사용자가 "/oh-my-kanban:handoff", "/omk:ho" 또는
"핸드오프 메모 남겨줘", "다음 세션을 위해 메모 기록해줘" 등을 요청한 경우.
또는 omk가 세션 종료 시 additionalContext로 핸드오프 기록을 요청한 경우.

## 절차

### 1. 현재 WI 확인

`state.plane_context.focused_work_item_id`를 확인한다. 없으면:

```text
[omk] 현재 세션에 연결된 Task가 없습니다.
  핸드오프 메모를 남길 Work Item이 없습니다.
```

### 2. 핸드오프 내용 수집

현재 세션의 작업 상태를 바탕으로 핸드오프 내용을 수집한다:

- **현재 상태**: 무엇이 완료됐는가?
- **미완성 부분**: 무엇이 남아있는가?
- **다음 할 일**: 다음 세션에서 어디서 시작해야 하는가?
- **주의사항**: 알아두어야 할 사항이 있는가?

사용자가 내용을 제공하지 않은 경우, 현재 대화 맥락에서 자동으로 추론한다.

### 3. 핸드오프 댓글 추가

```python
mcp__plane__create_work_item_comment(
  work_item_id="<focused_wi_id>",
  comment_html="## 핸드오프\n\n**현재 상태**: <current_status>\n\n"
  "**미완성 부분**: <incomplete_items>\n\n**다음 할 일**: "
  "<next_steps>\n\n**주의사항**: <notes>\n\n---\n"
  "*omk에 의해 <timestamp>에 기록됨 "
  "(세션 ID: <session_id[:8]>...)*"
)
```

### 4. 확인 알림

```text
[omk] 핸드오프 메모가 기록되었습니다.
  WI: <identifier> — <wi_name>
  다음 세션에서 이 메모가 자동으로 표시됩니다.
  URL: <plane_url>
```

## 주의사항

- 핸드오프 메모는 구체적이고 실행 가능한 정보를 포함해야 한다
- 파일 경로, 함수명, 라인 번호 등 구체적인 위치 정보를 포함하면 좋다
- 기록 실패 시 명확한 에러 메시지를 출력한다
