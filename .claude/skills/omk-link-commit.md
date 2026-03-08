# omk link-commit <커밋해시> — 커밋을 현재 WI에 수동 연결

특정 커밋 해시를 현재 Work Item의 댓글로 수동 기록합니다.

## 사용 예시

```bash
omk link-commit a1b2c3d
omk link-commit a1b2c3d7f9e2b4c6d8e0f1a2b3c4d5e6f7a8b9c0
```

## 실행 단계

1. **현재 WI 확인**
   - `focused_work_item_id` 없으면 오류:
     "Work Item이 연결되지 않았습니다.
     /oh-my-kanban:focus 먼저 실행하세요."

2. **커밋 정보 조회 (선택)**
   - `git show --oneline -s <커밋해시>` 로 커밋 메시지 조회 (실패해도 계속)

3. **WI에 댓글 추가**

   ```python
   mcp__plane__create_work_item_comment(
       project_id=<현재 project_id>,
       work_item_id=<focused_work_item_id>,
       comment_html=(
           "<h3>커밋 기록</h3>"
           "<p><strong>커밋</strong>: <code>{hash_short}</code><br>"
           "<strong>메시지</strong>: {sanitize_comment(commit_msg)}<br>"
           "<em>omk에 의해 수동 기록됨</em></p>"
       )
   )
   ```

4. **결과 출력**:

```text
[omk] 커밋 {hash_short}을 {wi_identifier}에 기록했습니다.
```

## 주의사항

- 해시가 7자 미만이면 경고 (단, 처리는 계속)
- git 명령 실패해도 댓글은 계속 추가
- 동일 커밋 중복 기록 방지는 미구현 (Plane 댓글 목록 검색 비용 큼)
