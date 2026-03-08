---
name: omk-setup
description: oh-my-kanban의 Plane 연동을 설정한다.
---

# omk setup — Plane 설정 마법사

oh-my-kanban의 Plane 연동을 설정한다.

## 실행 방법

다음 명령을 실행한다:

```bash
omk setup
```

## 설정 마법사 항목

1. **Plane 서버 URL** — 기본값: `https://app.plane.so`
   (self-hosted면 커스텀 URL)
2. **API 키** — Plane 프로필 → API Tokens에서 발급
3. **워크스페이스 슬러그** — Plane URL의 워크스페이스 이름 부분
4. **프로젝트 ID** — 현재 프로젝트의 UUID
   - `PLANE_PROJECT_ID`가 없으면 상위 디렉터리의 `CLAUDE.md`에서
     `<plane_context>` / `project_id`를 자동 감지할 수 있다

## 현재 설정 확인

현재 세션에서 PlaneContext 정보를 확인하려면:

- `state.plane_context.project_id` — 연결된 프로젝트
- `state.plane_context.work_item_ids` — 현재 추적 중인 WI 목록
- `state.plane_context.focused_work_item_id` — 집중 WI

설정 완료 후 세션을 재시작하거나 `omk status`로 연결 상태를 확인한다.
