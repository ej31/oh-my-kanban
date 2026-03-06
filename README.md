# oh-my-kanban | 오마이칸반

> Multi-platform project management CLI — built for AI agents first, humans second.

[![PyPI version](https://badge.fury.io/py/oh-my-kanban.svg)](https://pypi.org/project/oh-my-kanban/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-ej31%2Foh--my--kanban-black)](https://github.com/ej31/oh-my-kanban)

## Why oh-my-kanban?

AI 에이전트 중심의 프로젝트 관리 CLI입니다.

- **Zero-interaction mode** — 환경변수만으로 완전 자동화
- **Machine-readable output** — JSON 형식으로 에이전트 파이프라인 연동
- **Full Plane CRUD** — work items, cycles, modules, intake, pages, users, states, labels 등 완전 지원
- **Multi-workspace support** — 프로필 기반 복수 워크스페이스 관리
- **Self-hosted friendly** — Plane CE(무료 버전) 기준 개발

## Installation / 설치

### PyPI

```bash
pip install oh-my-kanban
```

### From Source

```bash
git clone https://github.com/ej31/oh-my-kanban.git
cd oh-my-kanban
pip install -e .
```

## Quick Start / 빠른 시작

### 1단계: 설정 초기화 (대화형)

```bash
omk config init
```

다음 정보를 입력합니다:

- **서버 종류**: plane.so 클라우드 또는 self-hosted
- **API 키**: [API 토큰 발급](https://app.plane.so/profile/api-tokens/)
- **워크스페이스 슬러그**: URL 또는 직접 입력

### 2단계: 에이전트 모드 (환경변수 자동화)

사람이 개입하지 않고 에이전트가 자동으로 처리하려면:

```bash
export PLANE_API_KEY="pl_xxxxxxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_BASE_URL="https://api.plane.so"  # 또는 self-hosted URL

# 환경변수만으로 전체 작업 가능
omk plane work-item list -o json
omk plane cycle create --name "Sprint 1" --start-date "2024-03-06" --end-date "2024-03-20"
omk plane work-item create --name "Fix login bug" --state-id "..." --project "..."
```

### 3단계: 사람이 사용 (대화형)

```bash
# 기본 프로필 사용
omk config show
omk plane work-item list

# 특정 프로필 사용
omk --profile production plane work-item list -o table
```

## Configuration / 설정

### 설정 파일 위치

```
~/.config/oh-my-kanban/config.toml
```

### 프로필 기반 다중 워크스페이스

```toml
[default]
base_url = "https://api.plane.so"
api_key = "pl_xxxxx"
workspace_slug = "my-workspace"
output = "table"

[production]
base_url = "https://plane.example.com"
api_key = "pl_yyyyy"
workspace_slug = "prod-workspace"
output = "json"
```

사용:

```bash
omk --profile production plane work-item list
```

### 환경변수 우선순위

명령행 옵션 > 환경변수 > 설정 파일 > 기본값

```bash
# 환경변수로 덮어쓰기
PLANE_API_KEY="pl_xxxxxx" omk config show
PLANE_WORKSPACE_SLUG="override-ws" omk plane work-item list
```

### 설정 관리 커맨드

```bash
# 설정 초기화 (대화형)
omk config init

# 현재 설정 확인 (API 키는 마스킹)
omk config show

# 특정 값 변경
omk config set workspace_slug my-new-workspace
omk config set output json

# 프로필 목록
omk config profile list

# 기본 프로필 변경
omk config profile use production
```

## Command Reference / 명령어 레퍼런스

### 글로벌 옵션

```bash
omk [OPTIONS] PROVIDER [PROVIDER_OPTIONS] COMMAND [ARGS]
```

| 옵션 | 환경변수 | 설명 |
|------|---------|------|
| `--workspace, -w SLUG` | `PLANE_WORKSPACE_SLUG` | 워크스페이스 슬러그 |
| `--project, -p ID` | `PLANE_PROJECT_ID` | 프로젝트 UUID |
| `--output, -o FORMAT` | - | 출력 포맷: `table` \| `json` \| `plain` (기본: `table`) |
| `--profile PROFILE` | `PLANE_PROFILE` | 설정 프로필 (기본: `default`) |
| `--version` | - | 버전 표시 |

### Provider Subgroups

omk는 provider별 서브그룹으로 커맨드를 분리합니다:
- `omk plane` (또는 `omk pl`) — Plane 프로젝트 관리
- `omk github` (또는 `omk gh`) — GitHub 프로젝트 관리 (향후 지원)
- `omk config` — 설정 관리 (provider 독립)

### 커맨드 레퍼런스

#### omk config — 설정 관리 (provider 독립)

```bash
omk config init                              # 대화형 초기 설정
omk config show [--profile PROFILE]          # 현재 설정 확인
omk config set KEY VALUE [--profile PROFILE] # 설정 값 변경
omk config profile list                      # 프로필 목록
omk config profile use NAME                  # 기본 프로필 변경
```

#### omk plane (또는 omk pl) — Plane 프로젝트 관리

##### work-item — 작업 항목

```bash
# 목록 조회
omk plane work-item list [--all] [--per-page N] [--cursor CURSOR] [--priority PRIORITY]

# 상세 조회
omk plane work-item get ITEM_ID_OR_IDENTIFIER

# 생성
omk plane work-item create --name NAME [--state-id STATE] [--priority PRIORITY] [--description DESC] [--assignees USER1,USER2]

# 수정
omk plane work-item update ITEM_ID [--name NAME] [--state-id STATE] [--priority PRIORITY]

# 삭제
omk plane work-item delete ITEM_ID [--force]

# 검색
omk plane work-item search QUERY

# 관계 설정
omk plane work-item relation create ITEM_ID --type TYPE --target TARGET_ITEM_ID
omk plane work-item relation list ITEM_ID
omk plane work-item relation delete ITEM_ID --target TARGET_ITEM_ID
```

##### cycle — 반복 주기

```bash
omk plane cycle list [--all]
omk plane cycle create --name NAME --owned-by USER_ID [--start-date DATE] [--end-date DATE]
omk plane cycle get CYCLE_ID
omk plane cycle update CYCLE_ID [--name NAME] [--start-date DATE] [--end-date DATE]
omk plane cycle delete CYCLE_ID
omk plane cycle list-work-items CYCLE_ID
omk plane cycle add-work-items CYCLE_ID ITEM1 ITEM2 ...
omk plane cycle remove-work-item CYCLE_ID ITEM_ID
```

##### module — 모듈

```bash
omk plane module list [--all]
omk plane module create --name NAME [--status STATUS] [--start-date DATE] [--target-date DATE]
omk plane module get MODULE_ID
omk plane module update MODULE_ID [--name NAME] [--status STATUS]
omk plane module delete MODULE_ID
omk plane module list-work-items MODULE_ID
omk plane module add-work-items MODULE_ID ITEM1 ITEM2 ...
```

##### 기타 커맨드

```bash
omk plane user list                              # 사용자 목록
omk plane project list [--all]                   # 프로젝트 목록
omk plane state list                             # 상태(state) 목록
omk plane label list [--all]                     # 라벨 목록
omk plane label create --name NAME [--color HEX] # 라벨 생성

omk plane milestone list                         # 마일스톤 목록
omk plane epic list                              # 에픽 목록
omk plane page list                              # 페이지 목록
omk plane intake list                            # 요청(Intake) 목록

omk plane workspace list                         # 워크스페이스 정보
omk plane teamspace list                         # 팀스페이스 목록
omk plane initiative list                        # 이니셔티브 목록

omk plane work-item-type list                    # 작업 항목 타입
omk plane work-item-property list --type TYPE_ID # 사용자 정의 속성
```

#### omk github (또는 omk gh) — GitHub 프로젝트 관리 (향후 지원)

```bash
omk github issue list --owner OWNER --repo REPO
omk github project list --owner OWNER
```

**현재 구현 예정입니다.**

## Output Formats / 출력 형식

### Table (기본)

```bash
omk plane work-item list
```

```
ID                                    NAME           PRIORITY  STATE      ASSIGNEES
12345678-90ab-cdef-1234-567890abcdef  Fix login bug  high      In Progress  alice
87654321-abcd-ef12-3456-7890abcdef12  Add dark mode  medium    To Do      bob, charlie
```

### JSON (에이전트 자동화용)

```bash
omk plane work-item list -o json
```

```json
{
  "data": [
    {
      "id": "12345678-90ab-cdef-1234-567890abcdef",
      "name": "Fix login bug",
      "priority": "high",
      "state": "In Progress",
      "assignees": ["alice"],
      "state_id": "state_uuid_1",
      "project_id": "proj_uuid_1"
    }
  ],
  "pagination": {
    "cursor": "next_cursor_token",
    "has_more": true
  }
}
```

### Plain (스크립트 파싱용)

```bash
omk plane work-item list -o plain
```

```
12345678-90ab-cdef-1234-567890abcdef|Fix login bug|high|In Progress|alice
87654321-abcd-ef12-3456-7890abcdef12|Add dark mode|medium|To Do|bob,charlie
```

## Server Compatibility / 서버 호환성

| 기능 | plane.so | Self-hosted CE | 비고 |
|------|----------|----------------|------|
| Work Items | ✅ | ✅ | - |
| Cycles | ✅ | ✅ | - |
| Modules | ✅ | ✅ | - |
| Milestones | ✅ | ✅ | - |
| Pages | ✅ | ✅ | - |
| Intake | ✅ | ✅ | - |
| Custom Properties | ✅ | ⚠️ | CE에서 제한됨 |
| Epics | ✅ | ⚠️ | CE에서 제한됨 |
| Initiatives | ✅ | ✅ | - |

**참고**: 현재 self-hosted Community Edition(무료 버전) 기준으로 개발되었습니다.
Enterprise 전용 기능은 미구현 상태입니다.

## Examples / 예제

### 에이전트 파이프라인: 반복 생성 → 작업 생성 → 할당

```bash
#!/bin/bash

export PLANE_API_KEY="pl_xxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj_uuid"

# 1. 반복 생성
CYCLE_ID=$(omk plane cycle create \
  --name "Sprint 1" \
  --owned-by "$USER_ID" \
  --start-date "2024-03-06" \
  --end-date "2024-03-20" \
  -o json | jq -r '.data.id')

echo "생성된 반복: $CYCLE_ID"

# 2. 작업 생성
ITEM_ID=$(omk plane work-item create \
  --name "Fix critical bug" \
  --priority high \
  --state-id "$STATE_ID" \
  -o json | jq -r '.data.id')

echo "생성된 작업: $ITEM_ID"

# 3. 반복에 작업 추가
omk plane cycle add-work-items "$CYCLE_ID" "$ITEM_ID"

# 4. 사용자에게 할당
omk plane work-item update "$ITEM_ID" --assignees "$ASSIGNEE_USER_ID"

echo "완료!"
```

### 다중 워크스페이스 관리

```bash
# Production 환경에서 작업 조회
omk --profile production plane work-item list

# Development 환경에서 작업 생성
omk --profile development plane work-item create --name "New feature" --priority medium

# 환경별 필터링
omk --profile staging plane work-item search "bug" -o json | jq '.data[] | select(.priority=="urgent")'
```

### 프로젝트 상태 리포트 생성

```bash
#!/bin/bash

export PLANE_WORKSPACE_SLUG="my-workspace"

# JSON 출력으로 리포트 생성
omk plane work-item list --all -o json > report.json

# 상태별 개수 집계
jq '[.data[] | .state] | group_by(.) | map({state: .[0], count: length})' report.json

# 우선순위별 상위 5개 작업
jq '.data | sort_by(.priority) | reverse | .[0:5]' report.json
```

## Roadmap / 로드맵

- [x] **Plane** (plane.so, self-hosted)
  - Note: Developed against **Community Edition (self-hosted, free tier)**. Enterprise-only features are not implemented.
  - Provider subgroup: `omk plane` (또는 `omk pl`)
  - Examples: `omk plane work-item list`, `omk plane cycle create --name "Sprint 1"`, `omk pl work-item search "bug"`
- [ ] **GitHub**
  - Provider subgroup: `omk github` (또는 `omk gh`)
  - Examples: `omk github issue list --owner ej31 --repo my-repo`, `omk github project list --owner ej31`
- [ ] **Linear**
- [ ] **Notion**
- [ ] **Jira**

## Contributing / 개발 참여

### 환경 설정

```bash
git clone https://github.com/ej31/oh-my-kanban.git
cd oh-my-kanban
pip install -e ".[dev]"
```

### 코드 스타일

- Python 3.10+
- Ruff lint rules: E, F, I, UP, B
- Line length: 100

### 테스트

```bash
pytest tests/
```

### Pull Request

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit changes: `git commit -am 'feat: add your feature'`
4. Push to branch: `git push origin feat/your-feature`
5. Open a Pull Request

## License

MIT License - See [LICENSE](LICENSE) for details

## Support

- **Issues**: [GitHub Issues](https://github.com/ej31/oh-my-kanban/issues)
- **Documentation**: [GitHub Wiki](https://github.com/ej31/oh-my-kanban/wiki)
- **API Reference**: [Plane API Docs](https://docs.plane.so/api-reference)
