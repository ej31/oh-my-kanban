---
name: omk-new-session
description: 현재 세션을 종료하고 새로운 작업 범위로 세션을 명시적으로 전환합니다. 이전 작업이 완료되고 완전히 다른 목표의 작업을 시작할 때 사용합니다.
---

현재 세션을 종료하고 새로운 작업 세션을 시작해주세요.

**1단계: 현재 세션 종료**

기존 세션을 정상 종료합니다 (Plane Work Item에 완료 댓글이 추가됩니다):

```bash
omk hooks opt-out
```

또는 현재 세션 Work Item을 삭제하면서 종료:

```bash
omk hooks opt-out --delete-tasks
```

**2단계: 새 세션 준비 확인**

```bash
omk hooks status
```

활성 세션이 없음을 확인한 후 새 작업을 시작하세요.

**3단계: 새 Plane Work Item 생성 (선택)**

새로운 작업 범위에 맞는 Work Item을 Plane에 생성하세요. 다음 Claude Code 세션 시작 시 oh-my-kanban이 자동으로 새 세션을 감지하고 Work Item과 연결을 시도합니다.

실행 후:
- 이전 세션이 종료되고 Plane에 최종 작업 요약이 기록됩니다
- 새로운 세션은 다음 Claude Code 대화 시작 시 자동으로 생성됩니다
- 새 세션은 새 Plane Work Item과 연결됩니다

**주의**: 현재 세션을 종료하기 전에 중요한 작업이 모두 커밋되었는지 확인하세요.
