---
layout: home
title: oh-my-kanban
titleTemplate: Plane + Claude Code 자동 WI 연동

hero:
  name: oh-my-kanban
  text: Plane + Claude Code 자동 WI 연동
  tagline: 코딩하는 동안 Work Item이 자동으로 업데이트됩니다.
  actions:
    - theme: brand
      text: 시작하기
      link: /ko/getting-started
    - theme: alt
      text: GitHub
      link: https://github.com/ej31/oh-my-kanban

features:
  - icon: ⚡
    title: 자동 세션 추적
    details: Claude Code 세션이 시작/종료될 때 Plane Work Item에 자동으로 댓글이 기록됩니다.
  - icon: 🔗
    title: WI 연결
    details: /oh-my-kanban:focus 명령으로 현재 작업 중인 Work Item을 세션에 연결합니다.
  - icon: 📊
    title: 진행 상황 가시화
    details: 드리프트 감지, 서브태스크 완료 알림, 팀원 댓글 폴링으로 작업 상황을 한눈에 파악합니다.
  - icon: 🛡️
    title: Fail-Open 설계
    details: 훅이 실패해도 Claude Code가 차단되지 않습니다. 안전한 fail-open 아키텍처.
---

## 빠른 시작

```bash
# Claude Code 마켓플레이스에서 설치
# Claude Code 내에서 실행:
/install-github-app ej31/oh-my-kanban

# 또는 직접 설치
omk hooks install
```

## 핵심 원칙

1. **WI는 기록이다** — 세션이 WI를 "소유"하지 않습니다. 세션은 WI에 "참조/기여"합니다.
2. **쓰레기 WI가 없어야 한다** — 시각적으로 깔끔하고, 장기적으로 가치 있는 데이터.
3. **용도 없는 기능은 만들지 않는다** — "나중에 쓸 수도 있으니까"는 최악의 패턴.
4. **fail-open with transparency** — 모든 훅은 실패해도 Claude Code를 차단하지 않습니다.
