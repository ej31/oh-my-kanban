---
name: omk-off
description: 현재 세션의 oh-my-kanban 자동 추적을 비활성화합니다.
---

# omk-off 스킬 실행 지침

사용자가 /omk-off를 실행하면 아래를 수행하세요.

## 현재 세션 opt-out

다음 명령을 실행합니다 (최근 활성 세션 자동 선택):
```bash
omk hooks opt-out
```

Plane Work Item도 함께 삭제하려면:
```bash
omk hooks opt-out --delete-tasks
```

특정 세션을 지정하려면:
```bash
omk hooks opt-out --session-id <SESSION_ID>
```

## 완료 후

opt-out이 완료되면 해당 세션에서는 더 이상 드리프트 감지, 파일 추적, WI 연동이 동작하지 않습니다.

다시 활성화하려면 새 Claude Code 세션을 시작하세요 (훅은 유지되므로 새 세션에서 자동으로 재활성화됩니다).

훅 자체를 제거하려면: `omk hooks uninstall`
