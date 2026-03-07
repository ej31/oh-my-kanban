# omk link-branch — 현재 브랜치를 WI에 연결 기록

현재 git 브랜치 정보를 Work Item 댓글에 기록하고 WI 링크를 설정합니다.

## 실행 단계

1. **현재 브랜치 조회**
   ```bash
   git branch --show-current
   ```
   브랜치가 없으면 (detached HEAD): "브랜치가 없는 상태입니다 (detached HEAD)."

2. **원격 저장소 URL 조회 (선택)**
   ```bash
   git remote get-url origin
   ```
   실패해도 계속 진행.

3. **현재 WI 확인**
   - `focused_work_item_id` 없으면: "Work Item이 연결되지 않았습니다. /oh-my-kanban:focus 먼저 실행하세요."

4. **WI에 브랜치 링크 댓글 추가**
   ```python
   mcp__plane__create_work_item_comment(
       project_id=<현재 project_id>,
       work_item_id=<focused_work_item_id>,
       comment_html="<h3>브랜치 연결</h3><p><strong>브랜치</strong>: <code>{branch_name}</code><br><strong>저장소</strong>: {repo_url}<br><em>omk에 의해 자동 기록됨</em></p>"
   )
   ```

5. **WI 링크 추가 (선택, 저장소 URL이 있을 때)**
   ```python
   # 브랜치 URL 구성 (GitHub/GitLab 형식)
   branch_url = f"{repo_url}/tree/{branch_name}"
   mcp__plane__create_work_item_link(
       project_id=<현재 project_id>,
       work_item_id=<focused_work_item_id>,
       url=branch_url,
       title=f"브랜치: {branch_name}"
   )
   ```

6. **결과 출력**:
```
[omk] 브랜치 {branch_name}을 {wi_identifier}에 연결했습니다.
  링크: {branch_url}
```

## 주의사항

- git 명령 실패 시 오류 안내 후 중단
- 원격 저장소 URL이 없으면 WI 링크 추가 건너뜀
- 동일 브랜치 중복 기록 방지는 미구현
