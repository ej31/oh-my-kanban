[한국어](README_kr.md) | [ENGLISH](README_en.md)

# oh-my-kanban | 오마이칸반

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
- **완전한 Plane CRUD 지원** — work items, cycles, modules, intake, pages, users, states, labels 등
- **다중 워크스페이스 관리** — 프로필 기반으로 여러 환경 동시 관리
- **Self-Hosted 친화적** — Plane Community Edition(무료) 기준 개발

Plane API의 오버헤드를 제거하고 직접 호출하여 빠르고 확장 가능한 자동화를 제공합니다.

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

사람의 개입 없이 에이전트가 자동으로 작업을 수행하려면:

```bash
export PLANE_API_KEY="pl_xxxxxxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_BASE_URL="https://api.plane.so"  # 또는 자체 호스팅 URL

# 환경변수만으로 모든 작업 가능
omk work-item list -o json
omk cycle create --name "Sprint 1" --start-date "2024-03-06" --end-date "2024-03-20"
omk work-item create --name "로그인 버그 수정" --state-id "..." --project "..."
```

### 3단계: 사람이 사용 (대화형)

```bash
# 기본 프로필 사용
omk config show
omk work-item list

# 특정 프로필 사용
omk --profile production work-item list -o table
```

---

## 설정

### 설정 파일 위치

```
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
omk --profile production work-item list
```

### 환경변수 우선순위

설정의 우선순위는 다음 순서대로 적용됩니다:

**명령행 옵션 > 환경변수 > 설정 파일 > 기본값**

```bash
# 환경변수로 덮어쓰기
PLANE_API_KEY="pl_xxxxxx" omk config show
PLANE_WORKSPACE_SLUG="override-ws" omk work-item list
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
omk [OPTIONS] COMMAND [ARGS]
```

| 옵션 | 환경변수 | 설명 |
|------|---------|------|
| `--workspace, -w SLUG` | `PLANE_WORKSPACE_SLUG` | 워크스페이스 슬러그 |
| `--project, -p ID` | `PLANE_PROJECT_ID` | 프로젝트 UUID |
| `--output, -o FORMAT` | - | 출력 포맷: `table` \| `json` \| `plain` (기본: `table`) |
| `--profile PROFILE` | `PLANE_PROFILE` | 설정 프로필 (기본: `default`) |
| `--version` | - | 버전 표시 |

### 커맨드 그룹

#### config — 설정 관리

설정 프로필과 워크스페이스 정보를 관리합니다.

```bash
omk config init                              # 대화형 초기 설정
omk config show [--profile PROFILE]          # 현재 설정 확인
omk config set KEY VALUE [--profile PROFILE] # 설정 값 변경
omk config profile list                      # 프로필 목록
omk config profile use NAME                  # 기본 프로필 변경
```

#### work-item — 작업 항목 관리

작업 항목(work items)의 생성, 조회, 수정, 삭제를 수행합니다.

```bash
# 목록 조회
omk work-item list [--all] [--per-page N] [--cursor CURSOR] [--priority PRIORITY]

# 상세 조회
omk work-item get ITEM_ID_OR_IDENTIFIER

# 생성
omk work-item create --name NAME [--state-id STATE] [--priority PRIORITY] [--description DESC] [--assignees USER1,USER2]

# 수정
omk work-item update ITEM_ID [--name NAME] [--state-id STATE] [--priority PRIORITY]

# 삭제
omk work-item delete ITEM_ID [--force]

# 검색
omk work-item search QUERY

# 관계 설정 (차단, 연관, 중복 등)
omk work-item relation create ITEM_ID --type TYPE --target TARGET_ITEM_ID
omk work-item relation list ITEM_ID
omk work-item relation delete ITEM_ID --target TARGET_ITEM_ID
```

#### cycle — 반복(스프린트) 관리

반복 주기를 생성하고 관리합니다.

```bash
omk cycle list [--all]
omk cycle create --name NAME --owned-by USER_ID [--start-date DATE] [--end-date DATE]
omk cycle get CYCLE_ID
omk cycle update CYCLE_ID [--name NAME] [--start-date DATE] [--end-date DATE]
omk cycle delete CYCLE_ID
omk cycle list-work-items CYCLE_ID
omk cycle add-work-items CYCLE_ID ITEM1 ITEM2 ...
omk cycle remove-work-item CYCLE_ID ITEM_ID
```

#### module — 모듈 관리

큰 기능 단위를 관리하는 모듈을 생성하고 관리합니다.

```bash
omk module list [--all]
omk module create --name NAME [--status STATUS] [--start-date DATE] [--target-date DATE]
omk module get MODULE_ID
omk module update MODULE_ID [--name NAME] [--status STATUS]
omk module delete MODULE_ID
omk module list-work-items MODULE_ID
omk module add-work-items MODULE_ID ITEM1 ITEM2 ...
```

#### 기타 커맨드

```bash
omk user list                              # 사용자 목록
omk project list [--all]                   # 프로젝트 목록
omk state list                             # 상태(state) 목록
omk label list [--all]                     # 라벨 목록
omk label create --name NAME [--color HEX] # 라벨 생성

omk milestone list                         # 마일스톤 목록
omk epic list                              # 에픽 목록
omk page list                              # 페이지 목록
omk intake list                            # 요청(Intake) 목록

omk workspace list                         # 워크스페이스 정보
omk teamspace list                         # 팀스페이스 목록
omk initiative list                        # 이니셔티브 목록

omk work-item-type list                    # 작업 항목 타입
omk work-item-property list --type TYPE_ID # 사용자 정의 속성
```

---

## 출력 형식

### Table (기본 형식)

사람이 읽기 좋은 테이블 형식입니다.

```bash
omk work-item list
```

```
ID                                    NAME           PRIORITY  STATE      ASSIGNEES
12345678-90ab-cdef-1234-567890abcdef  로그인 버그 수정  high      In Progress  alice
87654321-abcd-ef12-3456-7890abcdef12  다크 모드 추가   medium    To Do      bob, charlie
```

### JSON (에이전트 자동화용)

에이전트가 파싱하기 좋은 JSON 형식입니다. 페이지네이션 정보도 포함됩니다.

```bash
omk work-item list -o json
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

파이프 기호(|)로 구분된 일반 텍스트 형식입니다.

```bash
omk work-item list -o plain
```

```
12345678-90ab-cdef-1234-567890abcdef|로그인 버그 수정|high|In Progress|alice
87654321-abcd-ef12-3456-7890abcdef12|다크 모드 추가|medium|To Do|bob,charlie
```

---

## 서버 호환성

oh-my-kanban은 Plane의 여러 버전을 지원합니다.

| 기능 | plane.so | Self-hosted CE | 비고 |
|------|----------|----------------|------|
| Work Items | ✅ | ✅ | - |
| Cycles | ✅ | ✅ | - |
| Modules | ✅ | ✅ | - |
| Milestones | ✅ | ✅ | - |
| Pages | ✅ | ✅ | - |
| Intake | ✅ | ✅ | - |
| Custom Properties | ✅ | ⚠️ | Community Edition에서 제한됨 |
| Epics | ✅ | ⚠️ | Community Edition에서 제한됨 |
| Initiatives | ✅ | ✅ | - |

**참고**: 현재 Plane의 Community Edition(자체 호스팅, 무료 버전) 기준으로 개발되었습니다.
Enterprise 전용 기능은 미구현 상태입니다.

---

## 예제

### 예제 1: 에이전트 파이프라인 — 반복 생성 → 작업 생성 → 할당

환경변수를 설정한 후 shell 스크립트로 자동화할 수 있습니다:

```bash
#!/bin/bash

export PLANE_API_KEY="pl_xxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj_uuid"

# 1. 반복(스프린트) 생성
CYCLE_ID=$(omk cycle create \
  --name "Sprint 1" \
  --owned-by "$USER_ID" \
  --start-date "2024-03-06" \
  --end-date "2024-03-20" \
  -o json | jq -r '.data.id')

echo "생성된 반복: $CYCLE_ID"

# 2. 작업 생성
ITEM_ID=$(omk work-item create \
  --name "중요 버그 수정" \
  --priority high \
  --state-id "$STATE_ID" \
  -o json | jq -r '.data.id')

echo "생성된 작업: $ITEM_ID"

# 3. 반복에 작업 추가
omk cycle add-work-items "$CYCLE_ID" "$ITEM_ID"

# 4. 사용자에게 할당
omk work-item update "$ITEM_ID" --assignees "$ASSIGNEE_USER_ID"

echo "완료!"
```

### 예제 2: 다중 워크스페이스 관리

프로필을 사용하여 여러 환경을 동시에 관리합니다:

```bash
# Production 환경에서 작업 조회
omk --profile production work-item list

# Development 환경에서 작업 생성
omk --profile development work-item create --name "새 기능" --priority medium

# Staging 환경에서 필터링
omk --profile staging work-item search "버그" -o json | jq '.data[] | select(.priority=="urgent")'
```

### 예제 3: 프로젝트 상태 리포트 생성

JSON 출력을 활용하여 리포트를 생성합니다:

```bash
#!/bin/bash

export PLANE_WORKSPACE_SLUG="my-workspace"

# JSON 출력으로 리포트 생성
omk work-item list --all -o json > report.json

# 상태별 개수 집계
jq '[.data[] | .state] | group_by(.) | map({state: .[0], count: length})' report.json

# 우선순위별 상위 5개 작업
jq '.data | sort_by(.priority) | reverse | .[0:5]' report.json
```

---

## 로드맵

oh-my-kanban은 현재 Plane만 지원합니다. 향후 다른 프로젝트 관리 플랫폼을 추가할 계획입니다:

- [x] **Plane** (plane.so, 자체 호스팅)
  - 참고: **Community Edition(자체 호스팅, 무료 버전)** 기준으로 개발됨. Enterprise 전용 기능은 미구현.
- [ ] **GitHub**
- [ ] **Linear**
- [ ] **Notion**
- [ ] **Jira**

---

## 개발 참여

### 환경 설정

소스에서 개발 환경을 구성하려면:

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

모든 기여를 환영합니다!

---

## 라이선스

MIT License — [LICENSE](LICENSE) 파일을 참고하세요.

---

## 지원

문제가 발생하거나 도움이 필요한 경우:

- **이슈 보고**: [GitHub Issues](https://github.com/ej31/oh-my-kanban/issues)
- **문서**: [GitHub Wiki](https://github.com/ej31/oh-my-kanban/wiki)
- **API 레퍼런스**: [Plane API Docs](https://docs.plane.so/api-reference)

---

**oh-my-kanban**으로 AI 에이전트 기반의 자동화된 프로젝트 관리를 경험해보세요!
