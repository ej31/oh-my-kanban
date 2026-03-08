---
name: omk-help
description: oh-my-kanban 사용법을 안내합니다. 질문을 입력하면 FAQ로 답변합니다.
---

# omk-help 스킬 실행 지침

사용자가 `/omk-help` 또는 `/omk-help [질문]`을 실행하면 아래를 수행하세요.

---

## 인수 없음: 스킬 목록 표시

인수 없이 실행하면 아래 스킬 목록을 카테고리별로 표시합니다.

### 설정 및 진단

| 스킬 | 설명 |
| --- | --- |
| `/omk-setup` | Plane/Linear API 설정 마법사 |
| `/omk-status` | 훅 설치 상태와 활성 세션 확인 |
| `/omk-doctor` | 설정·API·훅 통합 진단 |
| `/omk-help` | 이 도움말 표시 |

### WI 연결 및 생성

| 스킬 | 설명 |
| --- | --- |
| `/omk-focus <WI-ID>` | 특정 WI를 현재 세션에 연결 |
| `/omk-create-task "<제목>"` | 새 WI 생성 후 세션 연결 |
| `/omk-subtask "<제목>"` | 현재 WI에 서브태스크 생성 |
| `/omk-done` | 현재 WI 완료 처리 |
| `/omk-switch-task <WI-ID>` | 다른 WI로 전환 |
| `/omk:gh` | GitHub Projects WI를 `gh` CLI로 관리하는 절차 안내 |

### 기록 및 메모

| 스킬 | 설명 |
| --- | --- |
| `/omk-note "<메모>"` | 현재 WI에 즉시 댓글 추가 |
| `/omk-decision "<결정>"` | 결정 사항 댓글 기록 |
| `/omk-handoff` | 핸드오프 메모 작성 |
| `/omk-snapshot` | 현재 세션 상태 스냅샷 저장 |

### 조회

| 스킬 | 설명 |
| --- | --- |
| `/omk-comments` | 현재 WI 최근 댓글 조회 |
| `/omk-history [WI-ID]` | WI 활동 이력 조회 |
| `/omk-me` | 내 세션 요약 |
| `/omk-sprint` | 현재 스프린트 진행 상황 |

### 고급

| 스킬 | 설명 |
| --- | --- |
| `/omk-open` | 현재 WI를 브라우저에서 열기 |
| `/omk-context-sync` | WI 컨텍스트 강제 동기화 |
| `/omk-disable-this-session` | 현재 세션 추적 비활성화 |

질문이 있으면 `/omk-help [질문]` 형식으로 입력하세요.

---

## 인수 있음: FAQ 답변

사용자가 질문을 입력하면 아래 FAQ에서 관련 항목을 찾아 답변합니다.
관련 항목이 없으면 `/omk-doctor` 실행 또는 GitHub Issues를 안내합니다.

### 설치 및 설정

**Q: 처음에 무엇을 해야 하나요?**
A: 설치 후 `/omk-setup` 스킬로 Plane 또는 Linear API 키를 설정하세요. 이후 `/omk-status`로 상태를 확인하세요.

**Q: API 키는 어디서 얻나요?**
A: Plane → 프로필 > API 토큰. Linear → Settings > API > Personal API keys.

**Q: 설정 파일은 어디 있나요?**
A: `~/.config/oh-my-kanban/config.toml`에 저장됩니다. `/omk-doctor`로 파일 상태를 진단할 수 있습니다.

**Q: workspace_slug란 무엇인가요?**
A: Plane URL에서 `https://<host>/<workspace_slug>/projects/...` 형태로 확인할 수 있습니다.

**Q: 여러 프로젝트에서 다른 설정을 쓰고 싶어요.**
A: `omk hooks install --local`로 프로젝트별 `.claude/settings.json`에 설치하고, `.omk/project.toml`에 `project_id`를 지정하세요.

### 훅 문제

**Q: 훅이 활성화되어 있는지 어떻게 확인하나요?**
A: `/omk-status` 스킬을 실행하거나 `omk hooks status` 명령을 실행하세요.

**Q: 훅이 작동하지 않아요. 세션 컨텍스트가 로드되지 않습니다.**
A: 아래 순서로 확인하세요:
1. `/omk-status`로 훅 설치 상태 확인
2. 훅이 없으면 `omk hooks install`로 재설치
3. Claude Code를 완전히 재시작
4. 여전히 안 되면 `/omk-doctor`로 전체 진단

**Q: 훅 설치는 어떻게 하나요?**
A: `/omk-setup` 스킬로 대화형 설치하거나 `omk hooks install` 명령을 직접 실행하세요.

### WI 연결 문제

**Q: WI ID는 어떤 형식인가요?**
A: Plane은 `<PROJECT>-<번호>` (예: `DEV-42`), Linear는 `<TEAM>-<번호>` 형식입니다.

**Q: GitHub Projects는 `omk gh` 명령이 있나요?**
A: 없습니다. GitHub 기반 WI는 `/oh-my-kanban:github-projects` 또는 `/omk:gh` 스킬을 통해 `gh issue`, `gh project` 조합으로 관리합니다.

**Q: omk focus가 안 됩니다. WI를 찾을 수 없다고 해요.**
A: 아래를 확인하세요:
1. `/omk-doctor`로 API 연결 상태 확인
2. WI ID 형식이 올바른지 확인 (`DEV-42` 형식)
3. `project_id`가 설정되어 있는지 확인 (`.omk/project.toml`)

**Q: stale WI란 무엇인가요?**
A: 이전에 연결했던 WI가 삭제되거나 접근 불가 상태가 된 것입니다. `/omk-focus <새_WI_ID>`로 새 WI를 연결하거나 `/omk-disable-this-session`으로 추적을 비활성화하세요.

**Q: 현재 어떤 WI가 연결되어 있나요?**
A: `/omk-status` 스킬로 현재 세션의 연결된 WI 목록을 확인하세요.

### 주요 스킬 사용법

**Q: omk-note와 omk-decision의 차이는 무엇인가요?**
A: `/omk-note`는 자유형식 메모, `/omk-decision`은 의사결정 기록에 특화된 포맷으로 댓글을 남깁니다.

**Q: omk-done 실행 후 WI 상태가 자동으로 바뀌나요?**
A: 네, 연결된 WI를 완료 상태(Done)로 변경합니다. Plane에 Done 상태가 설정되어 있어야 합니다.

**Q: 세션 중 WI를 전환하려면 어떻게 하나요?**
A: `/omk-switch-task <WI-ID>` 스킬로 새 WI를 현재 세션에 연결합니다.

**Q: 답변을 찾지 못했다면?**
A: `/omk-doctor`로 전체 진단을 실행하거나 GitHub Issues에 문의하세요.
GitHub Issues: https://github.com/ej31/oh-my-kanban/issues
