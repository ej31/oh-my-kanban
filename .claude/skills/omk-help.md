# omk help — omk 스킬 목록

oh-my-kanban에서 사용 가능한 모든 스킬 목록을 카테고리별로 표시한다.

## 설정 및 진단

| 스킬 | 설명 |
| --- | --- |
| `omk setup` | Plane API 설정 마법사 |
| `omk status` | 현재 세션 WI 연결 상태 |
| `omk doctor` | 설정/인증/네트워크 진단 |
| `omk help` | 이 도움말 표시 |

## WI 연결 및 생성

| 스킬 | 설명 |
| --- | --- |
| `omk focus <WI-ID>` | 특정 WI를 현재 세션에 연결 |
| `omk create-task "<제목>"` | 새 WI 생성 후 세션 연결 |
| `omk subtask "<제목>"` | 현재 WI에 서브태스크 생성 |
| `omk done` | 현재 WI 완료 처리 |
| `omk switch-task <WI-ID>` | 다른 WI로 전환 |

## 기록 및 메모

| 스킬 | 설명 |
| --- | --- |
| `omk note "<메모>"` | 현재 WI에 즉시 댓글 추가 |
| `omk decision "<결정>"` | 결정 사항 댓글 기록 |
| `omk handoff` | 핸드오프 메모 작성 |
| `omk snapshot` | 현재 세션 상태 스냅샷 저장 |

## 조회

| 스킬 | 설명 |
| --- | --- |
| `omk comments` | 현재 WI 최근 댓글 조회 |
| `omk history [WI-ID]` | WI 활동 이력 조회 |
| `omk me` | 내 세션 요약 |
| `omk sprint` | 현재 스프린트 진행 상황 |

## 고급

| 스킬 | 설명 |
| --- | --- |
| `omk open` | 현재 WI를 브라우저에서 열기 |
| `omk context-sync` | WI 컨텍스트 강제 동기화 |
| `omk disable-this-session` | 현재 세션 추적 비활성화 |

## PlaneContext에서 현재 WI 정보 읽기

WI 범위가 필요한 스킬만
`state.plane_context.focused_work_item_id`
(또는 `work_item_ids[0]`)를 기준으로 동작한다.
예: `omk focus`, `omk subtask`, `omk done`, `omk switch-task`,
`omk note`, `omk decision`, `omk handoff`, `omk comments`,
`omk history`, `omk sprint`, `omk open`.

반대로 아래 스킬은 focused WI가 없어도 동작한다:

- `omk setup`
- `omk doctor`
- `omk help`
- `omk status`
- `omk create-task`
- `omk disable-this-session`
