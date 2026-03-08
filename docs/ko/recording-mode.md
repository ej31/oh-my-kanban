# 기록 모드 (Recording Mode)

oh-my-kanban은 세션 종료 시 Plane Work Item에 댓글을 자동으로 기록합니다. `upload_level` 설정으로 기록 방식을 제어할 수 있습니다.

## 업로드 레벨

| 레벨 | 설명 |
|------|------|
| `none` | 댓글을 업로드하지 않습니다. 로컬 세션 파일만 저장됩니다. |
| `metadata` | (기본값) 통계, 수정 파일 목록, 범위 요약만 기록합니다. 프라이버시를 보호하면서 핵심 정보를 공유합니다. |
| `full` | 타임라인 이벤트를 포함한 상세 댓글을 업로드합니다. 모든 세션 활동이 기록됩니다. |

## 설정 방법

### CLI로 설정

```bash
omk config set upload_level metadata
omk config set upload_level full
omk config set upload_level none
```

### 설정 파일 직접 편집

`~/.config/oh-my-kanban/config.toml`:

```toml
[default]
upload_level = "metadata"
```

### 환경변수

```bash
export OMK_UPLOAD_LEVEL=full
```

### 프리셋 사용

```bash
# 최소 설정 (업로드 안 함)
omk config preset apply minimal

# 상세 기록
omk config preset apply verbose
```

## 모드별 댓글 예시

### metadata 모드

```markdown
## omk 세션 종료

**목표**: OAuth 리팩토링

**통계**
- 요청 횟수: 12회
- 수정 파일: 5개
- 범위 이탈 경고: 1회

**수정된 파일**
- `src/auth/oauth.py`
- `tests/test_oauth.py`
```

### full 모드

metadata 모드의 내용에 추가로 타임라인 이벤트가 포함됩니다.

```markdown
**타임라인**
- `2026-01-01T10:00:00` [scope_init] 세션 시작
- `2026-01-01T10:05:00` [prompt] OAuth 토큰 갱신 구현
- `2026-01-01T10:15:00` [drift_detected] 범위 이탈 감지
- `2026-01-01T10:30:00` [prompt] 세션 정상 종료
```

## 주의사항

- `none` 모드에서도 세션 상태는 로컬에 저장됩니다. Plane API 호출만 생략됩니다.
- 잘못된 `upload_level` 값은 자동으로 `metadata`로 대체됩니다.
- `upload_level` 변경은 다음 세션부터 적용됩니다.
