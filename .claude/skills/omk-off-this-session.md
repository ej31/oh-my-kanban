---
name: omk-off-this-session
description: 현재 Claude Code 세션의 oh-my-kanban 자동 추적을 중단합니다. 이미 생성된 Plane Work Item은 유지됩니다.
---

현재 Claude Code 세션의 oh-my-kanban 자동 추적을 중단해주세요.

다음 명령을 실행하세요:

```bash
omk hooks opt-out
```

이 명령은 자동으로 가장 최근 활성 세션을 찾아 추적을 중단합니다.

실행 후:
- 이미 생성된 Plane Work Item에 "사용자 요청에 의해 이 세션의 자동 추적이 중단되었습니다" 댓글이 추가됩니다
- 이 세션에서 이후 발생하는 작업은 더 이상 기록되지 않습니다
- 세션 종료(SessionEnd) 시 Plane 동기화가 생략됩니다

특정 세션을 지정하려면:
```bash
omk hooks status          # 세션 ID 확인
omk hooks opt-out --session-id <SESSION_ID>
```
