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
   # branch_name, repo_url은 HTML-safe 값으로 이스케이프한 뒤 사용
   mcp__plane__create_work_item_comment(
       project_id=<현재 project_id>,
       work_item_id=<focused_work_item_id>,
       comment_html="<h3>브랜치 연결</h3><p><strong>브랜치</strong>: <code>{escaped_branch_name}</code><br><strong>저장소</strong>: {escaped_repo_url}<br><em>omk에 의해 자동 기록됨</em></p>"
   )
   ```

5. **WI 링크 추가 (선택, 저장소 URL이 있을 때)**

   ```python
   # SSH/scp remote는 HTTPS browser URL로 정규화하고 trailing .git 제거
   normalized_repo_url = normalize_git_remote_to_https(repo_url)
   encoded_branch_name = quote(branch_name, safe="")
   branch_url = f"{normalized_repo_url}/tree/{encoded_branch_name}"
   mcp__plane__create_work_item_link(
       project_id=<현재 project_id>,
       work_item_id=<focused_work_item_id>,
       url=branch_url,
       title=f"브랜치: {branch_name}"
   )
   ```

6. **결과 출력**:

```text
[omk] 브랜치 {branch_name}을 {wi_identifier}에 연결했습니다.
  링크가 생성된 경우에만 아래를 함께 표시합니다.
  링크: {branch_url}
```

## 주의사항

- git 명령 실패 시 오류 안내 후 중단
- 원격 저장소 URL이 없으면 WI 링크 추가를 건너뛰고 결과 메시지에서도 링크 줄을 생략한다
- SSH/scp 형식 remote(`git@...`, `ssh://...`)는 브라우저용 HTTPS URL로 정규화한다
- 브랜치명은 URL-encode 후 링크에 사용한다
- 동일 브랜치 중복 기록 방지는 미구현
