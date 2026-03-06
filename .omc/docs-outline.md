# oh-my-kanban 문서 작성 초안

## 프로젝트 개요
**oh-my-kanban (omk)**: AI 에이전트가 Plane 프로젝트 관리 서버를 CLI로 제어하는 도구
- **핵심 가치**: AI 에이전트 우선 설계, 사람 사용은 후순위
- **GitHub**: https://github.com/ej31/oh-my-kanban
- **Package**: plane-sdk>=0.2.6, click>=8.0, rich>=13.0

---

## 1. 전체 명령어 트리

### 1.1 글로벌 옵션
```
omk [OPTIONS] PROVIDER [PROVIDER_OPTIONS] COMMAND [ARGS]
```

**프로바이더**: `plane` (또는 `pl`), `linear` (또는 `ln`), `github` (또는 `gh`), `config`

| 옵션 | 환경변수 | 설명 |
|------|---------|------|
| `-o/--output` | - | 출력 포맷: `table` (기본), `json`, `plain` |
| `--workspace, -w` | `PLANE_WORKSPACE_SLUG` | 워크스페이스 슬러그 |
| `--project, -p` | `PLANE_PROJECT_ID` | 프로젝트 UUID |
| `--profile` | `PLANE_PROFILE` | 설정 프로필 (기본: `default`) |
| `--version` | - | 버전 확인 |

### 1.2 환경변수 (우선순위: CLI > 환경변수 > config.toml > CLAUDE.md)

**Plane**
- `PLANE_BASE_URL`: API 서버 URL (기본: https://api.plane.so)
- `PLANE_API_KEY`: API 인증 키 (필수)
- `PLANE_WORKSPACE_SLUG`: 워크스페이스 슬러그
- `PLANE_PROJECT_ID`: 프로젝트 UUID (CLAUDE.md에서 자동 감지 지원)
- `PLANE_PROFILE`: 사용할 프로필

**Linear**
- `LINEAR_API_KEY`: Linear API 토큰 (linear 명령어에 필수)
- `LINEAR_TEAM_ID`: 기본 팀 ID (선택, --team 미지정 시 사용)

### 1.3 설정 파일 위치
- **경로**: `~/.config/oh-my-kanban/config.toml`
- **형식**: TOML 프로필 기반 (단일/다중 프로필 지원)

---

## 2. 명령어 그룹별 상세

### 2.1 config - 설정 관리
```
omk config init           # 대화형 초기 설정 (plane.so 또는 self-hosted 선택)
omk config show [--profile NAME]  # 현재 설정 출력 (API 키 마스킹)
omk config set KEY VALUE [--profile NAME]  # 설정 값 변경
omk config profile list   # 저장된 프로필 목록
omk config profile use NAME  # 기본 프로필 변경
```

**허용 설정 키**: base_url, api_key, workspace_slug, project_id, output

---

### 2.2 user - 사용자 정보
```
omk plane user me               # 현재 로그인한 사용자 정보 조회
```

**출력 필드**: id, display_name, email

---

### 2.3 workspace - 워크스페이스 관리
```
omk plane workspace members     # 워크스페이스 멤버 목록
omk plane workspace features    # 워크스페이스 기능 설정 조회
omk plane workspace update-features [--옵션] [bool]
```

**업데이트 옵션**: --project-grouping, --initiatives, --teams, --customers, --wiki, --pi

---

### 2.4 project - 프로젝트 관리
```
omk plane project list [--per-page N] [--all]
omk plane project get PROJECT_ID
omk plane project create --name STR --identifier STR [--description] [--timezone]
omk plane project update PROJECT_ID [--name] [--description]
omk plane project delete PROJECT_ID
omk plane project members PROJECT_ID
omk plane project features PROJECT_ID
omk plane project update-features PROJECT_ID [--에픽/--no-에픽] [--옵션...]
omk plane project worklog-summary PROJECT_ID
```

**출력 필드 (list)**: id, name, identifier, network, total_members
**출력 필드 (get)**: id, name, identifier, description, timezone, created_at

---

### 2.5 state - 상태(State) 관리
```
omk plane state list [--per-page] [--all]
omk plane state get STATE_ID
omk plane state create --name STR --color HEX [--group GROUP]
omk plane state update STATE_ID [--name] [--color] [--group]
omk plane state delete STATE_ID
```

**상태 그룹**: backlog, unstarted, started, completed, cancelled

---

### 2.6 label - 레이블 관리
```
omk plane label list [--per-page] [--all]
omk plane label get LABEL_ID
omk plane label create --name STR --color HEX [--parent UUID]
omk plane label update LABEL_ID [--name] [--color] [--parent]
omk plane label delete LABEL_ID
```

---

### 2.7 work-item - 작업 항목(Issue) 관리

#### 기본 CRUD
```
omk plane work-item list [--per-page] [--all] [--cursor] [--order-by] [--priority PRIORITY]
omk plane work-item get REF                    # UUID 또는 'PROJECT-123' 형식 지원
omk plane work-item create --name STR [--옵션...]
omk plane work-item update WORK_ITEM_ID [--옵션...]
omk plane work-item delete WORK_ITEM_ID
omk plane work-item search --query STR
```

**우선순위**: urgent, high, medium, low, none

#### 댓글 (comment 서브그룹)
```
omk plane work-item comment list WORK_ITEM_ID
omk plane work-item comment get WORK_ITEM_ID COMMENT_ID
omk plane work-item comment create WORK_ITEM_ID --body STR
omk plane work-item comment update WORK_ITEM_ID COMMENT_ID --body STR
omk plane work-item comment delete WORK_ITEM_ID COMMENT_ID
```

#### 링크 (link 서브그룹)
```
omk plane work-item link list WORK_ITEM_ID
omk plane work-item link get WORK_ITEM_ID LINK_ID
omk plane work-item link create WORK_ITEM_ID --url STR
omk plane work-item link update WORK_ITEM_ID LINK_ID [--url]
omk plane work-item link delete WORK_ITEM_ID LINK_ID
```

#### 관계 (relation 서브그룹)
```
omk plane work-item relation list WORK_ITEM_ID
omk plane work-item relation create WORK_ITEM_ID --related-work-item UUID --relation-type TYPE
omk plane work-item relation delete WORK_ITEM_ID --related-work-item UUID
```

**관계 유형**: blocking, blocked_by, duplicate, relates_to, start_before, start_after, finish_before, finish_after

#### 활동 (activity 서브그룹, 읽기 전용)
```
omk plane work-item activity list WORK_ITEM_ID
omk plane work-item activity get WORK_ITEM_ID ACTIVITY_ID
```

#### 첨부파일 (attachment 서브그룹)
```
omk plane work-item attachment list WORK_ITEM_ID
omk plane work-item attachment get WORK_ITEM_ID ATTACHMENT_ID
omk plane work-item attachment create WORK_ITEM_ID --name STR --size INT [--mime-type]
omk plane work-item attachment delete WORK_ITEM_ID ATTACHMENT_ID
```

#### 작업 로그 (worklog 서브그룹, plane.so 전용)
```
omk plane work-item worklog list WORK_ITEM_ID
omk plane work-item worklog create WORK_ITEM_ID --duration INT [--description]
omk plane work-item worklog update WORK_ITEM_ID WORKLOG_ID [--duration] [--description]
omk plane work-item worklog delete WORK_ITEM_ID WORKLOG_ID
```

---

### 2.8 cycle - 사이클(Sprint) 관리
```
omk plane cycle list [--per-page] [--all]
omk plane cycle archived
omk plane cycle get CYCLE_ID
omk plane cycle create --name STR [--start-date] [--end-date] [--description]
omk plane cycle update CYCLE_ID [--옵션...]
omk plane cycle delete CYCLE_ID
omk plane cycle archive CYCLE_ID
omk plane cycle unarchive CYCLE_ID
omk plane cycle items CYCLE_ID [--per-page] [--all]
omk plane cycle add-items CYCLE_ID --items UUID [--items UUID ...]
omk plane cycle remove-item CYCLE_ID WORK_ITEM_ID
omk plane cycle transfer CYCLE_ID --target TARGET_CYCLE_UUID
```

---

### 2.9 module - 모듈 관리
```
omk plane module list [--per-page] [--all]
omk plane module archived
omk plane module get MODULE_ID
omk plane module create --name STR [--description] [--status] [--start-date] [--target-date]
omk plane module update MODULE_ID [--옵션...]
omk plane module delete MODULE_ID
omk plane module archive MODULE_ID
omk plane module unarchive MODULE_ID
omk plane module items MODULE_ID [--per-page] [--all]
omk plane module add-items MODULE_ID --items UUID [--items UUID ...]
omk plane module remove-item MODULE_ID WORK_ITEM_ID
```

**상태**: backlog, planned, in-progress, paused, completed, cancelled

---

### 2.10 milestone - 마일스톤 관리
```
omk plane milestone list [--per-page] [--all]
omk plane milestone get MILESTONE_ID
omk plane milestone create --title STR [--target-date YYYY-MM-DD]
omk plane milestone update MILESTONE_ID [--title] [--target-date]
omk plane milestone delete MILESTONE_ID
omk plane milestone items MILESTONE_ID
omk plane milestone add-items MILESTONE_ID --items UUID [--items UUID ...]
omk plane milestone remove-items MILESTONE_ID --items UUID [--items UUID ...]
```

---

### 2.11 epic - 에픽 관리
```
omk plane epic list [--per-page]
omk plane epic get EPIC_ID
```

**주의**: 에픽은 읽기 전용 명령어만 제공 (생성/수정/삭제는 plane.so 웹 UI에서만 가능)

---

### 2.12 page - 페이지 관리
```
omk plane page get PAGE_ID [--workspace]
omk plane page create --name STR [--description-html HTML] [--workspace]
```

**주의**: --workspace 플래그로 워크스페이스 페이지 vs 프로젝트 페이지 구분

---

### 2.13 intake - 인테이크(Intake) 관리
```
omk plane intake list [--per-page] [--all]
omk plane intake get WORK_ITEM_ID              # 인테이크 자체 ID가 아닌 issue 필드 UUID 사용
omk plane intake create --name STR [--description] [--priority] [--source]
omk plane intake update WORK_ITEM_ID [--status INT] [--source] [--duplicate-to]
omk plane intake delete WORK_ITEM_ID
```

**상태 코드**: -2 (거부), -1 (스누즈), 0 (대기), 1 (승인), 2 (중복)

**중요**: list 결과의 'id' 필드가 아닌 'issue' 필드를 get/update/delete에 사용

---

### 2.14 initiative - 이니셔티브 관리 (워크스페이스 수준)
```
omk plane initiative list [--per-page] [--all]
omk plane initiative get INITIATIVE_ID
omk plane initiative create --name STR [--description] [--start-date] [--end-date] [--state] [--lead]
omk plane initiative update INITIATIVE_ID [--옵션...]
omk plane initiative delete INITIATIVE_ID

# 에픽 연결
omk plane initiative epic list INITIATIVE_ID
omk plane initiative epic add INITIATIVE_ID --epic-ids UUID [--epic-ids UUID ...]
omk plane initiative epic remove INITIATIVE_ID --epic-ids UUID [--epic-ids UUID ...]

# 레이블 연결
omk plane initiative label list INITIATIVE_ID
omk plane initiative label add INITIATIVE_ID --label-ids UUID [--label-ids UUID ...]
omk plane initiative label remove INITIATIVE_ID --label-ids UUID [--label-ids UUID ...]

# 프로젝트 연결
omk plane initiative project list INITIATIVE_ID
omk plane initiative project add INITIATIVE_ID --project-ids UUID [--project-ids UUID ...]
omk plane initiative project remove INITIATIVE_ID --project-ids UUID [--project-ids UUID ...]
```

---

### 2.15 teamspace - 팀스페이스 관리 (워크스페이스 수준)
```
omk plane teamspace list [--per-page] [--all]
omk plane teamspace get TEAMSPACE_ID
omk plane teamspace create --name STR [--description] [--lead]
omk plane teamspace update TEAMSPACE_ID [--옵션...]
omk plane teamspace delete TEAMSPACE_ID

# 멤버 관리
omk plane teamspace member list TEAMSPACE_ID
omk plane teamspace member add TEAMSPACE_ID --member-ids UUID [--member-ids UUID ...]
omk plane teamspace member remove TEAMSPACE_ID --member-ids UUID [--member-ids UUID ...]

# 프로젝트 관리
omk plane teamspace project list TEAMSPACE_ID
omk plane teamspace project add TEAMSPACE_ID --project-ids UUID [--project-ids UUID ...]
omk plane teamspace project remove TEAMSPACE_ID --project-ids UUID [--project-ids UUID ...]
```

---

### 2.16 customer - 고객 관리 (워크스페이스 수준)
```
omk plane customer list [--per-page] [--all]
omk plane customer get CUSTOMER_ID
omk plane customer create --name STR [--email] [--website-url] [--domain] [--employees INT] [--stage] [--contract-status] [--revenue]
omk plane customer update CUSTOMER_ID [--옵션...]
omk plane customer delete CUSTOMER_ID

# 고객 속성
omk plane customer property list [--per-page] [--all]
omk plane customer property get PROPERTY_ID
omk plane customer property create --name STR --display-name STR --property-type TYPE [--옵션...]
omk plane customer property update PROPERTY_ID [--display-name] [--description] [--is-required] [--is-active]
omk plane customer property delete PROPERTY_ID

# 고객 요청
omk plane customer request list CUSTOMER_ID [--per-page]
omk plane customer request get CUSTOMER_ID REQUEST_ID
omk plane customer request create CUSTOMER_ID --name STR [--description] [--link]
omk plane customer request update CUSTOMER_ID REQUEST_ID [--옵션...]
omk plane customer request delete CUSTOMER_ID REQUEST_ID
```

**속성 타입**: text, number, checkbox, select, multi_select, date, member, url, email, file

---

### 2.17 work-item-type - 워크 아이템 타입 관리 (프로젝트 수준)
```
omk plane work-item-type list
omk plane work-item-type get TYPE_ID
omk plane work-item-type create --name STR [--description] [--is-epic] [--is-active]
omk plane work-item-type update TYPE_ID [--optis-epic] [--is-active]
omk plane work-item-type delete TYPE_ID
```

---

### 2.18 work-item-property - 워크 아이템 속성 관리 (프로젝트 수준)
```
omk plane work-item-property list --type-id TYPE_UUID
omk plane work-item-property get PROPERTY_ID --type-id TYPE_UUID
omk plane work-item-property create --type-id TYPE_UUID --display-name STR --property-type TYPE [--옵션...]
omk plane work-item-property update PROPERTY_ID --type-id TYPE_UUID [--optis-active]
omk plane work-item-property delete PROPERTY_ID --type-id TYPE_UUID

# 속성 옵션
omk plane work-item-property option list PROPERTY_ID
omk plane work-item-property option get PROPERTY_ID OPTION_ID
omk plane work-item-property option create PROPERTY_ID --name STR [--description] [--is-active] [--is-default] [--parent]
omk plane work-item-property option update PROPERTY_ID OPTION_ID [--optis-default]
omk plane work-item-property option delete PROPERTY_ID OPTION_ID

# 속성 값
omk plane work-item-property value list WORK_ITEM_ID PROPERTY_ID
omk plane work-item-property value update WORK_ITEM_ID PROPERTY_ID --value STR
```

**속성 타입**: text, number, checkbox, select, multi_select, date, member, url, email, file, relation

---

### 2.19 agent-run - 에이전트 실행 관리 (워크스페이스 수준)
```
omk plane agent-run get RUN_ID
omk plane agent-run create --agent-slug SLUG [--issue UUID] [--project UUID] [--comment STR] [--external-link URL]

# 활동 조회
omk plane agent-run activity list RUN_ID [--per-page] [--all]
```

---

### 2.20 sticky - 스티키 관리 (워크스페이스 수준)
```
omk plane sticky list [--per-page] [--all] [--query STR]
omk plane sticky get STICKY_ID
omk plane sticky create [--name] [--description] [--color] [--background-color]
omk plane sticky update STICKY_ID [--optis]
omk plane sticky delete STICKY_ID
```

---

## 3. CE(Community Edition) vs plane.so 기능 차이

| 기능 | plane.so | CE | 설명 |
|------|----------|----|----|
| worklog | ✅ | ❌ | 작업 시간 기록 |
| page | ✅ | ⚠️ | 서버 버전에 따라 미지원 가능 |
| milestone | ✅ | ❌ | |
| initiative | ✅ | ❌ | |
| epic | ✅ | ❌ | |
| teamspace | ✅ | ❌ | |
| customer | ✅ | ❌ | |
| work-item-type | ✅ | ❌ | |
| work-item-property | ✅ | ❌ | |
| agent-run | ✅ | ❌ | |
| work-item relation | ✅ | ❌ | blocking/blocked_by 등 관계 설정 |

**404 에러 메시지 해석**: "기능이 현재 서버에서 지원하지 않습니다 (Plane Enterprise 전용일 수 있습니다)"

---

## 4. 특이사항 및 주의사항

### 4.1 intake의 ID 필드 혼동
- `omk plane intake list` 결과는 다음 필드를 포함:
  - `id`: 인테이크 자체 ID (내부용)
  - `issue`: work item UUID (get/update/delete에 사용)
- **반드시 'issue' 필드를 사용**해야 함

### 4.2 페이지 관리의 워크스페이스 vs 프로젝트
```bash
# 프로젝트 페이지 (기본)
omk plane page get PAGE_ID

# 워크스페이스 페이지
omk plane page get PAGE_ID --workspace
```

### 4.3 출력 포맷
- **table** (기본): Rich 라이브러리로 보기 좋은 테이블
- **json**: 완전한 JSON 출력
- **plain**: 탭 구분 텍스트 (스크립트용)

### 4.4 페이지네이션
- 기본: 50개 항목
- `--per-page N`: 페이지당 항목 수 지정
- `--all`: 모든 페이지 자동 순회 (커서 기반)
- `--cursor`: 다음 페이지 커서 명시 지정

### 4.5 설명 필드 처리
- CLI에서 평문(`--description "text"`)을 입력하면
- 자동으로 `<p>text</p>` HTML로 래핑됨
- HTML 형식이 필요하면 직접 `--description-html` 옵션 사용

### 4.6 CLAUDE.md의 project_id 자동 감지
- 환경변수와 config 파일에 project_id가 없으면
- 현재 디렉토리에서 상위로 올라가며 CLAUDE.md 검색
- `project_id: <UUID>` 형식으로 자동 감지 및 적용

---

## 5. AI 에이전트 워크플로우 예시

### 5.1 자동화된 작업 항목 생성
```bash
# 환경변수로 설정 (CI/CD 파이프라인용)
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj-uuid"
export PLANE_API_KEY="api_key"

# 자동으로 작업 항목 생성
omk plane work-item create \
  --name "Fix: auth module broken" \
  --priority high \
  --assignee "user-uuid" \
  --description "Authentication not working after latest deploy"
```

### 5.2 사이클 관리 자동화
```bash
# 현재 사이클의 모든 작업 항목 조회 (JSON)
omk plane cycle items CYCLE_UUID -o json | jq '.[] | select(.priority=="high")'

# 다른 사이클로 작업 항목 일괄 이전
omk plane cycle transfer OLD_CYCLE_ID --target NEW_CYCLE_ID
```

### 5.3 상태별 작업 항목 조회 및 업데이트
```bash
# 모든 미해결 작업 항목 조회
omk plane work-item list --all -o json | \
  jq '.[] | select(.state != "completed")'

# 특정 레이블의 작업 항목만 조회
omk plane work-item search --query "label:bug" -o json
```

### 5.4 멀티 프로필 관리
```bash
# 개발 환경
omk config init --profile dev

# 프로덕션 환경
omk config init --profile prod

# 작업 실행
omk --profile prod plane work-item list
```

---

## 6. 설정 우선순위

1. **CLI 옵션** (최고 우선순위)
   ```bash
   omk --workspace my-ws --project proj-id plane work-item list
   ```

2. **환경변수**
   ```bash
   export PLANE_WORKSPACE_SLUG=my-ws
   export PLANE_PROJECT_ID=proj-id
   omk plane work-item list
   ```

3. **config.toml** (프로필)
   ```toml
   [default]
   workspace_slug = "my-ws"
   project_id = "proj-id"
   ```

4. **CLAUDE.md** (project_id만)
   ```markdown
   <plane_context>
   - project_id: <UUID>
   </plane_context>
   ```

---

## 7. 에러 처리 및 exit code

| HTTP 상태 | Exit Code | 메시지 |
|----------|-----------|--------|
| 400 | 64 | 잘못된 요청 |
| 401 | 77 | 인증 실패 |
| 403 | 77 | 접근 권한 없음 |
| 404 | 1 | 리소스 미존재 (기능 미지원 가능) |
| 422 | 64 | 입력 데이터 유효성 오류 |
| 429 | 1 | 요청 제한 초과 |
| 500+ | 69 | 서버 오류 |

---

## 8. 빠른 참조 (자주 사용하는 패턴)

### 프로젝트 초기화
```bash
omk config init
omk plane project list --all
```

### 작업 항목 관리 (일일 업무)
```bash
omk plane work-item list -o json | jq '.[] | select(.state != "completed")'
omk plane work-item create --name "..." --priority high
omk plane work-item update ITEM_ID --state STATE_UUID
```

### 반복 작업 (사이클)
```bash
omk plane cycle create --name "Sprint 1" --start-date 2026-03-06 --end-date 2026-03-20
omk plane cycle items CYCLE_ID
omk plane cycle add-items CYCLE_ID --items UUID1 --items UUID2
```

### 에이전트 실행
```bash
omk plane agent-run create --agent-slug "my-agent" --project PROJECT_UUID
```

---

## 다음 단계
1. **README.md**: CLI 설치, 빠른 시작, 예시
2. **AGENTS.md**: AI 에이전트 통합 가이드
3. **.gitignore**: 프로젝트 구조 및 의존성
4. **원자 커밋**: 각 명령어 그룹별로 분리
5. **GitHub push**: 릴리스 준비
