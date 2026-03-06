---
name: omk-link-work-item
description: 현재 세션을 특정 Plane Work Item에 수동으로 연결합니다. 자동 연결이 실패했거나 기존 Work Item에 연결하고 싶을 때 사용합니다.
---

현재 oh-my-kanban 세션을 특정 Plane Work Item에 수동으로 연결해주세요.

## Phase 2 이후 (정식 명령)

```bash
omk hooks link --work-item-id <WORK_ITEM_ID>
```

> **참고**: 위 명령은 Phase 2에서 활성화됩니다.

---

## 현재 사용 가능한 대안 방법

**1단계: 세션 ID 확인**

```bash
omk hooks status
```

출력에서 `session_id` 값을 복사합니다 (예: `a1b2c3d4-...`).

**2단계: 세션 파일 직접 수정**

```bash
# 세션 파일 경로
~/.config/oh-my-kanban/sessions/<SESSION_ID>.json
```

파일을 열어 `plane_context.work_item_ids` 배열에 Work Item ID를 추가합니다:

```json
{
  "plane_context": {
    "project_id": "기존값 유지",
    "work_item_ids": ["추가할-work-item-id"],
    "module_id": null
  }
}
```

**3단계: 변경 확인**

```bash
omk hooks status
```

세션 상태에 Work Item ID가 표시되면 연결 완료입니다. 이후 세션 종료 시 해당 Work Item에 작업 요약이 댓글로 추가됩니다.
