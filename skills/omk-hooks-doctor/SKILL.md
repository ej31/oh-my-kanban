---
name: omk-hooks-doctor
description: oh-my-kanban 훅 설치 상태를 진단하고 문제를 수정합니다. 세션 추적이 작동하지 않거나 훅 관련 오류가 발생할 때 사용합니다.
---

oh-my-kanban 훅 설치 상태를 진단해주세요.

다음 명령을 실행하세요:

```bash
omk hooks status
```

**훅이 설치되지 않은 경우** 다음 명령으로 설치합니다:

```bash
omk hooks install
```

**훅을 재설치해야 하는 경우** (업데이트 후 또는 오류 발생 시):

```bash
omk hooks uninstall
omk hooks install
```

**진단 항목:**
- SessionStart / SessionEnd 훅 등록 여부
- `~/.claude/hooks/` 디렉토리 내 훅 파일 존재 여부
- oh-my-kanban 설정 파일 유효성
- Plane API 연결 상태

**일반적인 문제 해결:**

| 증상 | 해결 방법 |
|------|-----------|
| 세션 시작 시 Work Item이 생성되지 않음 | `omk hooks install` 재실행 |
| `omk` 명령어를 찾을 수 없음 | `pip install oh-my-kanban` 또는 `npx oh-my-kanban` 사용 |
| Plane 연결 오류 | `omk wizard`로 설정 재구성 |
| 훅 실행 권한 오류 | `chmod +x ~/.claude/hooks/*.sh` 실행 |

설정 마법사를 처음부터 다시 실행하려면:

```bash
npx oh-my-kanban wizard
```
