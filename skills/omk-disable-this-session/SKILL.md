---
name: omk-disable-this-session
description: 현재 Claude Code 세션의 omk 자동 추적을 비활성화한다.
---

# omk disable-this-session — 이 세션 추적 비활성화

현재 Claude Code 세션의 omk 자동 추적을 비활성화한다.
단순 Q&A 세션이나 추적이 필요 없는 작업에 사용한다.

## 실행 조건

사용자가 "/oh-my-kanban:disable-this-session", "/omk:off" 또는
"추적 꺼줘", "이 세션은 Q&A야", "기록하지 말아줘" 등을 요청한 경우.

## 절차

### 1. 현재 세션 ID 확인

현재 세션 ID를 확인한다 (환경변수 또는 세션 파일에서).

### 2. opt-out 실행

```bash
omk hooks opt-out
```

이 명령은 다음을 수행한다:

- `state.opted_out = True` 설정
- `state.status = "opted_out"` 설정
- WI가 연결된 경우 구조화 댓글 1회를 추가 (WI 삭제는 하지 않음)
- HUD 초기화

### 3. WI 댓글 형식 참고 (설명용 예시)

실제 구조화 댓글은 Step 2의 `omk hooks opt-out` 처리 안에서 한 번만 기록된다.
아래는 중복 실행용 절차가 아니라, 어떤 형식의 댓글이 남는지 설명하는 예시다.

```text
mcp__plane__create_work_item_comment(
  work_item_id="<focused_work_item_id>",
  comment_html="<h2>omk 추적 중단</h2>
<ul>
  <li>세션 ID: {session_id[:8]}...</li>
  <li>시점: {timestamp}</li>
  <li>사유: 사용자 요청 (단순 질의 세션)</li>
  <li>통계: 프롬프트 {n}회, 수정 파일 {n}개</li>
  <li>상태: 이 세션에서 더 이상 기여하지 않습니다.</li>
</ul>"
)
```

### 4. 사용자에게 확인 알림

```text
[omk] 이 세션의 Task 추적이 비활성화되었습니다.
  이 세션에서는 더 이상 WI 생성/업데이트가 발생하지 않습니다.
  이미 생성된 Plane Work Item은 유지됩니다.
  다시 활성화하려면 새 세션을 시작하세요.
```

## 현재 PlaneContext 읽기

- `state.opted_out` — 현재 opt-out 상태 확인
- `state.plane_context.focused_work_item_id` — 댓글 추가 대상 WI
- `state.stats.total_prompts` — 통계 정보
- `state.stats.files_touched` — 수정 파일 목록

## 주의사항

- **WI는 절대 삭제하지 않는다** — 다른 세션의 기여 기록이 소멸될 수 있음
- opt-out 후에는 SessionStart/End 훅이 no-op으로 동작
- 이미 opted_out 상태면 중복 실행을 방지하고 사용자에게 알린다
- opt-out은 현재 세션에만 영향 — 다른 세션이나 향후 세션은 영향 없음
