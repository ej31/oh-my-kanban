# oh-my-kanban | 오마이칸반

[한국어](README_kr.md) | [ENGLISH](README_en.md)

> AI 에이전트 중심의 멀티 플랫폼 프로젝트 관리 CLI — 에이전트를 먼저, 사람은 나중에.

[![PyPI version](https://badge.fury.io/py/oh-my-kanban.svg)](https://pypi.org/project/oh-my-kanban/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-ej31%2Foh--my--kanban-black)](https://github.com/ej31/oh-my-kanban)

---

## 왜 oh-my-kanban인가?

oh-my-kanban은 **AI 에이전트의 자동 워크플로우**를 염두에 두고 설계된 경량 CLI입니다.

- **상호 작용 없는 모드** — 환경변수 설정만으로 완전 자동화
- **기계 친화적 출력** — JSON 형식으로 에이전트 파이프라인 연동
- **폭넓은 Plane 지원** — work items, cycles, modules, milestones, intake, initiatives, teamspaces, stickies 등 (CE 무료 플랜 우선 구현)
- **Linear 지원** — GraphQL 기반으로 이슈, 팀, 사이클, 프로젝트, 상태, 레이블 관리
- **다중 워크스페이스 관리** — 프로필 기반으로 여러 환경 동시 관리
- **Self-Hosted 친화적** — Plane Community Edition(무료) 기준 개발

---

## 설치

### PyPI에서 설치

```bash
pip install oh-my-kanban
```

### 소스에서 설치

```bash
git clone https://github.com/ej31/oh-my-kanban.git
cd oh-my-kanban
pip install -e .
```

---

## 빠른 시작

### 1단계: 설정 초기화 (대화형)

```bash
omk config init
```

다음 정보를 입력합니다:

- **서버 종류**: plane.so 클라우드 또는 자체 호스팅(Self-Hosted)
- **API 키**: [API 토큰 발급](https://app.plane.so/profile/api-tokens/)
- **워크스페이스 슬러그**: URL에서 추출하거나 직접 입력

### 2단계: 에이전트 모드 (환경변수 기반 자동화)

Plane 사용:

```bash
export PLANE_API_KEY="pl_xxxxxxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="your-project-id"  # 프로젝트 범위 명령어에 필요
export PLANE_BASE_URL="https://api.plane.so"  # 또는 자체 호스팅 URL

omk plane work-item list -o json
omk plane cycle create --name "Sprint 1" --start-date "2024-03-06" --end-date "2024-03-20"
omk plane work-item create --name "로그인 버그 수정" --state-id "..."
```

Linear 사용:

```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxx"
export LINEAR_TEAM_ID="your-team-id"  # 기본 팀 ID (선택)

omk linear issue list -o json
omk linear issue create --title "버그 수정" --team TEAM_ID
```

### 3단계: 사람이 사용 (대화형)

```bash
# 기본 프로필 사용
omk config show
omk plane work-item list

# 특정 프로필 사용
omk --profile production plane work-item list -o table
```

---

## 설정

### 설정 파일 위치

```text
~/.config/oh-my-kanban/config.toml
```

### 프로필 기반 다중 워크스페이스

설정 파일에서 여러 워크스페이스(프로필)를 정의하여 관리할 수 있습니다:

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

프로필 사용:

```bash
omk --profile production plane work-item list
```

### 환경변수 우선순위

설정의 우선순위는 다음 순서대로 적용됩니다:

**명령행 옵션 > 환경변수 > 설정 파일 > 기본값**

```bash
# 환경변수로 덮어쓰기
PLANE_API_KEY="pl_xxxxxx" omk config show
PLANE_WORKSPACE_SLUG="override-ws" omk plane work-item list
```

### 설정 관리 커맨드

```bash
# 설정 초기화 (대화형)
omk config init

# 현재 설정 확인 (API 키는 마스킹됨)
omk config show

# 특정 값 변경
omk config set workspace_slug my-new-workspace
omk config set output json

# 프로필 목록 조회
omk config profile list

# 기본 프로필 변경
omk config profile use production
```

---

## 명령어 레퍼런스

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

### 프로바이더 서브그룹

- `omk plane` (또는 `omk pl`) — Plane 프로젝트 관리
- `omk linear` (또는 `omk ln`) — Linear 프로젝트 관리
- `omk github` (또는 `omk gh`) — GitHub 프로젝트 관리 (준비 중)
- `omk config` — 설정 관리 (프로바이더 독립)

### omk config — 설정 관리

설정 프로필과 워크스페이스 정보를 관리합니다.

```bash
omk config init                              # 대화형 초기 설정
omk config show [--profile PROFILE]          # 현재 설정 확인
omk config set KEY VALUE [--profile PROFILE] # 설정 값 변경
omk config profile list                      # 프로필 목록
omk config profile use NAME                  # 기본 프로필 변경
```

### omk plane (또는 omk pl) — Plane 프로젝트 관리

#### work-item — 작업 항목 관리

```bash
# 목록 조회
omk plane work-item list [--all] [--per-page N] [--cursor CURSOR] [--priority PRIORITY]

# 상세 조회
omk plane work-item get ITEM_ID_OR_IDENTIFIER

# 생성
omk plane work-item create --name NAME [--state STATE_ID] [--priority PRIORITY] [--description DESC] [--assignee USER_ID]

# 수정
omk plane work-item update ITEM_ID [--name NAME] [--state STATE_ID] [--priority PRIORITY]

# 삭제
omk plane work-item delete ITEM_ID [--force]

# 검색
omk plane work-item search --query QUERY

# 관계 설정
omk plane work-item relation list ITEM_ID
omk plane work-item relation create ITEM_ID --related-work-item ITEM_ID2 --relation-type blocking
omk plane work-item relation delete ITEM_ID --related-work-item ITEM_ID2

# 댓글
omk plane work-item comment list ITEM_ID
omk plane work-item comment create ITEM_ID --body "훌륭한 작업입니다!"
omk plane work-item comment update ITEM_ID COMMENT_ID --body "수정된 댓글"
omk plane work-item comment delete ITEM_ID COMMENT_ID

# 링크
omk plane work-item link list ITEM_ID
omk plane work-item link create ITEM_ID --url "https://example.com/doc"
omk plane work-item link delete ITEM_ID LINK_ID

# 활동 내역 (읽기 전용)
omk plane work-item activity list ITEM_ID

# 작업 로그 (plane.so 전용)
omk plane work-item worklog list ITEM_ID
omk plane work-item worklog create ITEM_ID --duration 120 --description "프론트엔드 리팩터링"
omk plane work-item worklog update ITEM_ID WORKLOG_ID --duration 90
omk plane work-item worklog delete ITEM_ID WORKLOG_ID
```

#### cycle — 반복(스프린트) 관리

```bash
omk plane cycle list [--all]
omk plane cycle create --name NAME [--start-date DATE] [--end-date DATE]
omk plane cycle get CYCLE_ID
omk plane cycle update CYCLE_ID [--name NAME] [--start-date DATE] [--end-date DATE]
omk plane cycle delete CYCLE_ID
omk plane cycle archive CYCLE_ID
omk plane cycle unarchive CYCLE_ID
omk plane cycle archived                        # 아카이브된 사이클 목록
omk plane cycle items CYCLE_ID                  # 사이클의 작업 항목 목록
omk plane cycle add-items CYCLE_ID --items ITEM1 --items ITEM2
omk plane cycle remove-item CYCLE_ID ITEM_ID
omk plane cycle transfer CYCLE_ID --target TARGET_CYCLE_ID
```

#### module — 모듈 관리

```bash
omk plane module list [--all]
omk plane module create --name NAME [--status STATUS] [--start-date DATE] [--target-date DATE]
omk plane module get MODULE_ID
omk plane module update MODULE_ID [--name NAME] [--status STATUS]
omk plane module delete MODULE_ID
omk plane module archive MODULE_ID
omk plane module unarchive MODULE_ID
omk plane module items MODULE_ID                # 모듈의 작업 항목 목록
omk plane module add-items MODULE_ID --items ITEM1 --items ITEM2
omk plane module remove-item MODULE_ID ITEM_ID
```

#### 기타 Plane 커맨드

```bash
omk plane user me                                    # 현재 사용자 정보
omk plane project list [--all]                       # 프로젝트 목록
omk plane state list                                 # 상태(state) 목록
omk plane label list [--all]                         # 라벨 목록
omk plane label create --name NAME [--color HEX]     # 라벨 생성

omk plane milestone list                             # 마일스톤 목록
omk plane epic list                                  # 에픽 목록 (list·get만)
omk plane epic get EPIC_ID                           # 에픽 상세 조회
omk plane page get PAGE_ID                           # 페이지 조회 (get·create만)
omk plane page create --name NAME [--workspace]      # 페이지 생성 (프로젝트 또는 워크스페이스 범위)
omk plane intake list                                # 요청(Intake) 목록

omk plane workspace members                          # 워크스페이스 멤버 목록
omk plane workspace features                         # 워크스페이스 기능 목록
omk plane teamspace list                             # 팀스페이스 목록
omk plane initiative list                            # 이니셔티브 목록
omk plane sticky list                                # 스티키 목록
omk plane customer list                              # 고객 목록 (Enterprise)

omk plane work-item-type list                        # 작업 항목 타입
omk plane work-item-property list --type TYPE_ID     # 사용자 정의 속성
```

### omk linear (또는 omk ln) — Linear 프로젝트 관리

Linear 명령어 사용 전 `LINEAR_API_KEY`를 설정합니다. 팀 기반 명령어에는 `LINEAR_TEAM_ID`도 설정하면 편리합니다.

#### me — 현재 사용자

```bash
omk linear me                             # 현재 사용자 정보 조회 (id, name, email)
```

#### team — 팀 관리

```bash
omk linear team list                      # 팀 목록 조회
omk linear team get TEAM_ID              # 팀 상세 조회
```

#### issue — 이슈 관리

```bash
omk linear issue list [--team TEAM_ID] [--first N]
omk linear issue get ISSUE_ID_OR_KEY     # UUID 또는 KEY-123 형식
omk linear issue create --title TITLE --team TEAM_ID [--description DESC] [--priority 0-4] [--state STATE_ID] [--assignee USER_ID]
omk linear issue update ISSUE_ID [--title TITLE] [--priority 0-4] [--state STATE_ID] [--assignee USER_ID] [--description DESC]
omk linear issue delete ISSUE_ID

# 댓글
omk linear issue comment list ISSUE_ID
omk linear issue comment create ISSUE_ID --body "댓글 내용"
```

우선순위: `0`=없음, `1`=긴급, `2`=높음, `3`=중간, `4`=낮음

#### state — Workflow 상태

```bash
omk linear state list [--team TEAM_ID]   # 팀 workflow 상태 목록
```

#### label — 레이블

```bash
omk linear label list [--team TEAM_ID]   # 팀 레이블 목록
omk linear label get LABEL_ID            # 레이블 상세 조회
```

#### project — 프로젝트

```bash
omk linear project list [--first N]      # 프로젝트 목록
omk linear project get PROJECT_ID        # 프로젝트 상세 조회
```

#### cycle — 사이클

```bash
omk linear cycle list [--team TEAM_ID]   # 팀 사이클 목록
omk linear cycle get CYCLE_ID            # 사이클 상세 조회
```

---

## 출력 형식

### Table (기본 형식)

```bash
omk plane work-item list
```

```text
ID                                    NAME           PRIORITY  STATE      ASSIGNEES
12345678-90ab-cdef-1234-567890abcdef  로그인 버그 수정  high      In Progress  alice
87654321-abcd-ef12-3456-7890abcdef12  다크 모드 추가   medium    To Do      bob, charlie
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
      "name": "로그인 버그 수정",
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

```text
12345678-90ab-cdef-1234-567890abcdef|로그인 버그 수정|high|In Progress|alice
87654321-abcd-ef12-3456-7890abcdef12|다크 모드 추가|medium|To Do|bob,charlie
```

---

## 서버 호환성

> 개발 기준: **Plane Community Edition (무료 자가호스팅)**
> 무료 플랜에서 제공하는 기능을 우선 구현합니다. 유료/Enterprise 전용 기능은 구현 범위에 포함되지 않습니다.

### Plane

| 기능 | 구현 | plane.so | Self-hosted CE | 비고 |
|------|:----:|:--------:|:--------------:|------|
| Work Items (CRUD) | ✅ | ✅ | ✅ | 댓글·링크·활동·첨부파일 포함 |
| 작업 항목 관계 (Relations) | ✅ | ✅ | ❌ | plane.so & Enterprise 전용; CE 미지원 |
| 작업 항목 로그 (Worklogs) | ✅ | ✅ | ❌ | plane.so & Enterprise 전용; CE 미지원 |
| Cycles (CRUD) | ✅ | ✅ | ✅ | 아이템 추가·제거 포함 |
| Modules (CRUD) | ✅ | ✅ | ✅ | 아이템 추가 포함 |
| Milestones (CRUD) | ✅ | ✅ | ✅ | 아이템 추가·제거 포함 |
| Intake (CRUD) | ✅ | ✅ | ✅ | 상태 승인·거부 포함 |
| Initiatives (CRUD) | ✅ | ✅ | ✅ | 에픽·레이블·프로젝트 연결 포함 |
| Teamspaces (CRUD) | ✅ | ✅ | ✅ | 멤버·프로젝트 관리 포함 |
| Stickies (CRUD) | ✅ | ✅ | ✅ | - |
| Work Item Types (CRUD) | ✅ | ✅ | ✅ | - |
| Custom Properties (CRUD) | ✅ | ✅ | ✅ | 옵션·값 관리 포함 |
| Users / Members | ✅ | ✅ | ✅ | me, workspace members |
| 프로젝트 페이지 | ⚠️ | ✅ | ✅ | get·create만 구현 |
| 워크스페이스 페이지 | ⚠️ | ✅ | ❌ | CE 자가호스팅에서 Enterprise 전용 |
| Epics | ⚠️ | ✅ | ✅ | list·get만 구현 |
| States | ⚠️ | ✅ | ✅ | list만 구현 |
| Labels | ⚠️ | ✅ | ✅ | list·create만 구현 |
| Projects | ⚠️ | ✅ | ✅ | list만 구현 |
| Workspace Features | ⚠️ | ✅ | ✅ | list만 구현 (read-only) |
| Customers (CRUD) | ✅ | ✅ | ❌ | Enterprise 전용 (CE 미지원) |

#### 부분 구현 사유

| 기능 | 미구현 범위 | 사유 |
|------|------------|------|
| 프로젝트 페이지 | list·update·delete | Plane Python SDK가 해당 엔드포인트를 미지원 |
| 워크스페이스 페이지 | list·update·delete | Plane Python SDK 미지원; CE에서 Enterprise 전용 |
| Epics | create·update·delete | Epic은 Work Item Type의 특수 케이스. Plane API의 Epic CRUD가 CE에서 제한적으로 제공되어 조회만 지원 |
| States | create·update·delete | 프로젝트 설정 리소스로, 자동화 파이프라인에서 직접 생성·삭제 수요가 낮아 list 우선 구현 |
| Labels | get·update·delete | 자동화 파이프라인에서 레이블 수정·삭제 수요가 낮아 후순위 |
| Projects | create·update·delete | 관리자 작업으로 CLI 자동화 범위 밖으로 판단 |

### Linear

| 기능 | 구현 | 비고 |
|------|:----:|------|
| Issues (CRUD) | ✅ | 댓글 포함 |
| Teams | ✅ | list·get |
| States | ✅ | list |
| Labels | ✅ | list·get |
| Projects | ✅ | list·get |
| Cycles | ✅ | list·get |
| Users | ✅ | me |

### GitHub

| 기능 | 구현 | 비고 |
|------|:----:|------|
| Issues | ❌ | 향후 구현 예정 |
| Projects | ❌ | 향후 구현 예정 |

> GitHub 통합은 [`gh` CLI](https://cli.github.com/) 기반으로 구현 예정입니다. `npx oh-my-kanban`을 실행하면 `gh` 설치 및 인증을 안내합니다.

### Notion / Jira

| 기능 | 구현 | 비고 |
|------|:----:|------|
| Notion | ❌ | 미착수 |
| Jira | ❌ | 미착수 |

---

## 예제

### 예제 1: 에이전트 파이프라인 — 반복 생성 → 작업 생성 → 할당

```bash
#!/bin/bash

export PLANE_API_KEY="pl_xxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj_uuid"

# 1. 반복(스프린트) 생성
CYCLE_ID=$(omk plane cycle create \
  --name "Sprint 1" \
  --start-date "2024-03-06" \
  --end-date "2024-03-20" \
  -o json | jq -r '.data.id')

echo "생성된 반복: $CYCLE_ID"

# 2. 작업 생성
ITEM_ID=$(omk plane work-item create \
  --name "중요 버그 수정" \
  --priority high \
  --state "$STATE_ID" \
  -o json | jq -r '.data.id')

echo "생성된 작업: $ITEM_ID"

# 3. 반복에 작업 추가
omk plane cycle add-items "$CYCLE_ID" --items "$ITEM_ID"

# 4. 사용자에게 할당
omk plane work-item update "$ITEM_ID" --assignee "$ASSIGNEE_USER_ID"

echo "완료!"
```

### 예제 2: Linear 이슈 파이프라인

```bash
#!/bin/bash

export LINEAR_API_KEY="lin_api_xxxxxx"

# 1. 팀 ID 조회
TEAM_ID=$(omk linear team list -o json | jq -r '.results[0].id')

# 2. 상태 ID 조회
STATE_ID=$(omk linear state list --team "$TEAM_ID" -o json | jq -r '.results[] | select(.name=="In Progress") | .id')

# 3. 이슈 생성
ISSUE_ID=$(omk linear issue create \
  --title "인증 버그 수정" \
  --team "$TEAM_ID" \
  --priority 2 \
  --state "$STATE_ID" \
  -o json | jq -r '.id')

echo "생성된 이슈: $ISSUE_ID"
```

### 예제 3: 다중 워크스페이스 관리

```bash
# Production 환경에서 작업 조회
omk --profile production plane work-item list

# Development 환경에서 작업 생성
omk --profile development plane work-item create --name "새 기능" --priority medium

# Staging 환경에서 필터링
omk --profile staging plane work-item search --query "버그" -o json | jq '.data[] | select(.priority=="urgent")'
```

### 예제 4: 프로젝트 상태 리포트 생성

```bash
#!/bin/bash

export PLANE_WORKSPACE_SLUG="my-workspace"

omk plane work-item list --all -o json > report.json

# 상태별 개수 집계
jq '[.data[] | .state] | group_by(.) | map({state: .[0], count: length})' report.json

# 우선순위별 상위 5개 작업
jq '.data | sort_by(.priority) | reverse | .[0:5]' report.json
```

---

## 로드맵

- [x] **Plane** (plane.so, 자체 호스팅)
  - 참고: **Community Edition(자체 호스팅, 무료 버전)** 기준으로 개발됨. Enterprise 전용 기능은 미구현.
  - 프로바이더 서브그룹: `omk plane` (또는 `omk pl`)
- [x] **Linear**
  - 프로바이더 서브그룹: `omk linear` (또는 `omk ln`)
  - 지원: 이슈, 팀, 사이클, 프로젝트, 상태, 레이블, 댓글
- [ ] **GitHub** ([`gh` CLI](https://cli.github.com/) 기반)
  - 프로바이더 서브그룹: `omk github` (또는 `omk gh`)
  - `npx oh-my-kanban` 실행 시 `gh` 설치 및 인증을 자동으로 안내합니다
- [ ] **Notion**
- [ ] **Jira**

---

## 개발 참여

### 환경 설정

```bash
git clone https://github.com/ej31/oh-my-kanban.git
cd oh-my-kanban
pip install -e ".[dev]"
```

### 코드 스타일

- **Python 버전**: 3.10 이상
- **Linting**: Ruff (E, F, I, UP, B 규칙)
- **줄 길이**: 100자

### 테스트

```bash
pytest tests/
```

### Pull Request 프로세스

1. 저장소를 Fork합니다
2. 기능 브랜치를 생성합니다: `git checkout -b feat/your-feature`
3. 변경사항을 커밋합니다: `git commit -am 'feat: add your feature'`
4. 브랜치에 Push합니다: `git push origin feat/your-feature`
5. Pull Request를 생성합니다

---

## 라이선스

MIT License — [LICENSE](LICENSE) 파일을 참고하세요.

---

## 지원

- **이슈 보고**: [GitHub Issues](https://github.com/ej31/oh-my-kanban/issues)
- **문서**: [GitHub Wiki](https://github.com/ej31/oh-my-kanban/wiki)
- **API 레퍼런스**: [Plane API Docs](https://docs.plane.so/api-reference)

---

**oh-my-kanban**으로 AI 에이전트 기반의 자동화된 프로젝트 관리를 경험해보세요!
