---
name: omk-doctor
description: oh-my-kanban 설정·API·훅을 통합 진단하고 복구 방법을 안내합니다.
---

# omk-doctor 스킬 실행 지침

사용자가 `/omk-doctor`를 실행하면 아래 순서로 진단을 수행하세요.

## Step 1: API 및 설정 진단

다음 명령을 실행합니다:

```bash
omk doctor
```

출력 예시:
```
oh-my-kanban 진단을 시작합니다...

  ✓ [PASS] 설정 파일: 설정 로드 완료 (프로필: default)
  ✓ [PASS] plane-sdk 버전: plane-sdk 0.3.1
  ✓ [PASS] Plane API 연결: 인증 성공
  - [SKIP] Linear API 연결: Linear API 미설정
```

**omk 명령이 없는 경우**: `pip install oh-my-kanban` 후 `omk hooks install`을 실행해야 한다고 안내합니다.

## Step 2: 훅 설치 진단

다음 명령을 실행합니다:

```bash
omk hooks status
```

훅 설치 여부(전역/프로젝트/개인로컬)와 활성 세션 목록을 확인합니다.

## Step 3: 종합 리포트 출력

두 명령의 출력을 종합해 아래 형식으로 리포트를 출력합니다:

```
## omk-doctor 진단 리포트

| 항목 | 상태 | 내용 |
|------|------|------|
| 설정 파일 | OK | 설정 로드 완료 (프로필: default) |
| plane-sdk | OK | plane-sdk 0.3.1 |
| Plane API | OK | 인증 성공 |
| Linear API | WARN | Linear API 미설정 (사용하지 않으면 정상) |
| 훅 설치 | OK | 전역 훅 활성 (4개 이벤트) |
| 활성 세션 | OK | 1개 |
```

상태 매핑:
- `[PASS]` → **OK**
- `[SKIP]` → **WARN** (미설정이지만 오류는 아님)
- `[FAIL]` → **CRITICAL**
- 훅 미설치 → **CRITICAL**

## Step 4: 복구 안내

WARN 또는 CRITICAL 항목 발견 시 아래 복구 방법을 안내합니다:

| 문제 | 복구 방법 |
|------|----------|
| 설정 파일 없음 / 파싱 오류 | `/omk-setup` 스킬 실행 |
| Plane API 키 인증 실패 (401) | Plane에서 새 API 토큰 발급 후 `/omk-setup` 재실행 |
| Plane 서버 연결 실패 | `base_url` 확인, 네트워크 상태 점검 |
| plane-sdk 버전 호환 오류 | `pip install --upgrade oh-my-kanban` |
| Linear API 키 오류 | Linear Settings > API에서 새 토큰 발급 후 `/omk-setup` 재실행 |
| 훅 미설치 | `omk hooks install` 또는 `/omk-setup` 스킬 재실행 |

모든 항목 OK이면: "모든 진단이 통과했습니다." 출력합니다.
