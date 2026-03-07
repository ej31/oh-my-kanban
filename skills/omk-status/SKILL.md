---
name: omk-status
description: oh-my-kanban 훅 설치 상태와 활성 세션 목록을 확인합니다.
---

# omk-status 스킬 실행 지침

사용자가 /omk-status를 실행하면 아래를 수행하세요.

## 상태 확인

다음 명령을 실행합니다:
```bash
omk hooks status
```

출력 내용을 사용자에게 요약하여 보고합니다:
- 전역/로컬 훅 설치 여부
- 등록된 훅 이벤트 목록 (SessionStart, UserPromptSubmit, PostToolUse, SessionEnd)
- 현재 활성 세션 수와 요약

## 추가 정보

드리프트 통계를 보려면:
```bash
omk hooks drift-report
```

훅이 설치되어 있지 않으면 `/omk-setup` 스킬로 설치를 안내하세요.
