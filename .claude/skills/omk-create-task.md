# omk create-task — 새 Task 생성 + 세션 연결

새 Plane Work Item을 생성하고 현재 세션에 연결한다.

## 실행 조건

사용자가 "/oh-my-kanban:create-task", "/omk:ct" 또는 "새 태스크 만들어줘", "Task 생성해줘" 등을 요청한 경우.

## 절차

### 1. Task 정보 수집

사용자에게 Task 이름과 설명을 확인한다. 대화 맥락에서 자동 추론 가능하면 추론하고 확인을 요청한다:

```
새로 만들 Task 이름: <사용자 입력 또는 추론>
설명 (선택): <사용자 입력>
```

### 2. config에서 task_mode 확인

`~/.config/oh-my-kanban/config.toml`의 `task_mode` 값을 확인한다:
- `main-sub`: MainTask 구조로 생성 (단독 WI, omk:type:main 라벨)
- `module-task-sub`: Module에 연결된 Task로 생성 (Module 선택 필요)

### 3. WI 생성

task_mode에 따라 적절한 구조로 WI를 생성한다:

**Mode A (main-sub):**
```
mcp__plane__create_work_item(
  project_id="<project_id>",
  name="<task_name>",
  description="<description>",
  state_id="<in_progress_state_id>",
  label_ids=["<omk:session 라벨 ID>", "<omk:type:main 라벨 ID>"]
)
```

**Mode B (module-task-sub):**
먼저 Module 목록 조회:
```
mcp__plane__list_modules(project_id="<project_id>")
```
Module 선택 후 WI 생성:
```
mcp__plane__create_work_item(
  project_id="<project_id>",
  name="<task_name>",
  description="<description>",
  state_id="<in_progress_state_id>",
  label_ids=["<omk:session 라벨 ID>"]
)
mcp__plane__add_work_items_to_module(module_id="<module_id>", work_item_ids=["<new_wi_id>"])
```

### 4. 세션 시작 댓글 추가

생성된 WI에 세션 시작 댓글을 추가한다:
```
mcp__plane__create_work_item_comment(
  work_item_id="<new_wi_id>",
  comment_html="## omk 세션 시작\n\n**세션 ID**: `<session_id[:8]>...`\n**시작 시각**: <timestamp>\n**목표**: <task_name>"
)
```

### 5. PlaneContext 업데이트

생성된 WI UUID를 세션의 plane_context에 반영한다:
- `work_item_ids` 에 새 WI UUID 추가
- `focused_work_item_id` 를 새 WI UUID로 설정
- `main_task_id` 를 새 WI UUID로 설정

### 6. 사용자에게 확인 알림

```
[omk] Task가 등록되었습니다.
  WI: <identifier> — <task_name>
  URL: <plane_url>
  중요한 메모나 맥락이 있으시면 위 링크에서 댓글로 남겨주세요.
  이 세션에서 자동으로 참고합니다.
```

## 현재 PlaneContext 읽기

- `state.plane_context.project_id` — 생성할 프로젝트 ID
- `state.plane_context.work_item_ids` — 기존 연결 WI 목록
- project_id가 없으면 사용자에게 먼저 `omk setup`을 실행하도록 안내한다

## 주의사항

- WI 생성 전 항상 이름을 사용자에게 확인받는다
- 상태(State) ID는 하드코딩하지 않고 `mcp__plane__list_states`로 동적 조회한다
- 라벨 ID는 하드코딩하지 않고 `mcp__plane__list_labels`로 동적 조회한다
- 생성 실패 시 명확한 에러 메시지를 출력한다
