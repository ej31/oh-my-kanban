---
name: omk-scope-expand
description: 현재 세션의 작업 범위를 명시적으로 확장합니다. 세션 drift 오탐을 방지하기 위해 새로운 작업 주제를 현재 세션 범위에 추가할 때 사용합니다.
---

현재 세션의 작업 범위를 확장해주세요. 예상치 못한 관련 작업이 추가되어 drift 경고가 발생하거나, 명시적으로 범위를 선언하고 싶을 때 사용합니다.

## Phase 2 이후 (정식 명령)

```bash
omk hooks expand-scope --topic "<새로운 작업 주제>"
```

> **참고**: 위 명령은 Phase 2에서 활성화됩니다.

---

## 현재 사용 가능한 대안 방법

**1단계: 세션 ID 확인**

```bash
omk hooks status
```

출력에서 `session_id` 값을 복사합니다.

**2단계: 세션 파일의 `expanded_topics`에 주제 추가**

```bash
# 세션 파일 경로
~/.config/oh-my-kanban/sessions/<SESSION_ID>.json
```

파일을 열어 `scope.expanded_topics` 배열에 새 주제를 추가합니다:

```json
{
  "scope": {
    "expanded_topics": ["기존 주제", "추가할 새 작업 주제"]
  }
}
```

**3단계: 변경 확인**

```bash
omk hooks status
```

`expanded_topics`에 추가한 주제가 표시되면 완료입니다.
이후 해당 주제 관련 작업은 drift로 감지되지 않습니다.

**현재 세션 범위 전체 확인**

```bash
omk hooks status
```
