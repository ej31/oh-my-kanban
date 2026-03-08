# oh-my-kanban WI 워크플로우 아키텍처 설계서

> 5명의 아키텍트 에이전트가 독립적으로 분석한 결과를 종합한 설계 문서입니다.
> 작성일: 2026-03-07

---

## 핵심 원칙

1. **WI는 기록이다** — 세션이 WI를 "소유"하지 않는다. 세션은 WI에 "참조/기여"한다.
2. **쓰레기 WI가 없어야 한다** — 시각적으로 깔끔하고, 장기적으로 가치 있는 데이터.
3. **용도 없는 기능은 만들지 않는다** — "나중에 쓸 수도 있으니까"는 최악의 패턴.
4. **fail-open with transparency** — 모든 훅은 실패해도 Claude Code를 차단하지 않되, 실패를 사용자와 Claude에게 반드시 알린다.

---

## 1. Task 관리 구조: 두 가지 모드

사용자가 설치 시 선택한다. 기본값은 **MainTask-Subtask**.

### Mode A: MainTask-Subtask (초보자 권장)

```
MainTask: "로그인 기능 구현"       ← 세션 단위 또는 사용자 지정
├── SubTask: "User 모델 정의"
├── SubTask: "로그인 API 구현"
└── SubTask: "테스트 작성"
```

- **MainTask 단위**: 1 Claude Code 세션 = 1 MainTask (기본). 사용자가 이름 지정 가능.
- **장점**: 진입 장벽 낮음, 웹 UI에서 MainTask만 보이고 펼치면 sub-task.
- **단점**: MainTask가 수십 개 쌓이면 아카이브 전략 필수.

### Mode B: Module-Task-Subtask (중급/팀 환경)

```
Module: "인증 시스템 리팩토링"       ← 기능 단위
├── Task: "OAuth2 Provider 구현"     ← Module에 연결
│   ├── SubTask: "Google OAuth"
│   └── SubTask: "GitHub OAuth"
└── Task: "토큰 관리 개선"
    └── SubTask: "Refresh 토큰 구현"
```

- **Module 단위**: 기능(feature) 단위. 여러 세션이 동일 Module에 기여 가능.
- **장점**: Module 단위로 깔끔하게 정리, 팀 환경에서 기능별 가시성 높음.
- **단점**: 초보자에게 "Module을 먼저 만들어야 한다"는 추가 단계.

### 플랫폼별 매핑 테이블

#### Mode A: MainTask-Subtask

| omk 개념 | Plane | Linear | GitHub |
|----------|-------|--------|--------|
| MainTask | Work Item | Issue | Issue |
| SubTask | Work Item (`parent=MainTask.id`) | Issue (`parentId`) | Task list checkbox |

#### Mode B: Module-Task-Subtask

| omk 개념 | Plane | Linear | GitHub |
|----------|-------|--------|--------|
| Module | Module | Project | Milestone |
| Task | Work Item (Module에 연결) | Issue (Project에 연결) | Issue (Milestone에 연결) |
| SubTask | Work Item (`parent=Task.id`) | Issue (`parentId`) | Task list checkbox |

### 상태 전이 (Lifecycle)

```
Backlog  ──▶  In Progress  ──▶  Completed  ──▶  Archived
  ▲               │                  │                │
  └───────────────┘                  │                │
    수동 (보류/재시작)          N일 경과 (자동)    검색은 가능
                                  또는 수동         UI에서 숨김
```

**자동 전이 트리거**:
- 세션 시작 → MainTask/Task: Backlog → In Progress
- 세션 종료 + 모든 sub-task 완료 → MainTask: In Progress → Completed
- Completed 상태 N일 경과 (기본 7일) → Archived

---

## 2. Session-WI 양방향 연결

### 데이터 모델 변경

```python
@dataclass
class PlaneContext:
    project_id: str = ""
    work_item_ids: list[str] = field(default_factory=list)    # 참조/기여 WI 목록
    module_id: Optional[str] = None
    stale_work_item_ids: list[str] = field(default_factory=list)
    main_task_id: Optional[str] = None                         # NEW: 최상위 WI ID
    focused_work_item_id: Optional[str] = None                 # NEW: 알림 폴링 대상
    last_comment_check: Optional[str] = None                   # NEW: 폴링 타임스탬프
    known_comment_ids: list[str] = field(default_factory=list)  # NEW: 확인된 댓글 ID
```

### WI에 session_id 기록: 구조화 댓글

**세션 시작 댓글** (SessionStart 훅):
```markdown
## omk 세션 시작
- **세션 ID**: {session_id[:8]}...
- **상태**: 활성
- **시작**: {created_at}
- **목표**: {scope.summary 또는 "초기화 중"}
```

**세션 종료 댓글** (SessionEnd 훅, 기존 확장):
```markdown
## omk 세션 기여 요약 (session: {id[:8]}...)
- **상태**: 완료
- **기간**: {start} ~ {end} (약 N시간)
- **통계**: 프롬프트 N회, 수정 파일 N개, 드리프트 N회
- **수정 파일**: file1.py, file2.py, ...
- **관련 커밋**: a1b2c3d, e4f5g6h (신규)
- **핸드오프**: {다음 세션을 위한 권고사항} (신규)
```

### 멀티세션 전략: Advisory Warning

- **Hard Lock 불채택**: 세션 crash 시 lock 해제 불가 → 데드락. fail-open 철학과 불일치.
- **Advisory Warning 채택**: 다른 활성 세션 감지 시 `additionalContext`로 경고만 주입. 작업 차단 안 함.
- **충돌 방지보다 "기여 이력의 투명성"이 핵심**: 각 세션이 독립적으로 댓글을 남기면 타임라인이 자연스럽게 구성.

### 댓글 알림 메커니즘

**UserPromptSubmit 훅에서 시간 기반 throttle 폴링**:
- 2분마다 최대 1회 Plane API 호출 (focused_work_item_id 대상)
- 3초 hard deadline (UserPromptSubmit 훅 5초 timeout 내)
- 축소 타임아웃: connect 1.5s + read 2.0s
- 새 댓글 감지 시 `additionalContext`로 주입:
  ```
  "새로운 의견이 접수되었습니다. [{author}] {comment_text}
   이 부분에 대해서 어떻게 처리하면 될까요?"
  ```
- Circuit breaker: 연속 3회 실패 시 폴링 자동 비활성화

---

## 3. 세션 데이터 업로드 전략

### 결론: 메타데이터만 (전체 로그는 구현하지 않음)

**전체 대화 로그를 구현하지 않는 이유**:
1. **기술적으로 불가** — Claude Code hooks가 대화 내용을 제공하지 않음
2. **용도 불명확** — 모든 주장된 용도에 더 나은 대안이 존재
3. **프라이버시 위험** — 시크릿, 코드, 개인정보 노출 가능
4. **"만들어놓고 나중에 용도 결정"의 전형**

### 메타데이터 모드 강화 (DO)

| 현재 | 추가 |
|------|------|
| scope.summary | 세션 기간 (created_at ~ updated_at) |
| stats (prompts, files, drift) | Git 커밋 해시 연동 |
| files_touched | 핸드오프 노트 (다음 세션 권고) |
| topics | 시크릿 필터링 (`sanitize_comment`) |

### "의사결정 기록" — 기존 기능 활용

`omk_add_comment` MCP tool이 이미 구현되어 있음 (`mcp/server.py:286-383`).
별도 기능 구현 불필요. CLAUDE.md에 "중요 결정 시 `omk_add_comment` 호출" 패턴을 명시하면 됨.

### Historical Data 활용 (메타데이터만으로 가능)

| 분석 | 데이터 소스 | 가치 |
|------|-----------|------|
| 개발 속도 트렌드 | WI별 세션 수/프롬프트 수 | "기능당 평균 3세션" |
| 코드 핫스팟 | files_touched 누적 | "auth.py가 20세션에서 수정 → 리팩토링 후보" |
| 드리프트 추세 | drift_warnings 시계열 | "프롬프트 품질 개선 모니터링" |
| 팀 작업 패턴 | 팀원별 세션 토픽 | "A는 백엔드, B는 프론트" |
| 회고 지원 | Cycle 내 WI + 세션 요약 | "스프린트에서 뭘 했는지 한눈에" |

→ `omk stats` 분석 명령은 **Phase 2+**에서 구현 (데이터 충분히 쌓인 후).

---

## 4. Label 컨벤션 및 크로스 플랫폼 필터링

### Label 네이밍 규칙: `omk:{category}:{value}`

| Label | 용도 | 색상 |
|-------|------|------|
| `omk:session` | omk 관리 WI 마커 | `#6366F1` (indigo) |
| `omk:module:{name}` | 모듈 그룹 | `#06B6D4` (cyan) |
| `omk:type:main` | MainTask 구분 | `#10B981` (emerald) |
| `omk:type:sub` | SubTask 구분 | `#6EE7B7` (light green) |

### SPA 가이드 페이지: 불필요

3개 플랫폼 모두 Label 기반 필터링을 API/CLI에서 지원:
- Plane: REST API (SDK 확장 또는 raw HTTP 필요)
- Linear: GraphQL `IssueFilter.labels`
- GitHub: `gh issue list --label "omk:session"` (네이티브)

### 추상화 전략: 얇은 어댑터 + Label 통합

완전한 `WIProvider` 인터페이스는 3개 플랫폼 격차가 너무 커서 과잉 설계.
기존 CLI 명령 위에 얇은 어댑터를 두되, Label 컨벤션으로 크로스 플랫폼 가시성 확보.

---

## 5. Setup Wizard 확장

### 추가 Step

```
기존 Step 0-2: 언어 → 서비스 → 계정 연결

★ Step 3: Task 관리 방식 선택 (NEW)
  "OH-MY-KANBAN은 Project Task 관리를 도와드리는 서비스입니다.
   MainTask-Subtask 구조로 관리하시겠나요?
   Module-Task-Subtask 단위로 관리하시겠나요?
   처음이시라면 MainTask-Subtask 구조를 추천드립니다."

★ Step 4: 세션 데이터 수준 (NEW)
  "메타데이터만 (추천) / 전체 로그"
  → 전체 로그 선택 시 구체적 활용 시나리오 안내

기존 Step 3-5 → Step 5-7로 이동
```

### Config 확장

```toml
[default]
# 기존...
task_mode = "main-sub"              # "main-sub" | "module-task-sub"
upload_level = "metadata"           # "metadata" | "full"
auto_archive_days = 7               # 0이면 비활성화
auto_complete_subtasks = true
session_retention_days = 30
```

---

## 6. 사용자 접점 설계 (User Touch Surface)

omk가 투명인간이 되면 서비스 가치가 소멸한다.
사용자와 서비스가 "닿는 면적"을 의도적으로 설계한다.

### 설계 원칙

1. **omk가 일하고 있다는 걸 느끼게 한다** — 무음은 곧 무가치
2. **모든 알림은 행동을 유도한다** — 정보만 주는 알림은 무시당함
3. **적절한 빈도** — 매 프롬프트마다 알림 = 스팸. 상태 변화 시에만 알림
4. **systemMessage + additionalContext 이중 채널** — 사용자에게도, Claude에게도

### 6-A. 접점 전체 지도 (Touch Surface Map)

세션 라이프사이클의 모든 순간에서 omk가 사용자와 만나는 지점:

```
SessionStart ──────────────────────────────────────────── SessionEnd
   │                                                         │
   ├─ [신규] WI 선택/생성 안내                                ├─ 세션 요약 기록 알림
   ├─ [재개] 핸드오프 노트 표시                                ├─ 핸드오프 메모 유도
   ├─ [재개] 팀원 댓글 알림                                   └─ Task 완료 여부 확인
   ├─ 멀티세션 경고 (Advisory)
   ├─ 미해결 차단 WI 알림
   └─ Cycle 마감 임박 알림
         │
         ├── UserPromptSubmit (매 프롬프트) ──────────────┐
         │     ├─ 드리프트 → 새 Task 생성 유도            │
         │     ├─ 팀원 댓글 폴링 (2분 throttle)           │
         │     └─ Sub-task 전체 완료 → 완료 처리 유도      │
         │                                               │
         ├── PostToolUse (파일 수정 시) ──────────────────┤
         │     ├─ 핫스팟 파일 인사이트                     │
         │     └─ 커밋 → WI 연결 제안                     │
         │                                               │
         └── 실패 시 (모든 훅) ──────────────────────────┘
               └─ 에러 진단 + 복구 안내 + WI 링크
```

---

### 6-B. 세션 시작 접점 (SessionStart)

#### B-1. 신규 세션: WI 선택/생성 안내

현재: 세션이 시작되면 아무 말 없이 파일만 생성.
변경: 사용자에게 현재 프로젝트의 활성 WI 목록을 보여주고 선택을 유도.

```
[omk] 세션이 시작되었습니다.
  현재 진행 중인 Task:
    YCF-121: OAuth2 Provider 구현 (In Progress)
    YCF-123: 로그인 API 테스트 (In Progress)
  작업할 Task의 번호를 알려주시거나, 새로운 작업을 시작하시면 자동으로 Task가 생성됩니다.
```

```
additionalContext: [omk] 프로젝트에 진행 중인 Work Item이 있습니다.
YCF-121: OAuth2 Provider 구현 | YCF-123: 로그인 API 테스트.
사용자가 특정 Task를 언급하면 해당 WI에 세션을 연결하세요.
새로운 주제로 작업을 시작하면 자동으로 새 Task를 생성합니다.
```

> **행동 유도**: "어떤 Task 할래?" → 사용자가 WI를 인식하고 선택하는 습관 형성

#### B-2. 세션 재개: 핸드오프 노트

현재: `[omk: 세션 재개] {summary}` (Claude에게만, 사용자 안 보임)
변경: 이전 세션의 핸드오프 메모를 사용자에게도 보여줌.

```
[omk] 세션을 재개합니다.
  📋 YCF-123: 로그인 API 테스트
  이전 세션 메모: "refresh_token 갱신 로직 미완성. token_store.py 36번줄부터."
  댓글이 1개 추가되었습니다.
```

> **행동 유도**: 이전 맥락을 즉시 복원 → 사용자가 "omk가 기억해준다" 체감

#### B-3. 차단 WI / Cycle 마감 알림

세션 시작 시 WI 관계와 Cycle을 조회하여 알림:

```
[omk] 주의: YCF-122 (DB 스키마 변경)이 현재 Task를 차단하고 있습니다.
```

```
[omk] Sprint 3 마감 2일 전. 미완료 Task 3개.
```

> **행동 유도**: 우선순위 재조정 유도

---

### 6-C. 작업 중 접점 (UserPromptSubmit / PostToolUse)

#### C-1. 드리프트 → Task 전환 유도

현재: drift 경고가 Claude에게만 주입됨 (`output_context`). 사용자는 모름.
변경: significant/major drift 시 `output_system_message`로 사용자에게도 알리고,
Claude에게는 상세 프로토콜을 `additionalContext`로 주입한다.

##### 사용자 알림 (systemMessage)

```
[omk] 현재 작업이 원래 목표({scope_summary_short})에서 벗어난 것 같습니다.
  새 주제: {new_topic}
  별도 Task로 등록할까요? (계속 진행하셔도 됩니다)
```

##### Claude 프로토콜 (additionalContext)

```
[omk drift 경고] 현재 요청이 세션 범위에서 벗어났습니다.
level={level}, score={score}. 범위: {scope_summary}.

사용자에게 새 Task 생성을 이미 제안했습니다 (systemMessage로 표시됨).
사용자 응답에 따라 아래를 실행하세요:

■ 긍정 응답 시 (응/네/좋아/만들어/별도로 등):
  1. 기존 WI 상태 → "On Hold" (동적 조회, 아래 전략 참조)
  2. 기존 WI에 "omk 작업 일시 중단 (드리프트)" 댓글
  3. 새 WI 생성 (프롬프트에서 작업명 추론, In Progress)
  4. relates_to 관계 설정
  5. 새 WI에 "omk 세션 연결 (드리프트 전환)" 댓글
  6. 세션 상태 전환 (switch_task 함수)
  결과를 [omk] 형식으로 보고

■ 부정 응답 시 (아니/괜찮아/그냥 계속/무시 등):
  scope 확장 + "[omk] 현재 작업 범위를 확장합니다." 안내
```

##### On Hold 상태 동적 조회 전략

Plane 상태(State)는 프로젝트별로 다르므로 상태 이름 하드코딩 금지. 아래 순서로 조회한다:

1. "On Hold" (정확 일치)
2. "Paused" (정확 일치)
3. `group="cancelled"` 중 첫 번째
4. 없으면 "Backlog" 폴백 + 사용자에게 안내

```
[omk] 프로젝트에 "On Hold" 상태가 없어 "Backlog"으로 대체합니다.
  Plane 설정에서 "On Hold" 상태를 추가하시면 더 정확한 추적이 가능합니다.
```

##### 상태 전이도

```
기존 WI                              새 WI
┌───────────┐                  ┌───────────┐
│In Progress│──(드리프트)───▶ │  (생성)    │
└─────┬─────┘                  └─────┬─────┘
      │                              │
      ▼                              ▼
┌───────────┐                  ┌───────────┐
│  On Hold  │ ◀──relates_to──▶│In Progress│
└───────────┘                  └───────────┘

세션 상태:
  focused_work_item_id: old_wi → new_wi
  scope: ScopeState() (리셋)
  timeline: + task_switched 이벤트
```

> **행동 유도**: 드리프트가 "경고"에서 "새 Task 기회"로 전환.
> 부산물로 생기는 작업도 WI로 포착 → 쓰레기 없이 모든 작업이 기록됨.
> 기존 WI는 On Hold 상태로 보존되어 나중에 재개 가능.

#### C-2. 팀원 댓글 알림 (기존 §2 확장)

이미 설계됨 (UserPromptSubmit 2분 throttle 폴링). 알림 형식 보강:

```
[omk] 새로운 의견이 접수되었습니다.
  📋 YCF-123: https://plane.example.com/.../abc123
  💬 김철수: "OAuth scope에 email도 포함해야 합니다"
```

> **행동 유도**: 사용자가 Plane/Linear 웹을 열어볼 이유 생성 + 협업 흐름 활성화

#### C-3. Sub-task 전체 완료 → 완료 처리 유도

세션 중 Sub-task 상태를 갱신할 때 (omk wi update), 모든 sub-task가 완료이면:

```
[omk] YCF-123의 모든 하위 Task가 완료되었습니다!
  Task를 완료 처리할까요?
```

> **행동 유도**: 완료 시점을 놓치지 않게 함 → WI가 In Progress로 방치되는 것 방지

#### C-4. 파일 핫스팟 인사이트

PostToolUse에서 파일 수정 추적 시, 과거 세션 데이터와 비교:

```
[omk] auth.py가 최근 5개 세션에서 수정되었습니다. 리팩토링 대상일 수 있습니다.
```

> **행동 유도**: 데이터 기반 개선 제안. Phase 3+ (데이터 축적 후).

#### C-5. 커밋 → WI 연결 제안

PostToolUse에서 `Bash` tool의 `git commit` 감지 시:

```
[omk] 커밋 a1b2c3d가 감지되었습니다. YCF-123에 기록합니다.
```

```
additionalContext: [omk] 커밋 a1b2c3d를 Work Item YCF-123 댓글에 자동 기록했습니다.
```

> **행동 유도**: 커밋-WI 연결이 자동화됨 → 사용자가 별도로 기록할 필요 없음

---

### 6-D. 세션 종료 접점 (SessionEnd)

#### D-1. 세션 요약 기록 알림

현재: Plane에 댓글 추가하고 끝. 사용자에게 알림 없음.
변경: 성공 시 URL과 함께 알림.

```
[omk] 세션 요약이 기록되었습니다.
  📋 YCF-123: https://plane.example.com/.../abc123
  수정 파일 4개, 프롬프트 23회, 드리프트 1회
```

#### D-2. 핸드오프 메모 유도

세션 종료 직전, 다음 세션을 위한 메모를 남기도록 유도:

```
[omk] 다음 세션을 위한 메모를 남기시겠습니까?
  예: "refresh_token 갱신 로직 미완성. token_store.py 36번줄부터."
  메모는 다음 세션 시작 시 자동으로 표시됩니다.
```

> **구현 참고**: SessionEnd 훅은 사용자 입력을 받을 수 없음 (단방향 출력만 가능).
> 따라서 Claude에게 additionalContext로 "핸드오프 메모를 WI 댓글에 남기세요"를 주입하고,
> Claude가 `omk_add_comment`로 기록하는 방식.

```
additionalContext: [omk 세션 종료 예정] 세션이 곧 종료됩니다.
다음 세션을 위해 핸드오프 메모를 Work Item 댓글에 남겨주세요.
현재 작업 상태, 미완성 부분, 다음에 할 일을 요약하세요.
omk_add_comment 도구를 사용하여 "## 핸드오프\n- ..." 형식으로 기록하세요.
```

#### D-3. Task 완료 여부 확인

작업이 충분히 진행된 세션(sub-task 완료 등)의 종료 시:

```
[omk] 이 세션에서 YCF-123의 작업이 완료된 것 같습니다.
  Task 상태를 "완료"로 변경할까요?
```

---

### 6-E. WI 등록 성공 접점 (핵심)

Task가 등록/연결되면 사용자에게 **즉시 알린다**. 수동적으로 기다리지 않는다.

#### 사용자에게 보이는 메시지 (systemMessage)

**WI 생성/연결 시:**
```
[omk] Task가 등록되었습니다.
  📋 YCF-123: https://plane.example.com/workspace/project/issues/abc123
  중요한 메모나 맥락이 있으시면 위 링크에서 댓글로 남겨주세요.
  이 세션에서 자동으로 참고합니다.
```

#### Claude에게 주입하는 additionalContext

```
[omk 연결 완료] 현재 세션이 Work Item에 연결되었습니다.
Work Item: {wi_identifier} ({wi_url})
사용자가 Plane/Linear 웹에서 이 Work Item에 댓글을 남기면 자동으로 이 세션에 전달됩니다.
중요한 결정이나 발견 사항이 있으면 omk_add_comment 도구로 Work Item에 기록하세요.
```

#### 구현: `notify_success` 유틸리티

```python
# common.py 확장

@dataclass(frozen=True)
class SuccessNudge:
    """성공 알림 정보."""
    event: str              # wi_created | wi_linked | summary_posted | subtask_done | ...
    wi_url: str             # 전체 URL
    wi_identifier: str      # 짧은 식별자 (예: YCF-123)
    message: str            # 사용자용 한글 메시지

def notify_success(nudge: SuccessNudge, hook_name: str) -> None:
    """성공을 사용자 + Claude에게 알린다."""
    # 1. 사용자에게 보이는 systemMessage
    if nudge.event in ("wi_created", "wi_linked"):
        user_msg = (
            f"[omk] Task가 등록되었습니다.\n"
            f"  {nudge.wi_identifier}: {nudge.wi_url}\n"
            f"  중요한 메모나 맥락이 있으시면 위 링크에서 댓글로 남겨주세요.\n"
            f"  이 세션에서 자동으로 참고합니다."
        )
    elif nudge.event == "summary_posted":
        user_msg = (
            f"[omk] 세션 요약이 기록되었습니다.\n"
            f"  {nudge.wi_identifier}: {nudge.wi_url}"
        )
    else:
        user_msg = f"[omk] {nudge.message}"

    # 2. Claude에게 주입할 additionalContext
    claude_ctx = (
        f"[omk 연결 완료] 현재 세션이 Work Item에 연결되었습니다. "
        f"Work Item: {nudge.wi_identifier} ({nudge.wi_url}). "
        f"사용자가 웹에서 댓글을 남기면 이 세션에 자동 전달됩니다. "
        f"중요한 결정이 있으면 omk_add_comment로 Work Item에 기록하세요."
    )

    output_system_message(user_msg, hook_name, claude_ctx)
```

#### WI URL 생성: 플랫폼별 패턴

```python
def build_wi_url(platform: str, cfg, project_id: str, wi_id: str) -> str:
    """플랫폼별 Work Item 전체 URL을 생성한다."""
    if platform == "plane":
        base = cfg.base_url.rstrip("/")
        return f"{base}/{cfg.workspace_slug}/projects/{project_id}/issues/{wi_id}"
    elif platform == "linear":
        # Linear는 issue identifier로 접근 (예: YCF-123)
        return f"https://linear.app/issue/{wi_id}"
    elif platform == "github":
        # GitHub는 repo + issue number
        return f"https://github.com/{cfg.repo}/issues/{wi_id}"
    return ""
```

#### WI 식별자: 사람이 읽을 수 있는 이름

UUID가 아닌 **사람이 알아볼 수 있는 식별자**를 사용한다.

| 플랫폼 | 식별자 형식 | 소스 |
|--------|-----------|------|
| Plane | `{project_identifier}-{sequence_id}` (예: YCF-123) | WI 응답의 `sequence_id` + 프로젝트 `identifier` |
| Linear | `{team_key}-{number}` (예: ENG-456) | Issue 응답의 `identifier` |
| GitHub | `#{number}` (예: #78) | Issue 응답의 `number` |

> UUID만 표시하면 사용자가 어떤 Task인지 인식할 수 없다. 반드시 human-readable 식별자를 함께 제공한다.

---

### 6-F. 스킬 카탈로그 (User-Invocable Skills)

사용자가 Claude Code 세션 안에서 `/oh-my-kanban:*`으로 실행할 수 있는 스킬 전체 목록.
omk의 모든 기능이 스킬로 노출되어야 사용자와의 접점이 넓어진다.

#### 카테고리 1: 세션 제어

| 스킬 | 설명 | 동작 | Phase |
|------|------|------|-------|
| `/oh-my-kanban:setup` | 초기 설정 마법사 | 서비스 선택 → API 키 → 프로젝트 → 훅 설치 → 검증 | 1 |
| `/oh-my-kanban:status` | 현재 세션 추적 상태 확인 | 연결된 WI, 프롬프트 수, 수정 파일, 드리프트 횟수 표시 | 1 |
| `/oh-my-kanban:disable-this-session` | 이 세션 추적 비활성화 | opted_out + 구조화 댓글 (§6-G) | 1 |
| `/oh-my-kanban:doctor` | 연결 진단 | 설정/인증/네트워크/WI 상태 점검 + 복구 안내 | 1 |

#### 카테고리 2: Task 관리

| 스킬 | 설명 | 동작 | Phase |
|------|------|------|-------|
| `/oh-my-kanban:focus` | 기존 WI에 세션 연결 | WI 번호 입력 → 세션을 해당 WI에 연결 + 시작 댓글 | 1 |
| `/oh-my-kanban:create-task` | 새 Task 생성 + 세션 연결 | 이름/설명 입력 → WI 생성 → 세션 연결 + 알림 | 1 |
| `/oh-my-kanban:subtask` | 현재 Task 하위에 Sub-task 추가 | 이름 입력 → parent=현재 WI로 생성 | 2 |
| `/oh-my-kanban:done` | 현재 Task 완료 처리 | WI 상태 → Completed + 완료 댓글 | 2 |
| `/oh-my-kanban:switch-task` | 다른 Task로 전환 | 기존 WI 댓글 → 새 WI 생성/선택 → 양방향 링크 (§6-H) | 2 |

#### 카테고리 3: 기록 & 협업

| 스킬 | 설명 | 동작 | Phase |
|------|------|------|-------|
| `/oh-my-kanban:note` | 현재 Task에 메모 추가 | 입력 텍스트 → WI 댓글로 기록 | 1 |
| `/oh-my-kanban:decision` | 의사결정 기록 | 결정/근거/대안 구조화 댓글 → WI에 기록 | 2 |
| `/oh-my-kanban:handoff` | 핸드오프 메모 작성 | 미완성 사항/다음 단계 → WI 댓글 + 세션 상태 저장 | 2 |
| `/oh-my-kanban:comments` | 현재 Task 최근 댓글 조회 | WI 댓글 목록 → 사용자에게 표시 | 2 |

#### 카테고리 4: 조회 & 탐색

| 스킬 | 설명 | 동작 | Phase |
|------|------|------|-------|
| `/oh-my-kanban:me` | 내 활성 Task 목록 | In Progress/Backlog WI 목록 + 상태 표시 | 2 |
| `/oh-my-kanban:open` | 현재 Task 웹 링크 표시 | 플랫폼별 URL 생성 → 클릭 가능한 링크 출력 | 1 |
| `/oh-my-kanban:sprint` | 현재 Cycle/Sprint 진행 상황 | 완료/진행중/남은 Task 수 + 마감일 | 3 |
| `/oh-my-kanban:history` | 현재 Task의 세션 이력 | WI 댓글에서 omk 세션 댓글 추출 → 타임라인 표시 | 3 |

#### 카테고리 5: Git 연동

| 스킬 | 설명 | 동작 | Phase |
|------|------|------|-------|
| `/oh-my-kanban:link-commit` | 커밋을 현재 Task에 연결 | 최근 커밋 해시 → WI 댓글에 기록 | 3 |
| `/oh-my-kanban:link-branch` | 브랜치를 현재 Task에 연결 | 현재 브랜치명 → WI 설명/댓글에 기록 | 3 |

#### 스킬 발견성 (Discoverability)

사용자가 어떤 스킬이 있는지 모르면 가치가 없다.

| 스킬 | 설명 | 동작 |
|------|------|------|
| `/oh-my-kanban:help` | 사용 가능한 스킬 목록 표시 | 카테고리별 스킬 + 한 줄 설명 출력 |

**SessionStart에서 자동 안내** (신규 사용자):

```
[omk] oh-my-kanban이 활성화되었습니다.
  /oh-my-kanban:help 로 사용 가능한 명령어를 확인하세요.
```

> 첫 3회 세션에서만 표시. 이후에는 표시하지 않음 (세션 카운트 기반 제어).

#### 스킬 별칭 (Shortcuts)

자주 쓰는 스킬은 짧은 별칭을 제공한다:

| 별칭 | 원본 |
|------|------|
| `/omk:s` | `/oh-my-kanban:status` |
| `/omk:f` | `/oh-my-kanban:focus` |
| `/omk:n` | `/oh-my-kanban:note` |
| `/omk:d` | `/oh-my-kanban:done` |
| `/omk:h` | `/oh-my-kanban:help` |
| `/omk:me` | `/oh-my-kanban:me` |
| `/omk:off` | `/oh-my-kanban:disable-this-session` |
| `/omk:sw` | `/oh-my-kanban:switch-task` |

#### 스킬 ↔ 접점 매핑

스킬은 사용자가 **능동적으로** 서비스와 접촉하는 방법.
§6-B~D의 자동 알림은 서비스가 **수동적으로** 사용자에게 다가가는 방법.
두 방향이 합쳐져야 "닿는 면적"이 완성된다.

```
                사용자 → omk (스킬)
               ┌─────────────────────┐
               │  /setup  /status    │
               │  /focus  /create    │
               │  /note   /done     │
               │  /switch /disable  │
               │  /me     /comments │
               │  /help   /doctor   │
               └─────────────────────┘
                         ↕
               ┌─────────────────────┐
               │  WI 등록 알림        │
               │  핸드오프 노트 표시   │
               │  드리프트 → 전환 제안 │
               │  댓글 알림           │
               │  에러 진단 안내       │
               └─────────────────────┘
                omk → 사용자 (자동 알림)
```

---

### 6-G. 접점별 구현 우선순위 (자동 알림 + 스킬)

| 우선순위 | 접점 | 훅 | 가치 | Phase |
|---------|------|-----|------|-------|
**자동 알림 (omk → 사용자)**

| 우선순위 | 접점 | 훅 | 가치 | Phase |
|---------|------|-----|------|-------|
| P0 | WI 등록/연결 성공 알림 (6-E) | SessionStart | 핵심 — 서비스 존재감 | 1 |
| P0 | 대시보드 HUD (6-H) | 모든 훅 | 핵심 — 관리 체감 | 1 |
| P0 | 외부 삭제 감지 + 복구 (6-K) | 모든 API 호출 | 핵심 — 데이터 정합성 | 1 |
| P0 | 실패 진단 + 복구 안내 (6-L) | 모든 훅 | 핵심 — 서비스 신뢰성 | 1 |
| P0 | 세션 요약 기록 알림 (6-D) | SessionEnd | 기록 확인 | 1 |
| P1 | 신규 세션 WI 선택 안내 (6-B) | SessionStart | 습관 형성 | 2 |
| P1 | 세션 재개 핸드오프 (6-B) | SessionStart | 맥락 연속성 | 2 |
| P1 | 드리프트 → 전환 제안 (6-C) | UserPromptSubmit | 작업 포착 | 2 |
| P1 | 팀원 댓글 알림 (6-C) | UserPromptSubmit | 협업 | 2 |
| P1 | 핸드오프 메모 유도 (6-D) | SessionEnd | 맥락 전달 | 2 |
| P2 | Sub-task 완료 → 완료 유도 (6-C) | UserPromptSubmit | 상태 정확성 | 3 |
| P2 | 커밋 → WI 자동 연결 (6-C) | PostToolUse | 트레이서빌리티 | 3 |
| P2 | 차단 WI / Cycle 마감 (6-B) | SessionStart | 우선순위 조정 | 3 |
| P3 | 파일 핫스팟 인사이트 (6-C) | PostToolUse | 개선 제안 | 4 |

**스킬 (사용자 → omk)**

| 우선순위 | 스킬 | 카테고리 | Phase |
|---------|------|---------|-------|
| P0 | `/oh-my-kanban:setup` | 세션 제어 | 1 |
| P0 | `/oh-my-kanban:status` | 세션 제어 | 1 |
| P0 | `/oh-my-kanban:focus` | Task 관리 | 1 |
| P0 | `/oh-my-kanban:create-task` | Task 관리 | 1 |
| P0 | `/oh-my-kanban:note` | 기록 & 협업 | 1 |
| P0 | `/oh-my-kanban:open` | 조회 & 탐색 | 1 |
| P0 | `/oh-my-kanban:disable-this-session` | 세션 제어 (6-I) | 1 |
| P0 | `/oh-my-kanban:doctor` | 세션 제어 (6-L) | 1 |
| P0 | `/oh-my-kanban:help` | 발견성 | 1 |
| P1 | `/oh-my-kanban:subtask` | Task 관리 | 2 |
| P1 | `/oh-my-kanban:done` | Task 관리 | 2 |
| P1 | `/oh-my-kanban:switch-task` | Task 관리 (6-J) | 2 |
| P1 | `/oh-my-kanban:decision` | 기록 & 협업 | 2 |
| P1 | `/oh-my-kanban:handoff` | 기록 & 협업 | 2 |
| P1 | `/oh-my-kanban:comments` | 기록 & 협업 | 2 |
| P1 | `/oh-my-kanban:me` | 조회 & 탐색 | 2 |
| P2 | `/oh-my-kanban:sprint` | 조회 & 탐색 | 3 |
| P2 | `/oh-my-kanban:history` | 조회 & 탐색 | 3 |
| P2 | `/oh-my-kanban:link-commit` | Git 연동 | 3 |
| P2 | `/oh-my-kanban:link-branch` | Git 연동 | 3 |

---

### 6-H. 대시보드 HUD (Dashboard)

"내 세션이 관리되고 있구나"를 **항상** 느끼게 하는 계기판.
systemMessage는 지나가면 사라지고, additionalContext는 사용자에게 안 보인다.
항상 보이는 채널이 필요하다.

#### 기술 제약

| 채널 | 지속성 | 사용자 가시성 | 제약 |
|------|--------|-------------|------|
| `systemMessage` | 일회성 | O | 지나가면 사라짐 |
| `additionalContext` | 컨텍스트 내 | X (Claude만) | 사용자 안 보임 |
| **Terminal title** (ANSI escape) | **영구** | **O** (탭 제목) | ~100자, stderr로 출력 |
| **tmux pane title** | **영구** | **O** (pane 테두리) | tmux 환경 필요 |
| **tmux status-right** | **영구** | **O** (하단 바) | tmux 환경 필요, 전역 |

#### 3-Layer Dashboard

```
┌─ Layer 1: Terminal Title (모든 환경) ─────────────────────┐
│  터미널 탭에 항상 표시. ANSI escape를 stderr로 출력.        │
│  "[omk] YCF-123 · 로그인 API"                             │
└───────────────────────────────────────────────────────────┘

┌─ Layer 2: tmux Pane Title (tmux 환경) ────────────────────┐
│  pane 테두리에 항상 표시. `tmux select-pane -T` 호출.       │
│  "📋 YCF-123 · 로그인 API · In Progress · 12p 3f"         │
└───────────────────────────────────────────────────────────┘

┌─ Layer 3: Status Pulse (상태 변화 시) ────────────────────┐
│  systemMessage로 주요 상태 변화 시에만 표시.                │
│  "[omk] 📋 YCF-123 연결됨 · In Progress"                  │
└───────────────────────────────────────────────────────────┘
```

#### 계기판 포맷

```
📋 YCF-123 · 로그인 API · ● In Progress · 23p 4f 1d
    │           │           │       │        │  │  │
    │           │           │       │        │  │  └─ drift 경고 횟수
    │           │           │       │        │  └─── 수정 파일 수
    │           │           │       │        └────── 프롬프트 횟수
    │           │           │       └─────────────── WI 상태
    │           │           └─────────────────────── 상태 아이콘
    │           └─────────────────────────────────── Task 이름 (15자 절삭)
    └─────────────────────────────────────────────── 사람이 읽을 수 있는 식별자
```

**상태 아이콘:**

| 상태 | 아이콘 | 의미 |
|------|--------|------|
| Backlog | ○ | 대기 중 |
| In Progress | ● | 진행 중 |
| Completed | ✓ | 완료 |
| 연결 없음 | — | WI 미연결 |
| 에러 | ✗ | API 연결 실패 |

#### 구현: `update_hud` 유틸리티

```python
# common.py 확장

import os
import subprocess

# HUD 포맷 (15자 이내로 task 이름 절삭)
HUD_TASK_NAME_MAX = 15

def update_hud(state: SessionState, wi_identifier: str = "", wi_name: str = "", wi_status: str = "") -> None:
    """세션 계기판을 갱신한다. stdout을 오염시키지 않는다."""
    stats = state.stats
    name = wi_name[:HUD_TASK_NAME_MAX] + ("…" if len(wi_name) > HUD_TASK_NAME_MAX else "")

    status_icon = {"Backlog": "○", "In Progress": "●", "Completed": "✓"}.get(wi_status, "—")

    if wi_identifier:
        hud_text = f"📋 {wi_identifier} · {name} · {status_icon} {wi_status} · {stats.total_prompts}p {len(stats.files_touched)}f {stats.drift_warnings}d"
    else:
        hud_text = f"[omk] 세션 활성 · {stats.total_prompts}p {len(stats.files_touched)}f"

    # Layer 1: Terminal title (모든 환경, stderr로 출력)
    sys.stderr.write(f"\033]2;{hud_text}\007")
    sys.stderr.flush()

    # Layer 2: tmux pane title (tmux 환경에서만)
    if os.environ.get("TMUX"):
        try:
            subprocess.run(
                ["tmux", "select-pane", "-T", hud_text],
                timeout=1,
                capture_output=True,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass  # fail-open: tmux 없으면 무시
```

#### HUD 갱신 시점

| 훅 | 갱신 내용 | 빈도 |
|----|----------|------|
| SessionStart (startup) | WI 연결 정보 + 초기 상태 | 1회 |
| SessionStart (resume) | 저장된 WI 정보 복원 | 1회 |
| UserPromptSubmit | 프롬프트 카운트 + 드리프트 카운트 | 매 프롬프트 |
| PostToolUse | 수정 파일 카운트 | 파일 수정 시 |
| Task 전환 (/switch-task) | 새 WI 정보 | 전환 시 |
| SessionEnd | HUD 초기화 (원래 상태 복원) | 1회 |

> UserPromptSubmit에서 매 프롬프트마다 갱신해도 괜찮은 이유:
> stderr 1줄 + tmux 호출 1회 = 총 ~5ms 이하. 훅 5초 timeout 대비 무시할 수준.

#### SessionEnd 시 원래 상태 복원

```python
def reset_hud() -> None:
    """세션 종료 시 HUD를 원래 상태로 복원한다."""
    sys.stderr.write("\033]2;Claude Code\007")
    sys.stderr.flush()

    if os.environ.get("TMUX"):
        try:
            subprocess.run(
                ["tmux", "select-pane", "-T", "⠐ Claude Code"],
                timeout=1,
                capture_output=True,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
```

#### opted_out 세션의 HUD

추적이 비활성화된 세션에서는:

```
[omk] 추적 비활성 · /oh-my-kanban:help
```

> 비활성 상태에서도 omk의 존재를 인식시키되, 재활성화 방법을 안내.

#### `/oh-my-kanban:status` 스킬과의 관계

HUD는 **항상 보이는 요약**이고, `/oh-my-kanban:status`는 **상세 조회**:

```
/oh-my-kanban:status 실행 시:

[omk] 세션 상태 상세
  📋 Task: YCF-123 · 로그인 API 테스트
  🔗 https://plane.example.com/workspace/project/issues/abc123
  📊 상태: In Progress
  ⏱️ 세션 시작: 14:30 (2시간 전)
  📝 프롬프트: 23회
  📁 수정 파일: auth.py, login_test.py, config.py, models.py
  ⚠️ 드리프트 경고: 1회
  💬 미확인 댓글: 2개
  🔄 마지막 동기화: 1분 전
```

> HUD = 계기판 (속도, RPM, 연료)
> /status = 차량 진단 리포트

---

### 6-I. 세션 비활성화 (Opt-out Redesign)

8개 세션을 동시에 띄우는 파워유저에게 Q&A 세션까지 WI가 생기면 쓰레기 데이터다.
세션 단위로 가볍게 추적을 끌 수 있어야 한다.

#### `/oh-my-kanban:disable-this-session` 스킬

**트리거**: 사용자가 스킬 실행 또는 "추적 꺼줘", "이 세션은 Q&A야" 등 발화.

**동작 흐름**:

```
1. state.opted_out = True 설정
2. WI가 이미 연결된 경우 → 구조화 댓글 추가 (삭제 안 함)
3. WI가 없는 경우 → 상태만 변경 (향후 WI 생성 방지)
4. 사용자에게 확인 알림
5. 이후 모든 훅은 이 세션에서 no-op
```

**WI 댓글 (구조화)**:

```markdown
## omk 추적 중단
- **세션 ID**: {session_id[:8]}...
- **시점**: {timestamp}
- **사유**: 사용자 요청 (단순 질의 세션)
- **통계**: 프롬프트 {n}회, 수정 파일 {n}개
- **상태**: 이 세션에서 더 이상 기여하지 않습니다.
```

**사용자 알림 (systemMessage)**:

```
[omk] 이 세션의 Task 추적이 비활성화되었습니다.
  이 세션에서는 더 이상 WI 생성/업데이트가 발생하지 않습니다.
  다시 활성화하려면 새 세션을 시작하세요.
```

#### `_delete_work_items` 제거

현재 `opt_out.py:54-88`의 `_delete_work_items` 함수를 **완전 제거**한다.

| 현재 | 변경 후 |
|------|---------|
| `--delete-tasks` 옵션으로 WI 삭제 가능 | 옵션 자체 제거 |
| 삭제하면 다른 세션의 기여도 사라짐 | WI는 절대 삭제 불가. 댓글로 대체 |
| `state.tasks_deleted = True` 플래그 | 플래그 제거 |

**기각 사유**: 세션 A가 opt-out하면서 WI를 삭제하면, 동일 WI를 참조 중인 세션 B의 기여 기록이 소멸.
"WI는 기록" 원칙과 정면 충돌.

#### 자동 감지 (Phase 3 고려)

파워유저를 위한 추가 개선: N회 프롬프트 이후에도 파일 수정 없는 세션을 자동 감지:

```
[omk] 이 세션에서 10회 대화 동안 파일 수정이 없었습니다.
  단순 Q&A 세션인 경우 Task 추적을 비활성화할 수 있습니다.
  비활성화하시려면 /oh-my-kanban:disable-this-session 을 실행하세요.
```

> P3 (Phase 3)에서 구현. 임계값과 타이밍은 데이터 축적 후 결정.

---

### 6-J. Task 전환 (Switch Task)

세션 도중 작업 방향이 완전히 바뀌는 경우:
- `disable-this-session`은 추적을 아예 끔 → 너무 극단적
- 드리프트 경고만으로는 부족 → 사용자가 의도적으로 전환하는 것
- **필요한 것**: 현재 WI 연결을 끊고 새 WI로 갈아타되, 양쪽에 흔적을 남김

#### `/oh-my-kanban:switch-task` 스킬

**트리거**: 사용자가 스킬 실행 또는 "다른 작업으로 바꿔", "이 Task 말고 새거", "새 Task로" 등 발화.

**동작 흐름**:

```
1. 현재 WI에 "전환 댓글" 추가 (→ 새 WI 링크)
2. 현재 WI 세션 상태를 In Progress → 기존 상태 유지 (완료 아님, 일시 중단)
3. 새 WI 생성 (사용자 입력 또는 Claude가 현재 작업 기반 자동 생성)
4. 새 WI에 "전환 출발 댓글" 추가 (← 이전 WI 링크)
5. 세션 상태 갱신: work_item_ids, main_task_id, focused_work_item_id 교체
6. 사용자에게 양쪽 URL 알림
```

#### 기존 WI에 남기는 댓글

```markdown
## omk Task 전환
- **세션 ID**: {session_id[:8]}...
- **시점**: {timestamp}
- **통계**: 프롬프트 {n}회, 수정 파일 {n}개
- **전환 대상**: → {new_wi_identifier} ({new_wi_url})
- **사유**: 사용자 요청에 의한 작업 전환
- **상태**: 이 세션에서 더 이상 이 Task에 기여하지 않습니다.
```

#### 새 WI에 남기는 댓글

```markdown
## omk 세션 연결 (전환)
- **세션 ID**: {session_id[:8]}...
- **시점**: {timestamp}
- **이전 Task**: ← {old_wi_identifier} ({old_wi_url})
- **목표**: {사용자 입력 또는 Claude 추론}
```

#### 사용자 알림 (systemMessage)

```
[omk] Task가 전환되었습니다.
  이전: YCF-123 (로그인 API 테스트) — 전환 기록 완료
  현재: YCF-456 (DB 마이그레이션) — https://plane.example.com/.../def456
  댓글로 맥락을 남겨주시면 이 세션에서 자동으로 참고합니다.
```

#### Claude에게 주입하는 additionalContext

```
[omk Task 전환] 세션이 새 Work Item에 연결되었습니다.
이전: {old_wi_identifier} ({old_wi_url}) — 전환 댓글 기록 완료.
현재: {new_wi_identifier} ({new_wi_url}).
이전 Task의 맥락은 더 이상 이 세션의 범위가 아닙니다.
새 Task의 목표에 집중하세요. scope가 초기화되었습니다.
```

#### 상태 처리

```python
def switch_task(state: SessionState, new_wi_id: str, new_wi_identifier: str) -> str:
    """현재 WI를 내려놓고 새 WI로 전환한다. 이전 WI ID를 반환한다."""
    old_wi_id = state.plane_context.work_item_ids[0] if state.plane_context.work_item_ids else ""

    # 1. 세션 상태 교체
    state.plane_context.work_item_ids = [new_wi_id]
    state.plane_context.main_task_id = new_wi_id
    state.plane_context.focused_work_item_id = new_wi_id

    # 2. scope 초기화 (새 작업이므로 드리프트 기준 리셋)
    state.scope = ScopeState()

    # 3. 타임라인 기록
    state.timeline.append(
        TimelineEvent(
            timestamp=now_iso(),
            type="task_switched",
            summary=f"Task 전환: {old_wi_id[:8]}... → {new_wi_identifier}",
        )
    )

    return old_wi_id
```

#### 드리프트 → switch-task 자연 연결 (C-1 확장)

§6-C의 "드리프트 → 새 Task 유도"와 자연스럽게 연결된다:

```
[omk] 현재 작업이 원래 목표(로그인 API 테스트)에서 벗어난 것 같습니다.
  새 주제: DB 마이그레이션
  1. 별도 Sub-task로 등록 (현재 Task 유지)
  2. 새 Task로 전환 (/oh-my-kanban:switch-task)
  3. 무시하고 계속 진행
```

> 드리프트가 minor면 Sub-task, major면 switch-task를 우선 제안.

#### WI 간 관계 설정

Plane에서 `relates_to` 관계를 자동 설정하여 웹 UI에서도 연결이 보이게 한다:

```python
# Plane API: 관계 설정
# POST /api/v1/workspaces/{ws}/projects/{pj}/issues/{old_wi_id}/relations/
# body: {"related_issue": new_wi_id, "relation_type": "relates_to"}
```

---

### 6-K. 외부 삭제 감지 (Orphan Detection)

사용자가 Plane/Linear/GitHub 웹에서 직접 WI를 삭제하면, omk 세션은 존재하지 않는 WI를 계속 참조한다.
현재 코드는 이 상황을 **완전히 무시**한다 (404 → 조용히 넘어감).

#### 감지 시점

| 훅 | API 호출 | 현재 404 처리 | 변경 후 |
|----|---------|--------------|---------|
| SessionStart (compact) | WI 상세 조회 | 빈 결과 반환 | orphan 감지 → 알림 |
| SessionEnd | 댓글 추가 | success_count에 미포함, 무시 | orphan 감지 → 알림 |
| UserPromptSubmit (Phase 2) | 댓글 폴링 | 미구현 | orphan 감지 → 폴링 중단 |

#### 404/410 응답 = orphan 확정

```python
# classify_api_error 확장

if status_code in (404, 410):
    return HookDiagnostic(
        category="wi_deleted",
        message="연결된 Task가 외부에서 삭제되었습니다.",
        detail=f"HTTP {status_code} - WI {wi_id} not found",
        recovery_hint="새 Task를 생성하거나, /oh-my-kanban:disable-this-session으로 추적을 중단하세요.",
    )
```

#### 사용자 알림 (systemMessage)

```
[omk] 연결된 Task가 삭제되었습니다.
  기존 Task: YCF-123 (외부에서 삭제됨)
  선택지:
    1. 새 Task를 생성하려면 작업을 계속 진행하세요 (자동 생성)
    2. 추적 없이 진행하려면 /oh-my-kanban:disable-this-session
```

#### Claude에게 주입하는 additionalContext

```
[omk orphan 감지] 세션이 참조하던 Work Item이 외부에서 삭제되었습니다.
WI ID: {wi_id} (HTTP {status_code}).
사용자에게 두 가지 선택지를 안내하세요:
1. 새 Task 생성 — 사용자가 작업을 계속하면 omk가 자동으로 새 WI를 생성합니다.
2. 추적 중단 — /oh-my-kanban:disable-this-session으로 이 세션의 추적을 끕니다.
사용자의 선택을 기다려주세요.
```

#### 상태 처리

```python
def handle_orphan_wi(state: SessionState, deleted_wi_id: str) -> None:
    """삭제된 WI를 세션 상태에서 정리한다."""
    # 1. work_item_ids에서 제거
    state.plane_context.work_item_ids = [
        wi for wi in state.plane_context.work_item_ids
        if wi != deleted_wi_id
    ]

    # 2. main_task_id가 삭제된 WI면 초기화
    if state.plane_context.main_task_id == deleted_wi_id:
        state.plane_context.main_task_id = None

    # 3. focused_work_item_id가 삭제된 WI면 초기화
    if state.plane_context.focused_work_item_id == deleted_wi_id:
        state.plane_context.focused_work_item_id = None

    # 4. 타임라인 기록
    state.timeline.append(
        TimelineEvent(
            timestamp=now_iso(),
            type="wi_orphaned",
            summary=f"WI {deleted_wi_id[:8]}... 외부 삭제 감지",
        )
    )
```

#### 복구 흐름

```
외부 삭제 감지
    │
    ├─ 사용자가 작업 계속 → 다음 SessionStart/WI 생성 시점에 새 WI 자동 생성
    │   └─ 새 WI 댓글: "이전 Task(삭제됨)에서 이어진 세션입니다."
    │
    └─ 사용자가 /disable-this-session → 추적 중단 (6-G)
```

#### 멀티 WI 부분 삭제

`work_item_ids`에 WI가 여러 개 연결된 경우, 일부만 삭제될 수 있다.
삭제된 WI만 제거하고 나머지는 유지한다. 모두 삭제된 경우에만 위 알림을 표시한다.

---

### 6-L. 실패 알림 (Failure Transparency)

#### 원칙: fail-open ≠ fail-silent

훅이 실패해도 Claude Code를 차단하지 않는다 (fail-open). 그러나 **실패를 사용자에게 반드시 알린다** (not silent).
실패를 조용히 삼키면 omk는 아무런 가치도 제공하지 않는 투명인간이 된다.

### 에러 분류 체계

| 카테고리 | 원인 | 심각도 | 예시 |
|----------|------|--------|------|
| `config_missing` | 설정 누락 | CRITICAL | API 키, workspace, project_id 미설정 |
| `auth_failure` | 인증 실패 | CRITICAL | API 키 만료/무효 (HTTP 401/403) |
| `network_error` | 네트워크 오류 | WARNING | 타임아웃, 연결 거부, DNS 실패 |
| `rate_limit` | API 한도 초과 | WARNING | HTTP 429 |
| `server_error` | 서버 오류 | WARNING | HTTP 5xx |
| `data_error` | 데이터 이상 | INFO | WI 조회 실패, JSON 파싱 오류 |

### 사용자 알림 메시지 형식

`output_system_message()` (common.py:58-70)를 활용하여 **사용자에게 직접 보이는 메시지**를 출력한다.

```
[omk] Task 등록이 실패했습니다.
  원인: Plane API 키가 만료되었습니다 (HTTP 401)
  해결: omk config set --api-key <NEW_KEY> 또는 /oh-my-kanban:doctor 실행
  현재 Task: YCF-123 (https://plane.example.com/workspace/project/issues/YCF-123)
```

### 동시에 Claude에게 주입하는 additionalContext

```
[omk 연결 실패] oh-my-kanban이 Plane API와 통신할 수 없습니다.
원인: {error_category} - {error_detail}
현재 바라보는 Work Item: {wi_identifier} ({wi_url})
사용자에게 "/oh-my-kanban:doctor"를 안내하거나, 설정 문제를 함께 해결해주세요.
이 세션의 작업은 계속 진행할 수 있지만, Task 추적이 중단된 상태입니다.
```

### 구현 전략: `HookError` 유틸리티

```python
# common.py 확장

@dataclass(frozen=True)
class HookDiagnostic:
    """훅 실패 진단 정보."""
    category: str           # config_missing | auth_failure | network_error | ...
    message: str            # 사용자용 한글 메시지
    detail: str             # 기술적 세부 (stderr용)
    recovery_hint: str      # 복구 방법 안내
    wi_context: str = ""    # 현재 바라보는 WI 정보 (있으면)

def notify_and_exit(diagnostic: HookDiagnostic, hook_name: str) -> None:
    """실패를 사용자 + Claude에게 알리고 fail-open 종료한다."""
    # 1. 사용자에게 보이는 systemMessage
    user_msg = (
        f"[omk] {diagnostic.message}\n"
        f"  원인: {diagnostic.detail}\n"
        f"  해결: {diagnostic.recovery_hint}"
    )
    if diagnostic.wi_context:
        user_msg += f"\n  현재 Task: {diagnostic.wi_context}"

    # 2. Claude에게 주입할 additionalContext
    claude_ctx = (
        f"[omk 연결 실패] {diagnostic.message} "
        f"원인: {diagnostic.category} - {diagnostic.detail}. "
        f"사용자에게 /oh-my-kanban:doctor를 안내하세요."
    )
    if diagnostic.wi_context:
        claude_ctx += f" 현재 Work Item: {diagnostic.wi_context}"

    # 3. stderr에 기술적 로그
    print(f"[omk] {hook_name} 실패: {diagnostic.detail}", file=sys.stderr)

    # 4. 사용자 + Claude 동시 알림 후 fail-open 종료
    output_system_message(user_msg, hook_name, claude_ctx)
    sys.exit(0)
```

### 에러 분류 함수

```python
def classify_api_error(exc: Exception, status_code: int | None = None) -> HookDiagnostic:
    """API 호출 예외를 HookDiagnostic으로 분류한다."""
    import httpx

    if isinstance(exc, httpx.TimeoutException):
        return HookDiagnostic(
            category="network_error",
            message="Plane 서버 응답 시간이 초과되었습니다.",
            detail=f"TimeoutException: {exc}",
            recovery_hint="네트워크 연결을 확인하거나, Plane 서버 상태를 점검하세요.",
        )
    if isinstance(exc, httpx.NetworkError):
        return HookDiagnostic(
            category="network_error",
            message="Plane 서버에 연결할 수 없습니다.",
            detail=f"NetworkError: {exc}",
            recovery_hint="VPN/네트워크 연결 확인 또는 omk config set --base-url 재설정.",
        )
    if status_code == 401:
        return HookDiagnostic(
            category="auth_failure",
            message="Plane API 키가 만료되었거나 유효하지 않습니다.",
            detail=f"HTTP 401 Unauthorized",
            recovery_hint="omk config set --api-key <NEW_KEY>",
        )
    if status_code == 403:
        return HookDiagnostic(
            category="auth_failure",
            message="Plane API 접근 권한이 없습니다.",
            detail=f"HTTP 403 Forbidden",
            recovery_hint="API 키 권한을 확인하세요. workspace/project 접근 권한이 필요합니다.",
        )
    if status_code == 429:
        return HookDiagnostic(
            category="rate_limit",
            message="Plane API 요청 한도를 초과했습니다.",
            detail=f"HTTP 429 Too Many Requests",
            recovery_hint="잠시 후 자동으로 복구됩니다.",
        )
    if status_code and status_code >= 500:
        return HookDiagnostic(
            category="server_error",
            message="Plane 서버에 오류가 발생했습니다.",
            detail=f"HTTP {status_code}",
            recovery_hint="Plane 서버 상태를 확인하세요.",
        )
    # 기본
    return HookDiagnostic(
        category="unknown",
        message="알 수 없는 오류가 발생했습니다.",
        detail=str(exc),
        recovery_hint="/oh-my-kanban:doctor를 실행해주세요.",
    )

def classify_config_error(cfg) -> HookDiagnostic | None:
    """설정 누락을 진단한다. 문제 없으면 None 반환."""
    missing = []
    if not cfg.api_key:
        missing.append("API 키 (--api-key)")
    if not cfg.workspace_slug:
        missing.append("워크스페이스 (--workspace-slug)")
    if not cfg.project_id:
        missing.append("프로젝트 ID (--project-id)")

    if not missing:
        return None

    return HookDiagnostic(
        category="config_missing",
        message="oh-my-kanban 설정이 불완전합니다.",
        detail=f"누락: {', '.join(missing)}",
        recovery_hint=f"omk config set {' '.join(missing)} 또는 /oh-my-kanban:setup 실행",
    )
```

### WI 컨텍스트 정보 생성

```python
def build_wi_context(state: SessionState, cfg) -> str:
    """현재 세션이 바라보는 WI의 식별자 + URL을 생성한다."""
    wi_ids = state.plane_context.work_item_ids
    if not wi_ids:
        return ""

    wi_id = wi_ids[0]  # 첫 번째 WI
    base_url = cfg.base_url.rstrip("/")
    ws = cfg.workspace_slug
    pj = state.plane_context.project_id or cfg.project_id

    if base_url and ws and pj:
        url = f"{base_url}/{ws}/projects/{pj}/issues/{wi_id}"
        return f"{wi_id[:8]}... ({url})"

    return wi_id[:8] + "..."
```

### 적용 지점: 각 훅의 에러 경로

| 훅 | 현재 | 변경 후 |
|----|------|---------|
| SessionStart (compact) | `build_plane_context` 실패 → stderr만 | `notify_and_exit` + WI 컨텍스트 |
| SessionEnd | `_post_plane_comment` 실패 → stderr만 | `notify_and_exit` + WI 컨텍스트 |
| UserPromptSubmit (Phase 2) | 댓글 폴링 실패 → 미구현 | `notify_and_exit` + circuit breaker |
| 모든 훅 | config 미설정 → `exit_fail_open()` | `classify_config_error` → `notify_and_exit` |

### 반복 알림 방지 (Throttle)

동일 에러가 매 프롬프트마다 반복 표시되면 오히려 사용자 경험 악화.

```python
# SessionState에 추가
@dataclass
class ErrorThrottle:
    last_error_category: str = ""
    last_error_time: str = ""
    consecutive_errors: int = 0

ERROR_NOTIFY_COOLDOWN_SECONDS = 300  # 동일 에러 5분 쿨다운
ERROR_ESCALATION_THRESHOLD = 3      # 3회 연속 → 심각도 상향
```

- **첫 번째 실패**: 즉시 알림
- **동일 카테고리 연속 실패**: 5분 쿨다운 (중복 알림 방지)
- **3회 연속 동일 에러**: 심각도 상향 + 강한 어조로 재알림
- **다른 카테고리 에러**: 즉시 알림 (쿨다운 리셋)

---

### 6-M. Compact 맥락 관리 (Context Compaction Management)

#### 문제 정의

Claude Code의 auto-compact(context window 64~75% 도달 시 자동 실행)는 세션 맥락을 요약하지만,
중요한 결정사항, 거절된 대안, 드리프트 감지 상태, 타임라인 이력이 손실된다.

#### 전략: Pull 우선 + Push 보조

**핵심 통찰**: Plane workflow를 잘 따르면 WI 자체가 곧 스냅샷이다.
착수/결정/완료/블로커 시점의 댓글을 포함한 WI 전체가 compact 후 pull할 데이터의 근간이 된다.

##### Pull (Post-compact 역주입) — Phase 1, 즉시 실행

| 항목 | 현재 | 확장 |
|------|------|------|
| 댓글 수 | 5개 | 10개 |
| 설명 길이 | 600자 | 800자 |
| Sub-task | 미조회 | 제목/상태 목록 추가 |
| 컨텍스트 | 3000자 | 4000자 |
| 댓글 구조화 | 없음 | 작업 시작/완료/블로커 패턴 인식 |

**트리거**: `SessionStart(source="compact")` — 100% 신뢰성, 이미 구현됨
**제약**: Hook timeout 30초, WI 3개 조회에 ~31초 → 병렬화(`asyncio.gather`) 필수

**CLAUDE.md Auto-Compact Instructions**:

```
# Auto-Compact Instructions
compact 시 반드시 보존할 것:
- 현재 진행 중 WI ID와 상태
- 수정 중인 파일 경로
- 최근 결정 사항과 이유
```

##### Push (Pre-compact 스냅샷) — Phase 2, 조건부

**진입 조건**: Phase 1 적용 후에도 compact 후 맥락 손실 불만이 반복될 때만

- `omk_snapshot` MCP tool: Claude가 자발적으로 호출
- WI sub-task로 스냅샷 저장
- Main WI에 `## Compact Timeline` 테이블 유지

| # | 시각 | 트리거 | Sub-Task |
|---|------|--------|----------|
| 1 | T1 | decision | OMK-456 |
| 2 | T2 | context_pressure | OMK-457 |

##### 평가 비교

| 항목 | Pull | Push |
|------|------|------|
| 트리거 신뢰성 | ★★★★★ (100%) | ★★☆☆☆ (불확실) |
| 구현 난이도 | ★★★★★ (기존 확장) | ★★☆☆☆ (신규 개발) |
| 정보 완결성 | ★★★☆☆ | ★★★★☆ |
| UX | ★★★★☆ (비간섭) | ★★★☆☆ (흐름 끊김) |
| **총점** | **25/30** | **18/30** |

##### 업계 레퍼런스

| 패턴 | 출처 | 적용 |
|------|------|------|
| 강제 읽기 규칙 | Cline Memory Bank | compact 후 WI 강제 pull |
| 2계층 메모리 | MemGPT/Letta | core=현재 WI, archival=Plane 전체 |
| Selective Injection | Beads | 현재 WI만 just-in-time 조회 |
| Just-in-Time Loading | Anthropic 공식 | ID만 유지, 필요 시 tool call로 로드 |

---

### 6-N. Context Sync 스킬 (`/oh-my-kanban:context-sync`)

#### 개요

현재 Claude Code 세션의 맥락과 Plane WI에 기재된 최신 내용을 비교하여,
세션에 없는 WI 정보(새 댓글, 상태 변경, 다른 세션의 진행상황)를 역으로 context에 주입한다.

**사용 시나리오**:
- 세션이 길어져 WI에 기록된 최신 결정사항을 놓쳤을 때
- 다른 세션(또는 다른 팀원)이 WI에 댓글을 남겨 맥락이 업데이트되었을 때
- compact 이후 자동 복원이 부족하다고 느낄 때 수동으로 전체 맥락 갱신
- 세션 중간에 Plane 웹 UI에서 WI를 수정한 후 세션에 반영하고 싶을 때

#### 구현 방식: MCP Tool + SKILL.md 하이브리드

##### SKILL.md (`plugin_data/skills/context-sync/SKILL.md`)

```yaml
---
name: context-sync
description: WI 맥락을 현재 세션에 동기화
---
```

Claude에게 `omk_context_sync` MCP tool을 호출하도록 지시하는 마크다운.

##### MCP Tool (`mcp/server.py`)

```python
@mcp.tool()
async def omk_context_sync() -> dict[str, Any]:
    """현재 세션의 WI 맥락을 Plane에서 최신 상태로 동기화한다."""
    # 1. 현재 세션의 PlaneContext에서 work_item_ids 조회
    # 2. build_plane_context() 호출 → WI 상세 + 댓글 조회
    # 3. last_sync_timestamp 기준으로 새 댓글 하이라이트
    # 4. WI 상태 변경 감지 및 보고
    # 5. 결과 반환 → Claude context에 자동 포함
```

#### 동기화 대상 데이터

| 데이터 | 소스 | 방향 | 우선순위 |
|--------|------|------|---------|
| WI 상태 (In Progress → Done 등) | Plane API | WI→세션 | 높음 |
| 새 댓글 (last_sync 이후) | Plane API | WI→세션 | 높음 |
| WI 설명 변경 | Plane API | WI→세션 | 중간 |
| Sub-task 상태 변경 | Plane API | WI→세션 | 중간 |
| 관련 WI 변경 | Plane API | WI→세션 | 낮음 |

#### Diff/비교 로직

**MVP (Phase 1)**: 비교 없이 전체 조회
- `build_plane_context()` 그대로 호출
- 새 댓글 하이라이트 없음, 전체 갱신
- 구현 즉시 가능

**Phase 2**: timestamp 기반 필터링
- `PlaneContext`에 `last_sync_timestamp: str` 추가
- 댓글의 `created_at`과 비교하여 새 댓글만 하이라이트
- 상태 변경 감지: `last_known_states: dict[str, str]` 추가

#### 출력 포맷 (Claude에게 주입되는 텍스트)

```
[omk context-sync 결과]
동기화 시각: 2026-03-07T12:15:00Z

📋 OMK-123: 로그인 API 구현
  상태: In Progress (변경 없음)
  설명: OAuth2 기반 로그인 엔드포인트...

  💬 새 댓글 (2개):
  - [홍길동 03-07 11:30] JWT 대신 opaque token 채택 결정
  - [bot 03-07 12:00] 작업 완료 — refresh_token 구현 완료

  📌 Sub-tasks:
  - [✅] 토큰 저장소 구현
  - [🔄] Refresh 엔드포인트 (진행 중)
  - [⬜] 로그아웃 엔드포인트 (미착수)
```

#### 에러 처리

- Plane API 실패 시: 에러 메시지 반환 (fail-open, Claude가 판단)
- 세션에 WI가 연결되지 않은 경우: "WI가 연결되지 않았습니다. /oh-my-kanban:omk-setup으로 설정하세요"
- 타임아웃: `plane_http_client()` 기본 타임아웃(10초) 활용

#### 다른 스킬과의 관계

| 스킬 | 관계 |
|------|------|
| `/omk-status` | status는 세션 로컬 상태 조회, context-sync는 원격 WI 동기화 |
| `/switch-task` (§6-J) | switch-task 후 자동으로 context-sync 호출 권장 |
| compact 복원 (§6-M) | compact 복원은 자동 pull, context-sync는 수동 pull |
| `/doctor` | doctor는 시스템 진단, context-sync는 맥락 진단 |

#### 구현 우선순위

1. SKILL.md 파일 추가 (즉시)
2. `omk_context_sync` MCP tool — `build_plane_context()` 재활용 (즉시)
3. `PlaneContext`에 `last_sync_timestamp` 추가 (Phase 2)
4. 새 댓글 하이라이트 + 상태 변경 감지 (Phase 2)
5. SessionStart resume 시 경량 자동 동기화 (Phase 3)

---

### 6-O. Context Injection 스킬 (`/oh-my-kanban:context-injection [work_item_id]`)

#### 개요

현재 세션에 연결되지 않은 **임의의 Work Item**의 맥락을 현재 세션에 주입한다.
context-sync(§6-N)가 "현재 WI 동기화"라면, context-injection은 "다른 WI 참조"이다.

**사용 시나리오**:
- 선행 작업(YCF-110)의 결정사항을 현재 작업(YCF-114)에서 참고할 때
- 관련 이슈의 댓글에 기록된 기술적 맥락을 현재 세션에 불러올 때
- 다른 팀원이 작업한 WI의 진행상황, 커밋, PR 정보를 확인할 때
- compact 후 손실된 이전 WI의 맥락을 수동으로 복원할 때

#### 필수 입력 강제

```
/oh-my-kanban:context-injection YCF-225    ← 정상 실행
/oh-my-kanban:context-injection            ← 거부: "Work Item ID가 필요합니다"
```

work_item_id 미입력 시 실행을 거부한다. 사용자 친화적 식별자(`YCF-225`)와
UUID 모두 허용하며, 식별자 입력 시 Plane API로 UUID 변환 후 조회한다.

#### 구현 방식: MCP Tool + SKILL.md

##### MCP Tool (`mcp/server.py`)

```python
@mcp.tool()
def omk_context_injection(
    work_item_id: str,
    session_id: str = "",
) -> dict[str, Any]:
    """지정한 Work Item의 맥락을 현재 세션에 주입한다.

    work_item_id 필수 — 미입력 시 거부.
    현재 세션에 연결되지 않은 WI도 조회 가능.
    """
    if not work_item_id or not work_item_id.strip():
        return {"error": "Work Item ID가 필요합니다. "
                "예: /oh-my-kanban:context-injection YCF-225"}

    # 1. 세션에서 Plane 설정 조회 (project_id, api_key 등)
    # 2. 식별자(YCF-225) → UUID 변환 (필요 시)
    # 3. _fetch_work_item() + _fetch_comments() 호출
    # 4. _build_wi_context()로 텍스트 변환 (확장 포맷)
    # 5. 결과 반환 → Claude context에 자동 포함
```

#### context-sync와의 차이

| | context-sync (§6-N) | context-injection (§6-O) |
|---|---|---|
| **대상** | 현재 세션에 연결된 WI | **임의의** WI |
| **목적** | 세션↔WI 동기화 | 다른 WI의 맥락 참조 |
| **필수 입력** | 없음 (자동) | WI ID 필수 |
| **사용 시나리오** | 최신 댓글 갱신 | 관련 이슈 참조, 선행 작업 맥락 획득 |

#### 출력 포맷

```
[omk context-injection 결과]
주입 시각: 2026-03-07T12:20:00Z
대상 WI: YCF-225

📋 YCF-225: OAuth2 인증 리팩토링
  상태: Done | 우선순위: High
  설명: 기존 세션 쿠키 기반 인증을 OAuth2 + opaque token 방식으로 전환...

  🔗 작업 이력:
  - Branch: feat/oauth2-refactor
  - PR: https://github.com/ej31/oh-my-kanban/pull/42
  - Commits: abc1234, def5678

  💬 댓글 (3개):
  - [홍길동 03-05] JWT 대신 opaque token 채택 — 이유: 내부 서비스간 통신에 payload 불필요
  - [bot 03-06] 작업 완료 — refresh_token 구현, 로그아웃 엔드포인트 추가
  - [김철수 03-07] 코드 리뷰 완료 — rate limiting 추가 권고
```

#### 에러 처리

- WI ID 미입력: `{"error": "Work Item ID가 필요합니다"}` — 실행 거부
- WI 미존재 (404): `{"error": "WI를 찾을 수 없습니다: YCF-225"}`
- Plane API 실패: fail-open, 에러 메시지 반환
- 프로젝트 경계: 현재 세션의 `project_id`와 동일 프로젝트의 WI만 조회 (Phase 1)

#### 구현 우선순위

1. SKILL.md 파일 추가 (즉시)
2. `omk_context_injection` MCP tool 구현 — `_fetch_work_item()` + `_fetch_comments()` 재활용 (즉시)
3. 식별자(YCF-225) → UUID 변환 로직 (Phase 1)
4. 크로스 프로젝트 WI 조회 지원 (Phase 2)

---

### 6-P. WI 작업 이력 기록 표준 (Work History Recording Standard)

#### 목적

context-injection(§6-O)과 context-sync(§6-N)가 효과적으로 동작하려면,
WI 댓글에 **재현 가능한 작업 이력**이 기록되어야 한다.
"무엇을 했는지"만이 아닌 "어디서, 어떤 코드로, 어떤 흐름으로" 했는지를
다른 세션이 주입받았을 때 즉시 이해하고 이어갈 수 있어야 한다.

#### 필수 기록 항목

| 항목 | 형식 | 예시 | 기록 시점 |
|------|------|------|----------|
| Repository URL | `https://github.com/{user}/{repo}` | `https://github.com/ej31/oh-my-kanban` | 착수 시 |
| Branch 이름 | `{type}/{description}` | `feat/oauth2-refactor` | 착수 시 |
| Commit ID (링크) | `https://github.com/{user}/{repo}/commit/{hash}` | `https://github.com/ej31/oh-my-kanban/commit/abc1234` | 커밋 시 |
| PR URL | `https://github.com/{user}/{repo}/pull/{number}` | `https://github.com/ej31/oh-my-kanban/pull/42` | PR 생성 시 |
| 변경 파일 목록 | `file:line` 패턴 | `src/auth/token_store.py:36` | 완료 시 |
| 배포 상태 | `deployed` / `staging` / `not deployed` | `staging 환경 배포 완료` | 배포 시 |

#### 댓글 기록 템플릿

##### 착수 시

```markdown
작업 시작
- Repository: https://github.com/ej31/oh-my-kanban
- Branch: `feat/oauth2-refactor`
- 접근 방법: 기존 세션 쿠키를 opaque token으로 교체
- 영향 파일: src/auth/token_store.py, src/auth/login.py, src/auth/middleware.py
- 완료 기준: 기존 테스트 통과 + OAuth2 flow e2e 테스트 추가
```

##### 커밋/PR 시

```markdown
코드 푸시
- Commit: https://github.com/ej31/oh-my-kanban/commit/abc1234
- PR: https://github.com/ej31/oh-my-kanban/pull/42
- 변경 요약: token_store.py에 refresh_token 갱신 로직 추가
- 테스트: `pytest tests/auth/ -v` 전체 통과 (12/12)
```

##### 완료 시

```markdown
작업 완료
- Branch: `feat/oauth2-refactor`
- PR: https://github.com/ej31/oh-my-kanban/pull/42 (merged)
- Commits: abc1234, def5678, ghi9012
- 변경 파일:
  - src/auth/token_store.py:36 — refresh_token 저장/갱신
  - src/auth/login.py:15 — OAuth2 flow 진입점
  - src/auth/middleware.py:42 — 토큰 검증 미들웨어
- 결정 이유: JWT 대신 opaque token (내부 통신에 payload 불필요)
- 기각된 대안: JWT — 토큰 크기, 무효화 어려움
- 다음 작업: rate limiting 추가 (코드 리뷰 권고 반영)
```

#### 자동화 구현

`session_end.py`의 `_build_summary_comment()`와 `hooks/post_tool.py`를 확장하여
git 정보를 자동 수집하고 WI 댓글에 포함한다.

```python
# 자동 수집 대상
git_context = {
    "repository": "git remote get-url origin",
    "branch": "git branch --show-current",
    "recent_commits": "git log --oneline -5",
    "changed_files": "git diff --name-only HEAD~1",
}
```

| 수집 항목 | 수집 시점 | Hook |
|----------|----------|------|
| Repository URL | SessionStart | `session_start.py` |
| Branch 이름 | SessionStart | `session_start.py` |
| 최근 커밋 | SessionEnd | `session_end.py` |
| 변경 파일 | PostToolUse (Write/Edit) | `post_tool.py` (기존 확장) |
| PR URL | SessionEnd (gh CLI 활용) | `session_end.py` |

#### context-injection과의 연계

WI 댓글에 위 형식으로 기록되어 있으면, context-injection으로 다른 WI를 주입받았을 때:
1. **코드 위치 즉시 파악**: `file:line` 패턴으로 해당 코드로 바로 이동
2. **변경 이력 추적**: commit 링크로 diff 확인 가능
3. **분기 전략 이해**: branch 이름으로 작업 맥락 파악
4. **리뷰 상태 확인**: PR URL로 리뷰 코멘트, 승인 상태 확인
5. **결정 맥락 복원**: "왜 이 방식을 선택했는지" + "무엇을 기각했는지" 즉시 파악

기록이 부실하면 context-injection의 효과가 반감된다.
**"주입받을 맥락의 품질은 기록의 품질에 비례한다."**

---

### 6-Q. Task Format 시스템 (Customizable WI Comment Templates)

#### 목적

§6-P에서 정의한 WI 작업 이력 기록 표준은 **무엇을 기록할지**를 규정한다.
§6-Q는 **어떤 형태로 기록할지**를 정의한다.

현재 `session_end.py`의 `_build_summary_comment()`는 포맷이 하드코딩되어 있어,
사용자가 댓글 형식을 변경하려면 Python 코드를 직접 수정해야 한다.

Task Format 시스템은 `.omk/` 디렉토리에 Mustache 스타일 템플릿 파일을 두고,
코드 수정 없이 WI 댓글 포맷을 커스터마이즈할 수 있게 한다.

**핵심 원칙**: "댓글의 **내용**은 omk가 자동 수집하고, **형태**는 사용자가 결정한다."

#### 파일 구조

```
{project_root}/
└── .omk/
    ├── task-config.json           # 설정 파일 (어떤 포맷 파일을 사용할지)
    ├── task-format.md             # 사용자 커스텀 포맷 템플릿
    └── task-format.example.md     # 기본 예시 (복사해서 수정용)
```

| 파일 | 역할 | Git 추적 |
|------|------|----------|
| `task-config.json` | 포맷 파일 경로 + 사용자 설정 | 권장 (팀 공유) |
| `task-format.md` | 실제 사용되는 커스텀 템플릿 | 권장 (팀 공유) |
| `task-format.example.md` | 기본 예시 템플릿 (참고용) | 권장 |

#### 설정 스키마 (`task-config.json`)

```json
{
  "format_file": "./task-format.md",
  "comment_types": {
    "session_start": "./formats/session-start.md",
    "session_end": "./formats/session-end.md",
    "task_switch": "./formats/task-switch.md",
    "opt_out": "./formats/opt-out.md"
  }
}
```

- `format_file`: 단일 템플릿으로 모든 댓글 유형을 통일 (기본값).
- `comment_types`: 댓글 유형별로 다른 템플릿을 사용 (선택적 확장).
- 경로는 `.omk/` 기준 상대 경로.

#### 변수 치환 시스템

**문법**: ``&#123;&#123;variable_name&#125;&#125;``

미치환 변수는 제거하지 않고 원본 그대로 유지한다 (디버깅 용이).

조건부 블록:
``&#123;&#123;#if var&#125;&#125;...&#123;&#123;/if&#125;&#125;``
변수가 존재하고 비어있지 않으면 블록 렌더링.

주요 자동 수집 변수:

| 변수명 | 수집 원본 | 예시 값 |
|--------|----------|---------|
| ``&#123;&#123;session_id&#125;&#125;`` | `state.session_id[:8]` | `a1b2c3d4` |
| ``&#123;&#123;scope_summary&#125;&#125;`` | `state.scope.summary` | `로그인 API 테스트` |
| ``&#123;&#123;files_touched&#125;&#125;`` | 수정된 파일 포맷 목록 | `` - `auth.py` `` |
| ``&#123;&#123;branch&#125;&#125;`` | `git branch --show-current` | `feat/oauth2-refactor` |
| ``&#123;&#123;commit_url&#125;&#125;`` | `{repository}/commit/{hash}` | `https://github.com/.../commit/abc` |
| ``&#123;&#123;pr_url&#125;&#125;`` | `gh pr view --json url` | `https://github.com/.../pull/42` |
| ``&#123;&#123;total_prompts&#125;&#125;`` | `state.stats.total_prompts` | `23` |
| ``&#123;&#123;drift_warnings&#125;&#125;`` | `state.stats.drift_warnings` | `1` |

전체 변수 목록: `src/oh_my_kanban/session/task_format.py` 참조.

#### 로딩 우선순위 (fail-open)

```
task-config.json → comment_types[type]
  └─ 없으면 → format_file 경로
        └─ 없으면 → .omk/task-format.md
                └─ 없으면 → 내장 기본 포맷 (_DEFAULT_TEMPLATE)
```

어떤 상황에서도 댓글 생성이 실패하지 않는다.
파일 없음/파싱 실패 시 경고 로그(`[omk] ...`) + 내장 기본 포맷 사용.

#### §6-P와의 관계

| §6-P (무엇을 기록할지) | §6-Q (어떻게 기록할지) |
|----------------------|---------------------|
| Repository URL 기록 필수 | ``&#123;&#123;repository&#125;&#125;`` 변수로 자동 주입 |
| Branch 이름 기록 필수 | ``&#123;&#123;branch&#125;&#125;`` 변수로 자동 주입 |
| Commit ID (링크) 기록 필수 | ``&#123;&#123;commit_url&#125;&#125;`` 변수로 자동 주입 |
| PR URL 기록 필수 | ``&#123;&#123;pr_url&#125;&#125;`` 변수로 자동 주입 |
| 변경 파일 목록 기록 필수 | ``&#123;&#123;files_touched&#125;&#125;`` 변수로 자동 주입 |
| 결정 이유, 기각된 대안 | `omk_add_comment` MCP로 사용자 수동 기록 |

#### 구현 우선순위

| 단계 | 작업 | 공수 |
|------|------|------|
| **P0** | `task_format.py` 신규 모듈 (로딩 + 치환 + 변수 수집) | S |
| **P0** | `session_end.py` `_build_summary_comment` 리팩토링 | S |
| **P1** | `task-format.example.md` 자동 생성 (`omk init` 확장) | XS |
| **P1** | `task-config.json` 로딩 + `comment_types` 지원 | S |
| **P1** | 유닛 테스트 (로딩 우선순위, 치환, fallback) | M |
| **P2** | ``&#123;&#123;#each&#125;&#125;`` 반복 블록 지원 | S |
| **P3** | 필터/파이프 (`\|truncate`, `\|date`) 지원 | M |

공수 기준: XS = 30분 이내, S = 1~2시간, M = 반나절

---

### 6-R. 기록 모드 표준 (Recording Mode Standard)

#### 목적

§6-P의 WI 작업 이력 기록 표준은 **무엇을 기록할 것인가**를 정의한다.
§6-R은 **얼마나 깊이 기록할 것인가**를 정의한다.

세 가지 모드(`detailed`, `normal`, `eco`)를 제공하여 토큰 사용량과 맥락 복원율의
트레이드오프를 사용자가 제어할 수 있게 한다.

#### 모드 요약

| 모드 | 댓글 시점 | Sub-task 분해 | 세션당 댓글 | 맥락 복원 | 세션당 토큰(추정) |
|------|----------|--------------|-----------|----------|--------------------|
| `detailed` | 착수, 분해, 결정, 블로커, 커밋, PR, 완료 (7종) | 적극적 | 15~18 | 100% | ~4,600 |
| `normal` | 착수, 커밋, 완료 (3종) | 필요시 | 5~6 | 80% | ~1,100 |
| `eco` | 착수, 완료 (2종) | 최소화 | 2~3 | 50% | ~210 |

#### 설정

```yaml
# 프로젝트 CLAUDE.md
omk_recording_mode: normal  # 기본값. detailed | normal | eco
```

설치 위저드(Setup Wizard)에서 선택하거나, CLAUDE.md에 직접 기입한다.
세션 시작 시 `session_start.py`가 이 값을 읽어 기록 깊이를 결정한다.

#### 모드별 기록 행위

##### `detailed`

| 시점 | 행위 |
|------|------|
| SessionStart | 착수 댓글 + 대안 분석 기록 |
| WI 분해 | sub-task WI 생성 + 분해 근거 댓글 |
| 중요 분기점 | 결정/발견 댓글 (코드 스니펫 포함) |
| 블로커 | 블로커 댓글 + 시도 내역 |
| git commit | 커밋 댓글 (commit URL + 핵심 diff) |
| PR 생성 | PR 댓글 (PR URL + 변경 파일 목록) |
| SessionEnd | 완료 댓글 (전체 요약 + 기각 대안 + 다음 작업) |

**주의**: 이 모드는 토큰 사용량이 normal 대비 약 4배이다. 세션 시작 시 비용 안내 메시지를 표시한다.

##### `normal` (기본값)

| 시점 | 행위 |
|------|------|
| SessionStart | 착수 댓글 (§6-P 기본 템플릿) |
| git commit | 커밋 댓글 (commit URL + 변경 요약) |
| SessionEnd | 완료 댓글 (§6-P 기본 템플릿) |

코드 스니펫 대신 commit URL로 대체. 중요 결정사항은 완료 댓글에 간결하게 기록.

##### `eco`

| 시점 | 행위 |
|------|------|
| SessionStart | 착수 댓글 (Branch + 1줄 목표) |
| SessionEnd | 완료 댓글 (Branch + commit 해시 목록 + 변경 파일) |

sub-task 분해, 결정 기록, 커밋 댓글을 생략한다.

#### 댓글 템플릿 파일

`.omk/task-format-preset/` 디렉토리에 모드별 템플릿 배치 (§6-S Preset 시스템 연계).

```
.omk/task-format-preset/
├── detailed.md    # 7종 댓글 템플릿
├── normal.md      # 3종 댓글 템플릿
└── eco.md         # 2종 댓글 템플릿
```

#### context-injection 복원율 매핑

| 복원 항목 | detailed | normal | eco |
|----------|----------|--------|-----|
| 무슨 작업인지 | O | O | O |
| 어떤 파일을 바꿨는지 | O (file:line) | O (file:line) | O (file만) |
| 왜 이 방법을 선택했는지 | O (상세) | O (간략) | X |
| 기각된 대안 | O | O (간략) | X |
| 코드 수준 diff | O (스니펫) | X (commit URL) | X |
| 중간 결정 과정 | O (댓글별) | X | X |
| 블로커/장애 이력 | O | X | X |
| 이어서 할 작업 | O | O | X |

#### 모드 선택 가이드

```
Q1. WI를 다른 세션이나 다른 사람이 읽는가?
├── 예 → Q2. 팀 3명+ 또는 장기(6개월+) 프로젝트인가?
│   ├── 예 → detailed
│   └── 아니오 → normal
└── 아니오 → Q3. 비용 절감이 최우선인가?
    ├── 예 → eco
    └── 아니오 → normal
```

기본값은 `normal`. 대부분의 사용자에게 비용 대비 맥락 복원율이 최적이다.

#### 구현 우선순위

| 단계 | 작업 | 공수 |
|------|------|------|
| **P0** | CLAUDE.md `omk_recording_mode` 파싱 | XS |
| **P0** | `session_start.py` / `session_end.py` 모드 분기 | S |
| **P1** | `detailed` 모드 — 결정/발견 댓글 자동화 | M |
| **P1** | `detailed` 모드 — 커밋/PR 댓글 (git hook 연동) | M |
| **P2** | 설치 위저드 Step에 모드 선택 UI 추가 | S |

---

### 6-S. Task Format Preset 시스템

#### 목적

기록 모드(§6-R)와 WI 댓글 포맷(§6-Q)을 **파일 기반 preset**으로 묶어 관리한다.
IntelliJ 테마 시스템에서 착안: 내장 preset 3종 + 사용자 커스텀 preset.

설치 직후 `normal` preset으로 즉시 동작. `omk preset use <name>` 한 명령으로 전환.

#### 핵심 개념

| 개념 | IntelliJ 대응 | omk 대응 |
|------|-------------|---------|
| 내장 테마 | Darcula, IntelliJ Light | `detailed.md`, `normal.md`, `eco.md` |
| 사용자 테마 | 커스텀 색상 스킴 | `.omk/task-format-preset/my-custom.md` |
| 활성 테마 | 현재 적용된 테마 | `.omk/task-format.md` (활성 preset의 복사본) |
| 테마 설정 | Settings > Appearance | `omk preset use <name>` / `task-config.json` |

#### 디렉토리 구조

```
.omk/
├── task-config.json              ← active_preset 지정
├── task-format.md                ← 현재 활성 포맷 (hooks가 참조)
└── task-format-preset/
    ├── _index.json               ← preset 레지스트리
    ├── detailed.md               ← 내장 (bundled)
    ├── normal.md                 ← 내장 (bundled, 기본값)
    ├── eco.md                    ← 내장 (bundled)
    └── {user-preset}.md          ← 사용자 생성
```

#### Preset 메타데이터 (YAML Front Matter)

각 preset 파일 상단에 YAML front matter로 메타데이터를 포함한다.

```yaml
---
name: "Normal Mode"
description: "표준 기록 수준"
token_estimate: "medium"    # low | medium | high
author: "oh-my-kanban"
version: "1.0"
category: "bundled"         # bundled | user
---
```

#### CLI 명령어

| 명령 | 설명 | Phase |
|------|------|-------|
| `omk preset list` | preset 목록 + 활성 표시 | 1 |
| `omk preset use <name>` | preset 전환 | 1 |
| `omk preset show <name>` | preset 미리보기 | 1 |
| `omk preset create <name>` | 현재 포맷을 preset으로 저장 | 1 |
| `omk preset diff [name]` | 활성 포맷과 비교 | 2 |
| `omk preset reset` | 활성 preset 원본 복원 | 2 |
| `omk preset import <path>` | 외부 preset 가져오기 | 2 |
| `omk preset export <name>` | preset 내보내기 | 2 |
| `omk preset delete <name>` | 사용자 preset 삭제 | 2 |

단축 경로: `omk config set preset <name>` → `omk preset use <name>` 위임.

#### 전환 데이터 흐름

```
omk preset use detailed
  → preset 존재 확인
  → task-format.md 변경 감지 (hash 비교)
  → preset 본문 → task-format.md 복사 (front matter 제외)
  → task-config.json 갱신 (active_preset, hash, timestamp)
  → 다음 세션부터 새 포맷 적용
```

#### 불변량

1. `task-format.md` ≡ 활성 preset 본문의 복사본 (사용자 수정 전까지)
2. 내장 preset은 사용자가 수정/삭제 불가. 패키지 업데이트 시 덮어쓰기
3. 사용자 preset은 패키지 업데이트에 영향받지 않음
4. preset 전환은 진행 중 세션에 영향 없음 (다음 세션부터 적용)

#### Hooks 연동

| 훅 | preset 역할 |
|----|------------|
| SessionStart | `task-format.md` 로딩 → 기록 포맷 결정 |
| SessionEnd | 포맷 기반 종료 댓글 생성 |
| PostToolUse | 포맷 기반 파일 변경 기록 상세도 |
| UserPromptSubmit | 포맷 기반 드리프트 감지 댓글 수준 |

#### 구현 우선순위

| 단계 | 작업 | 공수 |
|------|------|------|
| **P1** | `commands/preset.py` 신규 — `list`, `use`, `show`, `create` | M |
| **P1** | 내장 preset 3종 파일 (`detailed.md`, `normal.md`, `eco.md`) | S |
| **P1** | `task-config.json` `active_preset` + hash 관리 | S |
| **P1** | `_index.json` 레지스트리 자동 갱신 | S |
| **P1** | `cli.py`에 `preset` 그룹 등록 | XS |
| **P2** | `omk preset diff`, `reset` | S |
| **P2** | `omk preset import/export` | M |
| **P2** | `omk preset delete` (사용자 preset 한정) | S |

---

### 6-T. 문서 사이트 (GitHub Pages)

#### 목적

oh-my-kanban의 사용법, Task Format 시스템(§6-Q~§6-S), 레퍼런스를
한글/영어 이중 언어로 제공하는 공식 문서 사이트를 구축한다.

#### 기술 스택

| 항목 | 선택 | 근거 |
|------|------|------|
| 정적 사이트 생성기 | VitePress | 네이티브 i18n, Vite 빌드 성능, ~50KB 번들 |
| 호스팅 | GitHub Pages | 무료, GitHub Actions 통합 |
| i18n | `/ko/`, `/en/` prefix | 한글 기본, 파일 기반 번역 관리 |
| 배포 | `docs/**` 변경 시 자동 | path filter로 코드 CI와 분리 |

MkDocs 기각: i18n이 플러그인 의존으로 언어별 사이드바 구성이 번거로움.
Docusaurus 기각: React 200KB+ 번들이 CLI 도구 문서에 과잉.

#### Repository 전략

기존 `ej31/oh-my-kanban` repo의 `/docs` 디렉토리에 VitePress 프로젝트 배치.
코드 변경과 문서 변경이 같은 PR에 포함되어 불일치를 방지한다.

```
oh-my-kanban/
└── docs/
    ├── .vitepress/
    │   ├── config.mts             # i18n, 사이드바, 테마
    │   └── theme/custom.css       # Indigo #6366F1 브랜딩
    ├── ko/                        # 한국어 (기본)
    │   ├── getting-started.md
    │   ├── guide/
    │   │   ├── task-format.md     # §6-Q 반영
    │   │   ├── recording-modes.md # §6-R 반영
    │   │   └── preset-system.md   # §6-S 반영
    │   └── reference/
    └── en/                        # 영어 (동일 구조)
```

#### i18n

URL: `https://ej31.github.io/oh-my-kanban/ko/` (한글 기본), `/en/` (영어).

번역 관리: 한글 문서 우선 작성 후 영어 번역.
영어 문서 frontmatter에 `translatedFrom: ko` + `lastSynced: YYYY-MM-DD` 기록.

#### 배포 파이프라인

```yaml
# .github/workflows/docs.yml
on:
  push:
    branches: [main]
    paths: ['docs/**']   # 문서 변경 시에만 배포 트리거
```

GitHub Actions `actions/deploy-pages@v4` 활용.
`fetch-depth: 0`으로 VitePress `lastUpdated` 기능 활성화.

#### 디자인

- **Primary**: Indigo `#6366F1` (omk Label 색상과 일치)
- **코드 폰트**: JetBrains Mono / Fira Code
- **코드 중심 레이아웃**: CLI 도구에 맞게 코드 블록 우선
- **다크 모드**: VitePress 내장 토글

#### 문서 구조

```
/ko/ (한국어, 기본)
├── Getting Started
├── Guide/
│   ├── Task Format Guide (§6-Q)
│   ├── Recording Modes (§6-R)
│   ├── Preset System (§6-S)
│   └── AI Agent Integration
├── Reference/
│   ├── Configuration
│   ├── Template Variables
│   ├── CLI Commands
│   └── Environment Variables
├── Advanced/
│   ├── Custom Templates
│   └── Provider Adapters
└── FAQ
```

`/en/`은 동일 구조의 영어 번역.

#### 구현 우선순위

| Phase | 작업 | 공수 |
|-------|------|------|
| **P1** | VitePress 초기화 + i18n 설정 + GitHub Actions 파이프라인 | M |
| **P2** | 랜딩, Getting Started, CLI Commands, Configuration Reference (ko) | L |
| **P2** | Task Format Guide, Recording Modes, Preset System (ko) | M |
| **P3** | 전체 영어 번역 | L |
| **P3** | Advanced: Custom Templates, Provider Adapters | M |

공수 기준: XS = 30분, S = 1~2시간, M = 반나절, L = 1~2일

---

### 6-U. Snapshot 스킬 (`/oh-my-kanban:snapshot`)

#### 개요

현재 세션의 작업 상태를 Plane WI에 **스냅샷으로 영속화**하는 단발성 스킬.
context-sync(§6-N)가 "WI→세션 pull"이라면, snapshot은 **"세션→WI push"** 방향이다.

**사용 시나리오**:
- compact 임박 시 현재 맥락 보존
- 중요 결정 직후 다른 세션/팀원용 기록
- 긴 세션 중간 체크포인트
- 디버깅 중 가설/시도 내역 보존

#### 구현 방식: MCP Tool + SKILL.md 하이브리드

##### SKILL.md (`plugin_data/skills/snapshot/SKILL.md`)

Claude에게 현재 맥락을 정리한 뒤 `omk_snapshot` MCP tool을 호출하도록 지시하는 마크다운.

1단계: 주요 결정사항, 미해결 이슈, 다음 계획, 맥락 요약을 정리
2단계: `omk_snapshot` MCP tool 호출
3단계: 생성된 Sub-task ID + 댓글 결과를 사용자에게 보고

##### MCP Tool (`mcp/server.py`)

```python
@mcp.tool()
def omk_snapshot(
    decisions: str,
    blockers: str = "없음",
    next_steps: str = "",
    context_summary: str = "",
    trigger: str = "manual",
    session_id: str = "",
) -> dict[str, Any]:
    """현재 세션의 작업 상태를 Plane WI에 스냅샷으로 기록한다."""
    # 1. 세션 상태 로드 → 자동 수집 (scope, files, timeline, git)
    # 2. Main WI의 sub-task로 스냅샷 WI 생성 (parent=main_wi_id)
    # 3. Main WI에 참조 댓글 추가 (omk_add_comment 로직 재활용)
    # 4. 세션 타임라인에 snapshot 이벤트 추가
    # 5. 결과 반환
```

#### 기록 위치: 댓글 기반 참조 (Option A)

Sub-task WI를 생성하고, Main WI **댓글**에 sub-task ID를 참조한다.

**선택 근거**:
1. 원자성 — 댓글은 append-only, description 덮어쓰기의 race condition 회피
2. 구현 경제성 — 2 API calls (sub-task 생성 + 댓글) vs Option B/C의 3-4 calls
3. §6-P 패턴 정합 — 모든 기록이 댓글 기반, 일관성 유지
4. Sub-task 목록이 Plane UI에서 인덱스 역할

**Phase 2 확장**: 스냅샷 5개+ 실사용 패턴 확인 시 description에 Compact Timeline 테이블 추가.

#### 스냅샷 수집 항목

| 구분 | 항목 | 소스 |
|------|------|------|
| 자동 | 작업 목표 | `scope.summary` |
| 자동 | 수정 파일 | `stats.files_touched` (file:line) |
| 자동 | 진행 통계 | `stats.total_prompts`, `stats.drift_warnings` |
| 자동 | 타임라인 | `timeline` (최근 10개) |
| 자동 | git 상태 | branch, 최근 커밋, 미커밋 변경 |
| Claude | 주요 결정 + 이유 | `decisions` 파라미터 |
| Claude | 미해결 이슈 | `blockers` 파라미터 |
| Claude | 다음 계획 | `next_steps` 파라미터 |
| Claude | 맥락 요약 | `context_summary` 파라미터 |

#### 에러 처리

- WI 미연결: 실행 거부 + 안내 메시지
- decisions 빈 문자열: 실행 거부
- Sub-task 생성 실패: Main WI 댓글에 전체 내용 직접 기록 (fallback)
- 댓글 추가 실패: 경고 + sub-task ID만 반환
- git 실패: 해당 필드 대체 텍스트, 나머지 정상 진행

#### 다른 스킬과의 관계

| 스킬 | 관계 |
|------|------|
| context-sync (§6-N) | 역방향 — sync는 WI→세션, snapshot은 세션→WI |
| context-injection (§6-O) | 직교 — injection은 다른 WI 참조, snapshot은 현재 WI 기록 |
| §6-P 기록 표준 | sub-task description은 §6-P 템플릿 준수 |
| §6-R Recording Mode | eco 모드 시 자동 수집 항목 축소 |
| compact 복원 (§6-M) | snapshot은 수동 push, compact 복원은 자동 pull |

#### 구현 우선순위

| 단계 | 작업 | 공수 |
|------|------|------|
| **P0** | SKILL.md 파일 추가 | XS |
| **P0** | `omk_snapshot` MCP tool — 세션 수집 + sub-task 생성 + 댓글 참조 | M |
| **P0** | Sub-task 생성 실패 시 댓글 fallback | S |
| **P1** | git 상태 자동 수집 (`subprocess` 기반) | S |
| **P1** | 세션 타임라인에 `snapshot` 이벤트 타입 추가 | XS |
| **P2** | §6-Q Task Format 연동 — snapshot description에 변수 치환 적용 | S |
| **Phase 2** | description에 Compact Timeline 테이블 추가 (스냅샷 5개+ 확인 후) | M |

---

### 6-V. 프로젝트 분석 (Project Analysis)

WI에 축적된 기록을 소비하는 핵심 접점. "왜 WI를 쓰는가?"에 대한 답.

#### 스킬 목록

| 스킬 | 레벨 | 소요 시간 | 출력 | Phase |
|------|------|----------|------|-------|
| `/oh-my-kanban:analyze-project-lv1` | Quick Overview | ~1분 | 인라인 | 2 |
| `/oh-my-kanban:analyze-project-lv2` | Structural Analysis | ~5분 | `.omk/reports/` + 인라인 요약 | 2 |
| `/oh-my-kanban:analyze-project-lv3` | Deep Analysis | ~15분 | 상세 보고서 + Mermaid 다이어그램 | 3 |

각 레벨은 누적 구조: lv2 = lv1 전체 + 추가 분석, lv3 = lv2 전체 + 추가 분석.

#### 데이터 흐름

```
WI 댓글 (기록 모드별 깊이)
     ↓
 [댓글 파서] ← COMMENT_PATTERNS
     ↓
 결정 타임라인 / 기술 부채 / 세션 통계
     ↓                    ↓
  git 히스토리 보완     코드 구조 분석 (lv2+)
     ↓                    ↓
 [분석 엔진]  ←──────────┘
     ↓
 보고서 생성 (인라인 / 파일 / Mermaid)
```

#### 레벨별 분석 항목

**lv1 — Quick Overview**:
- WI 통계 (상태별 분포, 완료율)
- 세션 통계 (총 세션 수, 평균 프롬프트/파일 수, 드리프트 경고)
- 최근 활동 (최근 10개 WI)
- 기술 스택 (`pyproject.toml` / `package.json`)

**lv2 — Structural Analysis** (lv1 포함):
- 디자인 패턴 추론 (코드 구조 시그널 기반)
- 주요 결정 타임라인 (`## 결정` 댓글 파싱 → 시계열)
- 기술 부채 식별 (핫스팟 파일, 장기 미완료 WI)
- 모듈/기능 구조 (디렉토리 트리 + Module/Label 매핑)
- 보고서 파일: `.omk/reports/structural-analysis-{date}.md`

**lv3 — Deep Analysis** (lv2 포함):
- 아키텍처 다이어그램 (Mermaid C4/flowchart, import 분석 기반)
- 의존성 그래프 (모듈 간 관계, 순환 의존성 감지)
- 코드 품질 메트릭 (파일별 수정 빈도, 커밋 추이)
- 팀 기여 분석 (`git shortlog`, 영역별 Bus Factor)
- 리스크 분석 (단일 장애점, 테스트 커버리지, 높은 결합도)
- 개선 제안 (우선순위별, 데이터 기반)
- 보고서 파일: `.omk/reports/project-analysis-{date}.md`

#### 핵심 가치

1. **기록의 소비자**: WI 댓글이 단순 로그가 아닌 분석 데이터로 활용됨
2. **적응적 깊이**: 기록 모드(detailed/normal/eco)에 맞춰 가용 데이터 활용
3. **git 폴백**: 댓글이 부족해도 git 히스토리로 최소한의 분석 가능
4. **점진적 가치**: lv1은 즉시 가치 제공, lv3는 데이터 축적 후 풍부한 인사이트

#### 별칭

| 별칭 | 원본 |
|------|------|
| `/omk:ap1` | `/oh-my-kanban:analyze-project-lv1` |
| `/omk:ap2` | `/oh-my-kanban:analyze-project-lv2` |
| `/omk:ap3` | `/oh-my-kanban:analyze-project-lv3` |

#### 출력 디렉토리

`.omk/reports/` — 프로젝트 루트에 생성. `.gitignore`에 `.omk/` 추가 권장.
날짜 기반 파일명으로 분석 히스토리 보존. 동일 날짜 재실행 시 덮어쓰기.

#### 구현 전략

프롬프트 기반 스킬 (`.claude/skills/omk-analyze-lv*.md`)로 구현.
Claude Code의 기존 도구(Read, Glob, Grep, Bash)를 조합하여 분석 수행.
별도 Python 코드 불필요 — 스킬 프롬프트가 분석 절차를 지시.

Phase 3+ 최적화: MCP 도구 `omk_project_stats`로 세션 통계 수집 효율화.

#### 접점 우선순위

| 우선순위 | 스킬 | Phase |
|---------|------|-------|
| P1 | `/oh-my-kanban:analyze-project-lv1` | 2 |
| P1 | `/oh-my-kanban:analyze-project-lv2` | 2 |
| P2 | `/oh-my-kanban:analyze-project-lv3` | 3 |

---

## 7. 긴급 수정 사항

### `opt_out.py`의 `_delete_work_items` 제거 필요

**문제**: 세션 A가 opt-out하면서 WI를 삭제하면, 같은 WI를 참조 중인 세션 B의 기여가 사라짐.
**해결**: `_delete_work_items` 함수 제거. WI는 세션이 삭제할 수 있는 대상이 아님.
**대안**: 삭제 대신 "이 세션이 더 이상 기여하지 않습니다" 댓글로 대체.

---

## 8. 데이터 보관 정책

### 로컬 세션 파일

| 상태 | 보관 기간 |
|------|----------|
| Active | 무기한 |
| Completed | 30일 (핵심 데이터는 WI 댓글에 이미 업로드) |
| Opted Out | 7일 |

### 원격 데이터 (Plane/Linear/GitHub)

| 데이터 | 정책 |
|--------|------|
| WI 댓글 | 영구 (WI와 함께 보존) |
| WI 자체 | Archived 상태로 영구 보존 (삭제 안 함) |

---

## 9. 구현 우선순위

### Phase 1: 핵심 구조 (P0)

1. `PlaneContext` 확장 (`main_task_id`, `focused_work_item_id`, 폴링 상태)
2. `WiModeConfig` 데이터클래스 + Config 확장 (`task_mode`, `upload_level`)
3. Setup Wizard Step 3, 4 추가
4. `opt_out.py`의 `_delete_work_items` 제거/변경
5. Label 자동 생성 + 부착 (`omk:session`, `omk:type:main/sub`)
6. **fail-open with transparency** — `HookDiagnostic` + `notify_and_exit` + 에러 분류 체계 (§6)

### Phase 2: 세션 연동 강화 (P1)

6. Mode A(MainTask-Subtask) Plane 구현 — 세션 시작 시 MainTask 자동 생성
7. 세션 시작/종료 구조화 댓글 + 핸드오프 메타데이터
8. 자동 상태 전이 (세션 시작→In Progress, 종료→Completed)
9. 시크릿 필터링 (`sanitize_comment`)
10. UserPromptSubmit 댓글 폴링 (throttle + deadline + circuit breaker)

### Phase 3: 확장 (P2)

11. Mode B(Module-Task-Subtask) Plane 구현
12. 자동 아카이브 배치 로직
13. Linear 확장 (label create, parentId, label filter)
14. Git 커밋 해시 연동

### Phase 4: 추가 플랫폼 (P3)

15. GitHub stub 구현 (gh CLI 래핑)
16. `omk stats` 분석 명령 (데이터 축적 후)

### Phase 5: Task Format 시스템 (§6-Q~§6-S)

17. `task_format.py` 신규 모듈 — 템플릿 로딩 + Mustache 변수 치환 (§6-Q, P0)
18. `session_end.py` `_build_summary_comment` 리팩토링 → 템플릿 기반 (§6-Q, P0)
19. CLAUDE.md `omk_recording_mode` 파싱 + SessionStart/End 분기 (§6-R, P0)
20. `detailed` 모드 — 결정/발견·커밋·PR 댓글 자동화 (§6-R, P1)
21. `commands/preset.py` 신규 + 내장 preset 3종 bundled (§6-S, P1)
22. 설치 위저드 Step에 기록 모드 선택 UI 추가 (§6-R/§6-S, P2)

### Phase 6: 문서 사이트 (§6-T)

23. VitePress 초기화 + i18n 설정 (`/ko/`, `/en/`) + GitHub Actions 파이프라인 (P1)
24. 핵심 문서 작성 — Getting Started, CLI Commands, Configuration Reference (ko) (P2)
25. Task Format Guide, Recording Modes, Preset System 문서 (ko) (P2)
26. 전체 영어 번역 + Advanced 섹션 (P3)

### Phase 7: 스킬 확장 (§6-U~§6-V)

27. `/oh-my-kanban:snapshot` SKILL.md 추가 (§6-U, P0)
28. `omk_snapshot` MCP tool — 세션 수집 + sub-task 생성 + 댓글 참조 (§6-U, P0)
29. Sub-task 생성 실패 시 댓글 fallback (§6-U, P0)
30. `/oh-my-kanban:analyze-project-lv1` 스킬 — Quick Overview 인라인 출력 (§6-V, P1)
31. `/oh-my-kanban:analyze-project-lv2` 스킬 — Structural Analysis + `.omk/reports/` 보고서 (§6-V, P1)
32. `/oh-my-kanban:analyze-project-lv3` 스킬 — Deep Analysis + Mermaid 다이어그램 + 리스크 분석 (§6-V, P2)

---

## 10. 아키텍처 결정 기록 (ADR)

| # | 결정 | 근거 | 대안 (기각) |
|---|------|------|-------------|
| 1 | WI에 session_id는 **구조화 댓글**로 기록 | 모든 플랫폼 호환, 추가 API 불필요 | 커스텀 필드 (플랫폼별 차이), 라벨 (동적 session_id에 부적합) |
| 2 | 멀티세션은 **Advisory Warning** | fail-open 일관성, crash 시 데드락 방지 | Hard Lock (crash 시 해제 불가), 세션 큐잉 (과잉 설계) |
| 3 | 전체 대화 로그 **미구현** | 기술적 불가(hooks에 대화 내용 없음), 용도 불명확, 프라이버시 | 전체 로그 업로드 (기술 제약 + "나중에 용도 결정" 패턴) |
| 4 | 추상화는 **얇은 어댑터 + Label** | 플랫폼 격차 크고 완전 추상화는 leaky abstraction | 완전한 WIProvider 인터페이스 (과잉 설계) |
| 5 | SPA 가이드 페이지 **불필요** | 3개 플랫폼 모두 Label API 필터링 지원 | SPA 대시보드 (유지보수 부담) |
| 6 | 솔로/팀 모드 **별도 설정 불필요** | upload_level + Claude scope로 간접 유도 | 명시적 모드 선택 (동작 차이 미미) |
| 7 | 훅 실패 시 **사용자 + Claude 동시 알림** (fail-open with transparency) | 실패를 삼키면 서비스 가치 소멸. systemMessage + additionalContext 동시 활용 | fail-silent (현재, 가치 없음), fail-closed (Claude Code 차단, 불가) |
| 8 | Task Format 템플릿 엔진은 **Mustache 스타일 자체 구현** (~100줄) | 의존성 최소화 원칙. Jinja2는 강력하지만 과잉. chevron도 추가 의존성 | Jinja2 (과잉), chevron (추가 의존성), Python string.Template (`$var`가 Markdown에서 혼동) |
| 9 | 기록 모드는 **3단계** (detailed/normal/eco) | 선택의 단순성. 5단계 이상은 선택 피로 유발. normal(80%)이 대부분 충분 | 연속 슬라이더 (설정 난이도 높음), 4단계 (불필요한 세분화) |
| 10 | Preset은 **파일 복사** 방식 (심볼릭 링크 아님) | 사용자 수정 감지 가능 (hash 비교), 크로스 플랫폼 호환 | 심볼릭 링크 (Windows 미지원, 수정 감지 불가) |
| 11 | 문서 사이트는 **VitePress** (기존 repo `/docs`) | 네이티브 i18n, ~50KB 번들, Node.js 기반 도구 이미 존재. 코드-문서 PR 동기화 | MkDocs (i18n 플러그인 의존), Docusaurus (React 과잉), 별도 repo (v0.x 단계 오버헤드) |
| 12 | Plane CRUD는 **omk CLI 우선**, Plane MCP 비활성화 | 109개 MCP tool이 context window에 ~22K-55K 토큰 고정 소비 (매 턴). omk CLI는 `Bash` tool 1개로 동일 기능 + Linear/세션 관리 통합. 인지 부담 107 tool 감소 (`omk pl <resource> <action>` 단일 패턴). omk 자체 MCP 5개(세션 관리)는 유지 | Plane MCP 유지 (context 소비 과대), MCP+CLI 혼용 (일관성 저해), CLI 완전 제거 (Linear·세션 통합 기능 손실) |

---

## 11. 플랫폼별 구현 격차 및 필요 작업

| 작업 | Plane | Linear | GitHub |
|------|-------|--------|--------|
| WI CRUD | ✅ 완전 | ✅ 완전 | ❌ 미구현 (gh CLI 래핑) |
| Parent-Child | ✅ `--parent` | ❌ 미구현 (`parentId` 추가 필요) | ❌ (task list) |
| Label Create | ✅ 구현됨 | ❌ 미구현 (GraphQL mutation 추가) | ✅ `gh label create` |
| Label Filter | ⚠️ SDK 미지원 (raw HTTP) | ❌ 미구현 (`IssueFilter.labels` 추가) | ✅ `gh issue list --label` |
| Module/Group | ✅ 완전 CRUD | ❌ Project 조회만 | ❌ Milestone 래핑 필요 |
| Archive | ✅ Module/Cycle | ❌ | ✅ `gh issue close` |
