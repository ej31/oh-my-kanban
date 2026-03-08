---
name: omk-snapshot
description: 현재 세션 상태의 스냅샷을 저장하거나 저장된 스냅샷을 조회합니다.
---

# omk snapshot — 현재 세션 스냅샷 저장/조회

현재 세션 상태의 스냅샷을 저장하거나 저장된 스냅샷을 조회합니다.

## 하위 명령

### omk snapshot save [메모]

현재 세션 상태를 스냅샷으로 저장합니다.

```bash
omk snapshot save "OAuth 리팩토링 완료 직전"
omk snapshot save  # 메모 없이 타임스탬프로 자동 명명
```

**실행 단계**:

1. 현재 세션 JSON 파일 읽기 (`~/.claude/oh-my-kanban/sessions/{session_id}.json`)
2. 스냅샷 파일로 복사: `~/.claude/oh-my-kanban/snapshots/{session_id}_{timestamp}.json`
3. 메모가 있으면 스냅샷 파일에 `snapshot_note` 필드 추가
4. 출력:

```text
[omk] 스냅샷 저장됨: omk-snap-2026-03-08T14:30:00
  파일: ~/.claude/oh-my-kanban/snapshots/{session_id}_20260308T143000.json
  목표: {현재 scope.summary}
  수정 파일: {len(files_touched)}개
```

### omk snapshot list

저장된 스냅샷 목록을 조회합니다.

**실행 단계**:

1. `~/.claude/oh-my-kanban/snapshots/` 디렉토리 조회
2. 현재 세션 ID와 일치하는 스냅샷 필터링
3. 최신순 정렬 후 출력:

```text
[omk] 저장된 스냅샷 목록:
  1. omk-snap-2026-03-08T14:30:00 — "OAuth 리팩토링 완료 직전"
  2. omk-snap-2026-03-08T12:00:00 — (메모 없음)
```

### omk snapshot restore <스냅샷_ID>

스냅샷을 현재 세션에 복원합니다.

```bash
omk snapshot restore omk-snap-2026-03-08T14:30:00
```

**주의**: 복원은 현재 세션 상태를 **덮어씁니다**. 반드시 사용자 확인 후 진행.

**실행 단계**:

1. 스냅샷 파일 확인
2. 사용자에게 확인: "현재 세션 상태를 스냅샷으로 복원합니다. 계속하시겠습니까?"
3. 확인 시: 세션 파일 복원 (`session_id` 필드는 유지, 나머지 덮어쓰기)
4. 출력:

```text
[omk] 스냅샷 복원됨.
  목표: {복원된 scope.summary}
  수정 파일: {len(files_touched)}개
```

## 주의사항

- 스냅샷 디렉토리가 없으면 자동 생성
- 스냅샷 파일은 원본 세션 JSON과 동일한 형식
- restore 명령은 반드시 사용자 확인 필요 (되돌릴 수 없음)
