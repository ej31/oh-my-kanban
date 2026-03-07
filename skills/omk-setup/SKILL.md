---
name: omk-setup
description: oh-my-kanban 전체 설치 및 설정 마법사. Plane/Linear 연결, Claude Code 훅 설치, 검증을 단계별로 안내합니다.
---

# omk-setup 스킬 실행 지침

사용자가 /omk-setup을 실행하면 아래 단계를 순서대로 수행하세요.

## 1단계: 패키지 설치 확인

`omk --version` 명령을 실행하여 oh-my-kanban이 설치되어 있는지 확인합니다.
설치되어 있지 않으면 `pip install oh-my-kanban` 또는 `pipx install oh-my-kanban`을 안내합니다.

## 2단계: 서비스 선택

사용자에게 어떤 프로젝트 관리 도구를 사용하는지 물어보세요:
- Plane (self-hosted 또는 plane.so 클라우드)
- Linear

## 3단계: 서비스별 설정

### Plane 설정
다음 명령을 순서대로 실행합니다:
```bash
omk config set base_url <PLANE_URL>
omk config set api_key <API_KEY>
omk config set workspace_slug <WORKSPACE>
omk config set project_id <PROJECT_ID>
```
환경변수 방식: `PLANE_BASE_URL`, `PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG`, `PLANE_PROJECT_ID`

### Linear 설정
다음 명령을 순서대로 실행합니다:
```bash
omk config set linear_api_key <LINEAR_API_KEY>
omk config set linear_team_id <TEAM_ID>
```
환경변수 방식: `LINEAR_API_KEY`, `LINEAR_TEAM_ID`

## 4단계: Claude Code 훅 설치

다음 명령을 실행합니다:
```bash
omk hooks install
```

전역 설치(권장): `omk hooks install`
프로젝트별 설치: `omk hooks install --local`

이 명령은:
- Claude Code settings.json에 4가지 훅(SessionStart, UserPromptSubmit, PostToolUse, SessionEnd)을 등록합니다
- 플러그인 파일을 ~/.claude/plugins/cache/omk/oh-my-kanban/<version>/에 복사합니다
- 세션 드리프트 감지, 파일 추적, WI 연동이 자동으로 활성화됩니다

## 5단계: 설치 검증

다음 명령으로 설치 상태를 확인합니다:
```bash
omk hooks status
```

## 완료

설치가 완료되면:
- 다음 Claude Code 세션부터 세션 자동 추적이 시작됩니다
- 범위 이탈(drift) 시 경고가 주입됩니다
- 파일 수정 이력이 자동으로 기록됩니다
- `omk hooks drift-report`로 드리프트 통계를 확인할 수 있습니다

비활성화가 필요하면 `/omk-off` 스킬을 사용하세요.
