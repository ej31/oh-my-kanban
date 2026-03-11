# oh-my-kanban | 오마이칸반

[한국어](README_kr.md) | [ENGLISH](README_en.md)

> Plane과 Linear를 위한 자동화 친화적 CLI.

[![PyPI version](https://badge.fury.io/py/oh-my-kanban.svg)](https://pypi.org/project/oh-my-kanban/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-ej31%2Foh--my--kanban-black)](https://github.com/ej31/oh-my-kanban)

## 개요

oh-my-kanban은 스크립트, 에이전트 워크플로우, 일반적인 터미널 작업에서 Plane과 Linear를 다루기 위한 Python CLI입니다.

- `omk plane ...`, `omk linear ...` 형태의 단일 명령 표면
- `table`, `json`, `plain` 출력 모드
- Plane 프로필 기반 설정과 두 프로바이더용 환경변수 오버라이드
- Self-hosted Plane 지원
- 현재 저장소 범위는 Plane과 Linear로 한정

## 지원 프로바이더

- **Plane**
  - 작업 항목, 사이클, 모듈, 마일스톤, 에픽, 페이지, 인테이크
  - 프로젝트, 상태, 레이블, 팀스페이스, 고객, 워크스페이스/사용자 도우미
  - 추가 그룹: `agent-run`, `sticky`, `work-item-type`, `work-item-property`
- **Linear**
  - 현재 사용자 조회, 팀, 이슈, 이슈 댓글
  - 상태, 레이블, 프로젝트, 사이클

## 아키텍처

- 런타임은 하나의 `omk`로 유지
- provider별 실제 구현은 `src/oh_my_kanban/providers/<name>/` 아래에 위치
- 기존 `commands/*`, `commands/linear/*`, `context.py`, provider별 root 모듈은 호환용 래퍼만 유지
- 새 provider-specific 코드는 compatibility wrapper가 아니라 `providers/<name>/` 아래에 추가

## 설치

### PyPI

```bash
pip install oh-my-kanban
```

### 소스에서 설치

```bash
git clone https://github.com/ej31/oh-my-kanban.git
cd oh-my-kanban
pip install -e ".[dev]"
```

### 대화형 설치 위저드

```bash
npx @oh-my-kanban/setup

# 로컬 개발
cd installer
npm install
npm run start
```

## 빠른 시작

### 1. Plane 설정

`config init`은 provider-aware 대화형 설정입니다. Plane, Linear, 또는 둘 다 한 프로필에 설정할 수 있습니다.

```bash
omk config init
omk config set plane.project_id YOUR_PROJECT_UUID
```

비대화형으로 설정하려면:

```bash
export PLANE_BASE_URL="https://api.plane.so"
export PLANE_API_KEY="pl_xxxxxxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="your-project-id"
```

### 2. Linear 설정

Linear 설정을 config 파일에 저장할 수 있습니다.

```bash
omk config set linear.api_key lin_api_xxxxxxxxxx
omk config set linear.team_id your-linear-team-id
```

또는 환경변수로 줄 수 있습니다.

```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxx"
export LINEAR_TEAM_ID="your-linear-team-id"
```

### 3. CLI 사용해보기

```bash
omk config show
omk plane work-item list
omk linear me
omk linear issue list --team YOUR_LINEAR_TEAM_ID
```

## 설정

### 설정 파일

```text
~/.config/oh-my-kanban/config.toml
```

### 예시

```toml
[default]
output = "table"

[default.plane]
base_url = "https://api.plane.so"
api_key = "pl_xxxxx"
workspace_slug = "my-workspace"
project_id = "plane-project-uuid"

[default.linear]
api_key = "lin_api_xxxxx"
team_id = "team-id"

[production]
output = "json"

[production.plane]
base_url = "https://plane.example.com"
api_key = "pl_yyyyy"
workspace_slug = "prod-workspace"
project_id = "prod-project-uuid"

[production.linear]
api_key = "lin_api_prod"
team_id = "prod-team-id"
```

### 우선순위

명령행 옵션 > 환경변수 > 설정 파일 > 기본값

### 환경변수

| 변수 | 용도 |
|---|---|
| `PLANE_BASE_URL` | Plane API base URL |
| `PLANE_API_KEY` | Plane API key |
| `PLANE_WORKSPACE_SLUG` | Plane workspace slug |
| `PLANE_PROJECT_ID` | 기본 Plane 프로젝트 UUID |
| `LINEAR_API_KEY` | Linear API key |
| `LINEAR_TEAM_ID` | 기본 Linear 팀 ID |
| `PLANE_PROFILE` | 활성 설정 프로필 |

### 설정 명령

```bash
omk config init
omk config show [--profile PROFILE]
omk config set plane.base_url VALUE
omk config set plane.api_key VALUE
omk config set plane.workspace_slug VALUE
omk config set plane.project_id VALUE
omk config set output VALUE
omk config set linear.api_key VALUE
omk config set linear.team_id VALUE
omk config migrate [--profile PROFILE]
omk config migrate --all-profiles
omk config profile list
omk config profile use NAME
```

## 명령 개요

### 글로벌 형태

```bash
omk [OPTIONS] COMMAND [ARGS]...
```

| 옵션 | 환경변수 | 설명 |
|---|---|---|
| `--output`, `-o` | - | 출력 포맷: `table`, `json`, `plain` |
| `--profile` | `PLANE_PROFILE` | 설정 프로필 |
| `--version` | - | 버전 표시 |

### 최상위 명령

- `omk config` - 프로바이더 독립 설정 관리
- `omk plane` / `omk pl` - Plane 명령
- `omk linear` / `omk ln` - Linear 명령

Plane 전용 컨텍스트 옵션은 provider 그룹 아래에 있습니다.

```bash
omk plane --workspace MY_WORKSPACE --project PROJECT_UUID work-item list
```

### Plane 명령

전체 목록은 `omk plane --help`를 보세요. 자주 쓰는 진입점:

```bash
omk plane user me
omk plane project list [--all]
omk plane state list
omk plane label list [--all]

omk plane work-item list [--all] [--per-page N] [--priority PRIORITY]
omk plane work-item get ITEM_ID_OR_IDENTIFIER
omk plane work-item create --name NAME [--state STATE_ID] [--priority PRIORITY]
omk plane work-item update ITEM_ID [--name NAME] [--state STATE_ID]

omk plane cycle list [--all]
omk plane cycle create --name NAME [--start-date DATE] [--end-date DATE]
omk plane cycle add-items CYCLE_ID --items ITEM1 --items ITEM2

omk plane module list [--all]
omk plane milestone list
omk plane epic list
omk plane page list
omk plane intake list
omk plane workspace members
omk plane teamspace list
omk plane customer list
omk plane sticky list
omk plane agent-run list
```

### Linear 명령

전체 목록은 `omk linear --help`를 보세요. 자주 쓰는 진입점:

```bash
omk linear me
omk linear team list
omk linear team get TEAM_ID

omk linear issue list [--team TEAM_ID] [--first N]
omk linear issue get ISSUE_ID_OR_KEY
omk linear issue create --title TITLE --team TEAM_ID [--priority 0-4] [--state STATE_ID]
omk linear issue update ISSUE_ID [--title TITLE] [--priority 0-4] [--state STATE_ID]
omk linear issue delete ISSUE_ID

omk linear issue comment list ISSUE_ID
omk linear issue comment create ISSUE_ID --body "Comment text"

omk linear state list [--team TEAM_ID]
omk linear label list [--team TEAM_ID]
omk linear project list [--first N]
omk linear cycle list [--team TEAM_ID]
```

## 출력 형식

`--output`은 글로벌 옵션이라 프로바이더 명령 앞에 둬야 합니다.

```bash
omk -o table plane work-item list
omk -o json plane work-item list
omk -o plain linear issue list --team TEAM_ID
```

## 예제

### Plane 워크플로우

```bash
export PLANE_API_KEY="pl_xxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj_uuid"

CYCLE_ID=$(omk -o json plane cycle create \
  --name "Sprint 1" \
  --start-date "2024-03-06" \
  --end-date "2024-03-20" | jq -r '.data.id')

STATE_ID="state_uuid"

ITEM_ID=$(omk -o json plane work-item create \
  --name "중요 버그 수정" \
  --priority high \
  --state "$STATE_ID" | jq -r '.data.id')

omk plane cycle add-items "$CYCLE_ID" --items "$ITEM_ID"
omk plane work-item update "$ITEM_ID" --assignee "user_uuid"
```

### Linear 워크플로우

```bash
export LINEAR_API_KEY="lin_api_xxxxxx"
export LINEAR_TEAM_ID="team_uuid"

omk linear team list
omk -o json linear issue list --team "$LINEAR_TEAM_ID"

omk linear issue create \
  --title "로그인 버그 수정" \
  --team "$LINEAR_TEAM_ID" \
  --priority 2

omk linear issue comment create ISSUE_ID --body "조사 시작."
```

## 프로바이더 참고사항

### Plane

- Plane Community Edition과 plane.so cloud 기준으로 개발
- `PLANE_BASE_URL`로 self-hosted 배포 지원
- 일부 Plane enterprise 전용 영역은 서버 환경에 따라 제한될 수 있음

### Linear

- `httpx` 기반 Linear GraphQL API 사용
- `LINEAR_API_KEY` 필수
- `LINEAR_TEAM_ID`는 선택이지만 기본 팀 설정에 유용

## 개발

```bash
uv run pytest
uv run python -m oh_my_kanban --help
```

## 지원

- **이슈**: [GitHub Issues](https://github.com/ej31/oh-my-kanban/issues)
- **Plane API 문서**: [docs.plane.so/api-reference](https://docs.plane.so/api-reference)
- **Linear API 문서**: [developers.linear.app](https://developers.linear.app/)

## 라이선스

MIT License - 자세한 내용은 [../LICENSE](../LICENSE)를 보세요.
