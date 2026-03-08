# 스냅샷 (Snapshot)

세션 상태를 특정 시점에 저장하고 나중에 복원할 수 있습니다.

## 개요

스냅샷은 세션의 현재 상태(범위, 통계, Work Item 연결 정보, 타임라인)를 JSON 파일로 저장합니다. 중요한 작업 전후에 스냅샷을 남기면 필요할 때 이전 상태로 돌아갈 수 있습니다.

## CLI 명령

### 스냅샷 저장

```bash
# 최근 활성 세션을 스냅샷으로 저장
omk hooks snapshot save

# 특정 세션 지정
omk hooks snapshot save --session-id abc12345
```

### 스냅샷 목록 조회

```bash
omk hooks snapshot list
```

출력 예시:

```
=== 스냅샷 목록 ===
  abc12345_20260101T100000  세션: abc12345...  OAuth 리팩토링
  def67890_20260101T090000  세션: def67890...  API 엔드포인트 추가
```

### 스냅샷 복원

```bash
# 복원 (활성 세션이 있으면 경고)
omk hooks snapshot restore abc12345_20260101T100000

# 강제 복원
omk hooks snapshot restore abc12345_20260101T100000 --force
```

## 스냅샷 파일 구조

스냅샷은 `~/.config/oh-my-kanban/snapshots/` 디렉토리에 저장됩니다.

파일명 형식: `{session_id_prefix}_{timestamp}.json`

```json
{
  "session_id": "abc12345-...",
  "status": "active",
  "scope": {
    "summary": "OAuth 리팩토링",
    "topics": ["auth", "oauth"]
  },
  "stats": { ... },
  "timeline": [ ... ],
  "snapshot_version": 1,
  "snapshot_created_at": "2026-01-01T10:00:00+00:00"
}
```

## 주의사항

- 스냅샷 파일은 소유자만 읽기/쓰기 가능합니다 (0o600).
- API 키나 민감 정보는 스냅샷에 포함되지 않습니다.
- 활성 세션이 있는 상태에서 복원하면 충돌할 수 있으므로 `--force` 옵션을 사용하세요.
- 스냅샷은 수동 삭제하기 전까지 유지됩니다.
