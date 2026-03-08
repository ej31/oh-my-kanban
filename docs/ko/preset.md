# 프리셋 (Preset)

프리셋은 자주 사용하는 설정 조합을 묶어서 한 번에 적용할 수 있는 기능입니다.

## 개요

프로젝트마다 다른 설정이 필요할 때, 매번 개별 설정을 변경하는 대신 프리셋을 적용하면 됩니다. 빌트인 프리셋 3종이 제공되며, 사용자 정의 프리셋도 생성할 수 있습니다.

## 빌트인 프리셋

| 프리셋 | task_mode | upload_level | 설명 |
|--------|-----------|--------------|------|
| `minimal` | flat | none | 최소 설정. 댓글 업로드 없이 로컬 기록만. |
| `standard` | main-sub | metadata | 표준 설정. 메타데이터 댓글 업로드. |
| `verbose` | main-sub | full | 상세 기록. 타임라인 포함 전체 댓글 업로드. |

## CLI 명령

### 프리셋 목록

```bash
omk config preset list
```

### 프리셋 적용

```bash
# 빌트인 프리셋 적용
omk config preset apply minimal

# 특정 프로필에 적용
omk config preset apply verbose --profile work
```

### 사용자 프리셋 생성

```bash
# 현재 설정을 프리셋으로 저장
omk config preset create my-setup

# 설명 추가
omk config preset create my-setup -d "팀 프로젝트용 설정"
```

### 프리셋 내보내기

```bash
# TOML 형식으로 출력
omk config preset export my-setup
```

출력 예시:

```toml
[preset]
name = "my-setup"
description = "팀 프로젝트용 설정"
task_mode = "main-sub"
upload_level = "full"
drift_sensitivity = 0.7
drift_cooldown = 2
```

## 사용자 프리셋 파일

사용자 프리셋은 `~/.config/oh-my-kanban/presets/` 디렉토리에 TOML 파일로 저장됩니다.

## 주의사항

- 빌트인 프리셋은 수정할 수 없습니다.
- 프리셋 이름에는 영문자, 숫자, 하이픈, 밑줄만 사용할 수 있습니다.
- 프리셋 적용 시 기존 설정이 덮어쓰여집니다. 적용 전 현재 설정을 확인하세요.
