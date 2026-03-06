---
name: omk-off-this-session-with-delete-task
description: 현재 Claude Code 세션의 oh-my-kanban 자동 추적을 중단하고, 이 세션에서 생성된 Plane Work Item을 모두 삭제합니다.
---

현재 Claude Code 세션의 oh-my-kanban 자동 추적을 중단하고, 이 세션에서 생성된 Plane Work Item을 삭제해주세요.

다음 명령을 실행하세요:

```bash
omk hooks opt-out --delete-tasks
```

이 명령은 자동으로 가장 최근 활성 세션을 찾아 추적을 중단하고 Work Item을 삭제합니다.

실행 후:
- 이 세션에서 생성된 모든 Plane Work Item이 삭제됩니다
- 세션 상태가 opted_out으로 변경됩니다
- 이 세션에서 이후 발생하는 작업은 더 이상 기록되지 않습니다

**주의**: Work Item 삭제는 되돌릴 수 없습니다. Work Item을 유지하면서 추적만 중단하려면 `/omk-off-this-session`을 사용하세요.

특정 세션을 지정하려면:
```bash
omk hooks status          # 세션 ID 확인
omk hooks opt-out --session-id <SESSION_ID> --delete-tasks
```
