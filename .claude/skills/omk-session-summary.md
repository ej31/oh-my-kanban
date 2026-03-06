---
name: omk-session-summary
description: 현재 세션의 작업 내용을 즉시 Plane Work Item에 댓글로 동기화합니다. 세션을 종료하지 않고 중간 진행 상황을 Plane에 기록하고 싶을 때 사용합니다.
---

현재 세션의 작업 내용을 Plane Work Item에 즉시 동기화해주세요.

## Phase 2 이후 (정식 명령)

```bash
omk hooks sync
```

> **참고**: 위 명령은 Phase 2에서 활성화됩니다.

---

## 현재 사용 가능한 대안 방법

**방법 A: 세션을 opt-out으로 종료해 즉시 동기화**

세션을 종료하면 연결된 Plane Work Item에 작업 요약이 즉시 댓글로 추가됩니다:

```bash
omk hooks opt-out
```

종료 후 새 세션이 자동으로 시작되며, 이후 작업은 새 세션에서 계속 추적됩니다.

**방법 B: Claude Code 대화 종료 (SessionEnd 이벤트)**

Claude Code 대화를 자연스럽게 종료하면 SessionEnd 훅이 실행되어 Plane에 자동 동기화됩니다.
새 대화를 시작하면 새 세션이 생성됩니다.

**세션이 Work Item에 연결되어 있지 않은 경우**

`/omk-link-work-item` 으로 먼저 세션을 Work Item에 연결한 후 동기화하세요:

```bash
omk hooks status          # 연결 상태 확인
```
