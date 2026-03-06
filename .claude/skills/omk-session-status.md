---
name: omk-session-status
description: 현재 oh-my-kanban 세션 추적 상태를 확인합니다. 활성 세션 ID, 목표, 연결된 Plane Work Item, 진행 통계를 한눈에 표시합니다.
---

현재 oh-my-kanban 세션 추적 상태를 확인해주세요.

다음 명령을 실행하세요:

```bash
omk hooks status
```

실행 후 다음 정보가 표시됩니다:
- 현재 활성 세션 ID
- 세션 시작 시각 및 경과 시간
- 연결된 Plane Work Item 링크 (있는 경우)
- 세션 목표 및 범위
- 지금까지 감지된 작업 수 / 변경 파일 수
- 세션 상태 (active / opted_out / ended)

세션이 특정 Work Item에 연결되어 있지 않다면 `/omk-link-work-item`을 사용하여 수동으로 연결할 수 있습니다.
