---
name: omk-stats
description: 현재 프로젝트의 세션 통계와 Work Item 현황을 분석해 요약합니다.
---

# omk stats — 세션/WI 통계 대시보드

현재 프로젝트의 세션 통계와 Work Item 현황을 분석해 요약합니다.

## 실행 단계

1. **세션 파일 집계**

   - `~/.claude/oh-my-kanban/sessions/*.json` 읽기
   - 집계 항목:
     - 총 세션 수
     - 총 프롬프트 수 (`stats.total_prompts` 합계)
     - 총 수정 파일 수 (중복 제거한 `stats.files_touched`)
     - 드리프트 경고 총합 (`stats.drift_warnings`)
     - 평균 세션당 프롬프트 수
   - 핫스팟 파일 (5개 이상 세션에서 수정된 파일):

     ```text
     [hotspot] src/auth.py — 7개 세션에서 수정됨 (리팩토링 검토 권장)
     ```

1. **WI 현황 조회 (Plane API 있을 때)**

   - `mcp__plane__list_work_items`로 전체 WI 목록 조회
   - 상태별 분포 계산 (In Progress / Backlog / Done 등)
   - 완료율 계산: `완료된 WI / 전체 WI * 100`
   - 최근 10개 WI 목록 (업데이트 시각 기준)

1. **출력 형식**

```text
[omk stats] 세션 통계
  총 세션: 24개
  총 프롬프트: 1,247회
  수정된 파일 (unique): 89개
  드리프트 경고: 12회
  세션당 평균 프롬프트: 51.9회

[omk stats] 핫스팟 파일 (5개 이상 세션)
  src/oh_my_kanban/hooks/session_start.py — 12세션
  src/oh_my_kanban/session/state.py — 9세션
  src/oh_my_kanban/hooks/common.py — 7세션

[omk stats] WI 현황
  전체: 35개 | 완료: 32개 | 진행 중: 2개 | 백로그: 1개
  완료율: 91.4%
```

## API 키 없을 때

세션 통계만 출력하고 WI 현황은 건너뜀:

```text
[omk stats] Plane API 키가 설정되지 않아 WI 현황을 조회할 수 없습니다.
  /oh-my-kanban:setup 으로 설정하세요.
```

## 주의사항

- 세션 파일이 없으면 "아직 세션 데이터가 없습니다" 출력
- 파일 읽기 실패는 건너뜀 (fail-open)
- 통계는 로컬 세션 파일 기반이므로 실제 Plane 상태와 다를 수 있음
