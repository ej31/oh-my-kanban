# omk me — 현재 세션 정보 조회

현재 세션의 상태, 연결된 WI, 진행 상황 등을 보여준다.

## 실행 조건

사용자가 "/oh-my-kanban:me", "/omk:me" 또는
"현재 세션 상태 보여줘", "내 작업 상황 알려줘", "omk 상태 확인해줘" 등을 요청한 경우.

## 절차

### 1. 세션 파일 읽기

현재 세션의 상태를 세션 파일에서 읽는다.

### 2. 세션 정보 표시

```text
[omk] 현재 세션 정보
  세션 ID: <session_id[:8]>...
  시작 시각: <created_at (KST 변환)>
  세션 기간: <duration>

  📋 연결된 Task: <identifier> — <wi_name>
     URL: <plane_url>
     상태: <wi_status>

  📊 진행 통계:
     요청 횟수: <total_prompts>회
     수정 파일: <files_touched_count>개
     범위 이탈 경고: <drift_warnings>회
     범위 자동 확장: <scope_expansions>회

  🎯 세션 목표:
     <scope_summary>

  📁 주요 수정 파일:
     <files_touched[:5]>

  ⏱️ 마지막 댓글 폴링: <last_comment_check or '없음'>
```

연결된 WI가 없으면:

```text
  📋 연결된 Task: 없음
     /oh-my-kanban:focus로 Task를 연결하거나 /oh-my-kanban:create-task로 새로 생성하세요.
```

### 3. 현재 사용자 정보 (선택)

Plane API를 통해 현재 인증된 사용자 정보를 조회한다:

```python
mcp__plane__get_me()
```

## 주의사항

- 세션 파일 읽기 실패 시 "세션 정보를 불러올 수 없습니다"를 출력한다
- 타임스탬프는 가능하면 KST (UTC+9)로 변환하여 표시한다
- WI URL은 config에서 base_url, workspace_slug, project_id로 조합하여 생성한다
