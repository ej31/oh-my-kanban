# omk sprint — 현재 Sprint(Cycle) 상태 조회

현재 프로젝트의 활성 Sprint(Cycle) 정보와 미완료 Task 목록을 조회합니다.

## 실행 단계

1. **활성 Cycle 조회**
   ```python
   mcp__plane__list_cycles(project_id=<현재 project_id>)
   ```
   status가 "current" 또는 end_date가 미래인 Cycle을 찾는다.

2. **Cycle 내 Work Items 조회**
   ```python
   mcp__plane__list_cycle_work_items(project_id=<현재 project_id>, cycle_id=<active_cycle_id>)
   ```

3. **상태별 분류**
   - 미완료 (group: started, unstarted, backlog)
   - 완료 (group: completed, cancelled)

4. **결과 출력** (아래 형식):

```
[omk] Sprint: {cycle_name}
  기간: {start_date} ~ {end_date} (D-{days_left})
  진행률: {done_count}/{total_count} ({percent}%)

  미완료 Task ({incomplete_count}개):
    OMK-XXX: Task 이름 (In Progress)
    OMK-YYY: Task 이름 (Todo)
    ...
```

## 컨텍스트 접근

```python
# 세션 상태에서 project_id 조회
import json, pathlib
session_files = list(pathlib.Path.home().glob(".claude/oh-my-kanban/sessions/*.json"))
# 가장 최근 파일의 plane_context.project_id 사용
```

또는 MCP 설정에서 `OMK_PROJECT_ID` 환경변수를 참조한다.

## 주의사항

- Cycle이 없으면 "현재 활성 Sprint가 없습니다." 안내
- API 실패 시 오류 메시지 출력 후 종료
- 마감 3일 이내이면 경고 강조 표시
