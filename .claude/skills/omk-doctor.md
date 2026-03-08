# omk doctor — 설정/인증/네트워크 진단

oh-my-kanban의 설정, Plane API 인증, 네트워크 연결을 진단한다.

## 진단 절차

### 1. API 키 진단

```bash
# 설정 파일 존재/권한 확인
ls -l ~/.config/oh-my-kanban/config.toml

# 민감정보를 제외하고 주요 설정만 확인
grep -E '^(workspace_slug|project_id)\s*=' ~/.config/oh-my-kanban/config.toml

# API 키 존재 여부만 확인
grep -q '^\s*api_key\s*=' ~/.config/oh-my-kanban/config.toml && echo "api_key configured"
```

- `api_key`가 비어있으면 → `omk setup`으로 재설정
- 키가 있지만 인증 실패(401) → Plane에서 새 토큰 발급

### 2. 워크스페이스 슬러그 진단

```bash
# 워크스페이스 슬러그 확인
grep workspace_slug ~/.config/oh-my-kanban/config.toml
```

- 비어있으면 → `omk setup`으로 재설정
- Plane URL에서 슬러그 확인: `<your_plane_url>/<workspace_slug>/`

### 3. API 응답 진단

```bash
# Plane API 연결 테스트
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-API-Key: <your_api_key>" \
  "https://<your_plane_url>/api/v1/workspaces/<workspace_slug>/projects/"
```

응답 코드별 진단:
- `200` — 정상
- `401` — API 키 오류 → Plane에서 새 토큰 발급
- `403` — 권한 없음 → 워크스페이스 접근 권한 확인
- `404` — 슬러그 오류 → workspace_slug 재확인
- `000` — 네트워크 오류 → 인터넷 연결 확인

### 4. PlaneContext 상태 진단

현재 세션의 PlaneContext를 확인한다:
- `plane_context.project_id` — 비어있으면 CLAUDE.md에 project_id 추가
- `plane_context.work_item_ids` — 비어있으면 `omk focus <WI-ID>`로 연결
- `plane_context.stale_work_item_ids` — 여기 있는 WI는 삭제된 것

### 5. 세션 파일 진단

```bash
# 최근 세션 파일 확인
ls -lt ~/.local/share/oh-my-kanban/sessions/ | head -5
```

## PlaneContext에서 정보 읽기

진단 스킬도 `state.plane_context`에서 현재 WI 정보를 읽어 표시한다:
- `focused_work_item_id` — 집중 WI
- `work_item_ids` — 전체 추적 WI 목록
- `stale_work_item_ids` — 삭제 감지된 WI 목록

## 자가 복구 시도

진단 후 자동 복구 가능한 항목:
1. config.toml 권한 오류 → `chmod 600 ~/.config/oh-my-kanban/config.toml`
2. stale WI 정리 → `omk focus <새_WI_ID>`로 새 WI 연결
3. 세션 충돌 → `omk disable-this-session`으로 현재 세션 비활성화 후 재시작
