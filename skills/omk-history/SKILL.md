---
name: omk-history
description: 현재 Work Item에 달린 omk 세션 댓글 이력을 시간순으로 조회합니다.
---

# omk history — 현재 WI의 세션 기여 이력 조회

현재 Work Item에 달린 omk 세션 댓글 이력을 시간순으로 조회합니다.

## 실행 단계

1. **세션 상태에서 현재 WI 확인**
   - `focused_work_item_id` 또는 `work_item_ids[0]` 사용

2. **WI 댓글 조회**

   ```python
   mcp__plane__list_work_item_comments(
       project_id=<현재 project_id>,
       work_item_id=<focused_work_item_id>
   )
   ```

3. **omk 세션 관련 댓글 필터링**
   - `## omk 세션 시작` 또는 `## omk 세션 종료` 또는 `## 커밋 기록` 또는 `## 핸드오프` 패턴

4. **결과 출력** (아래 형식):

```text
[omk] Work Item 기여 이력: {wi_identifier} — {wi_name}

  [2026-03-07 09:15 UTC] 세션 시작 (sess-abc123...)
    목표: OAuth2 Provider 구현

  [2026-03-07 09:42 UTC] 커밋: a1b2c3d

  [2026-03-07 10:30 UTC] 세션 종료 (sess-abc123...)
    요청 23회, 수정 4파일, 기간 1시간 15분

  [2026-03-08 14:00 UTC] 핸드오프 메모
    "refresh_token 미완성, token_store.py 36번줄부터"

총 세션: N개 | 총 요청: N회 | 총 커밋: N개
```

## 주의사항

- WI가 연결되지 않은 경우 "현재 세션에 연결된 Work Item이 없습니다." 안내
- 댓글이 많으면 최근 20개만 표시
- omk 댓글이 없으면 "기록된 세션 이력이 없습니다." 안내
