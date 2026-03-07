# Incident Report: Hook Bootstrap Lock

- **날짜**: 2026-03-07
- **심각도**: Medium (로컬 개발 환경 작업 불가)
- **영향 범위**: oh-my-kanban 프로젝트 디렉토리에서 Claude Code 세션 전체 차단
- **세션 ID**: `814647f6-2295-4da4-a2c1-5715b926a849`

---

## 발생 경위

1. Phase 2 개발 중 `UserPromptSubmit` hook을 `.claude/settings.json`에 등록
2. hook 스크립트(`user_prompt.py`)를 완성하기 전에 세션 종료
3. 이후 `main` 브랜치 직접 커밋 문제를 해결하는 과정에서 `git reset --hard 342ab33` 실행
4. reset으로 인해 `user_prompt.py`, `post_tool.py` 파일이 working tree에서 삭제됨
5. `.claude/settings.json`의 hook 등록은 그대로 유지
6. 이후 해당 디렉토리에서 Claude Code 세션을 시작할 때마다 `UserPromptSubmit` hook이 실행 시도 → 파일 없음 → 세션 전체 차단

---

## 에러 메시지

```
UserPromptSubmit operation blocked by hook:
["/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"
"/Users/yimtaejong/IdeaProjects/oh-my-kanban/src/oh_my_kanban/hooks/user_prompt.py"]:
/Library/Frameworks/Python.framework/Versions/3.10/bin/python3: can't open file
'/Users/yimtaejong/IdeaProjects/oh-my-kanban/src/oh_my_kanban/hooks/user_prompt.py':
[Errno 2] No such file or directory
```

---

## 근본 원인

**Hook Bootstrap 문제** — hook 스크립트 파일이 존재하지 않는 상태에서 hook이 먼저 등록됨.

`UserPromptSubmit` hook은 blocking 방식으로 실행되며, 실행 실패 시 해당 이벤트를 차단한다. 이로 인해 모든 사용자 입력이 막혀 Claude Code와의 대화 자체가 불가능해진다.

추가로, `.claude/settings.json`이 `.gitignore`에 등록되지 않아 git reset 이후에도 hook 설정이 남아있었다.

---

## 해결 방법

다른 프로젝트 디렉토리(`~/setting-up-pve`)에서 Claude Code 세션을 열어 작업 진행:

1. `.claude/settings.json` 확인 → `UserPromptSubmit` hook이 `user_prompt.py` 참조 중
2. `hooks/` 디렉토리 확인 → `user_prompt.py`, `post_tool.py` 없음
3. `feat/phase2-plugin-marketplace` 브랜치에 해당 파일들이 완성된 상태로 존재함을 확인
4. 브랜치 push 및 PR #16 생성
5. `.gitignore`에 누락 항목 추가 후 커밋

---

## 재발 방지

### 개발 원칙

**Code → Test → Register** 순서를 반드시 지킨다. 절대 Register → Code 순서로 진행하지 않는다.

### Stub-First 패턴

`.claude/settings.json`에 hook을 등록하기 전, 반드시 최소 stub 파일을 먼저 생성한다.

```python
# 최소 stub — 아무것도 안 하고 성공 종료
import sys
sys.exit(0)
```

### 격리된 환경에서 개발

hook 스크립트 개발 중에는 해당 프로젝트 디렉토리가 아닌 다른 디렉토리에서 Claude Code를 열어 작업한다. `.claude/settings.json`은 프로젝트 로컬 설정이므로 디렉토리가 다르면 적용되지 않는다.

### Hook에 방어 코드 적용

```python
import sys
import traceback

try:
    # 실제 로직
    pass
except Exception:
    traceback.print_exc(file=sys.stderr)
    sys.exit(0)  # 예외 발생 시에도 blocking 방지
```

### .gitignore 관리

`omk hooks install`이 자동 관리하는 `.claude/settings.json`은 `.gitignore`에 포함한다. `git reset` 등 destructive 작업 시 hook 설정이 남아 lock이 발생하는 것을 방지한다.

---

## 타임라인

| 시각 | 이벤트 |
|---|---|
| ~14:40 | Phase 2 개발 중 `.claude/settings.json`에 hook 등록 |
| ~14:55 | `6eb1554`, `5b64978` 두 커밋 완성 (main에 직접 커밋) |
| ~14:55 | feat 브랜치 규칙 위반 발견, `git reset --hard 342ab33` 실행 |
| ~14:55 | `feat/phase2-plugin-marketplace` 브랜치로 커밋 이동 |
| ~15:00 | push 여부 확인 중 세션 종료 (lock 상태 진입) |
| ~16:06 | 다른 디렉토리에서 세션 시작, 원인 파악 |
| ~16:15 | PR #16 생성 및 `.gitignore` 정리 완료 |
