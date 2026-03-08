"""설정 관리: TOML 프로필 + 환경변수 + CLAUDE.md 자동 감지."""

from __future__ import annotations

import os
import re
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path

# 프로필 이름 허용 문자: 영문자, 숫자, 하이픈, 밑줄만 허용 (TOML 섹션 헤더 인젝션 방지)
_PROFILE_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')

# UUID 형식 검증 패턴 (project_id 등) — 외부 모듈에서도 import하여 사용
UUID_RE = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')

# .omk 디렉토리 이름 상수 — 외부 모듈에서도 import하여 사용
OMK_DIR_NAME = ".omk"

# project_id 소스 레이블 (사람이 읽기 좋은 형식) — 외부 모듈에서도 import하여 사용
SOURCE_LABELS: dict[str, str] = {
    "env": "환경변수 (PLANE_PROJECT_ID)",
    "omk_project_toml": ".omk/project.toml",
    "claude_md": "CLAUDE.md",
    "config_toml": "~/.config/oh-my-kanban/config.toml",
    "": "(소스 불명)",
}

# 저장 허용 설정 키 화이트리스트 (임의 키 TOML 인젝션 방지)
ALLOWED_CONFIG_KEYS = frozenset({
    "base_url", "api_key", "workspace_slug", "project_id",
    "output", "linear_api_key", "linear_team_id",
    "drift_sensitivity", "drift_cooldown", "task_mode",
    "upload_level", "auto_archive_days", "auto_complete_subtasks",
    "session_retention_days",
    "active_profile",  # _meta 프로필에서 활성 프로필 이름 저장 용도
})

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

# 설정 파일 기본 위치
CONFIG_DIR = Path.home() / ".config" / "oh-my-kanban"
CONFIG_FILE = CONFIG_DIR / "config.toml"

# 기본 Plane API URL (plane.so 클라우드)
DEFAULT_BASE_URL = "https://api.plane.so"


@dataclass
class Config:
    """CLI 설정 값."""

    base_url: str = DEFAULT_BASE_URL
    api_key: str = ""
    workspace_slug: str = ""
    project_id: str = ""
    output: str = "table"
    profile: str = "default"
    linear_api_key: str = ""
    linear_team_id: str = ""
    drift_sensitivity: float = 0.5
    drift_cooldown: int = 3
    task_mode: str = "main-sub"
    upload_level: str = "metadata"
    auto_archive_days: int = 7
    auto_complete_subtasks: bool = True
    session_retention_days: int = 30
    project_id_source: str = ""  # 활성 project_id의 출처: "env", "omk_project_toml", "claude_md", "config_toml", ""


def detect_project_id() -> str:
    """현재 디렉토리에서 상위로 올라가며 CLAUDE.md의 project_id를 찾는다."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        claude_md = parent / "CLAUDE.md"
        if claude_md.exists():
            try:
                content = claude_md.read_text(encoding="utf-8")
                match = re.search(r"project_id:\s*([a-f0-9-]{36})", content)
                if match:
                    return match.group(1)
            except OSError:
                continue
    return ""


def detect_project_toml() -> tuple[str, str]:
    """cwd에서 상위로 올라가며 .omk/project.toml의 project_id를 찾는다.

    Returns:
        (project_id, provider) 튜플. 찾지 못하면 ("", "").
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        project_toml = parent / ".omk" / "project.toml"
        if project_toml.exists():
            try:
                with open(project_toml, "rb") as f:
                    data = tomllib.load(f)
                section = data.get("project", {})
                if not isinstance(section, dict):
                    continue
                pid = section.get("project_id", "")
                provider = section.get("provider", "plane")
                if pid and UUID_RE.match(pid.lower()):
                    return pid, provider
            except (OSError, tomllib.TOMLDecodeError):
                continue
    return "", ""


def load_config(profile: str = "default") -> Config:
    """설정을 로드한다. 우선순위: env vars > TOML 파일."""
    cfg = Config(profile=profile)

    # 1. TOML 파일에서 기본값 로드 (project_id는 별도 변수에 보관)
    _toml_project_id: str = ""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as f:
                data = tomllib.load(f)
            section = data.get(profile, data.get("default", {}))
            cfg.base_url = section.get("base_url", cfg.base_url)
            cfg.api_key = section.get("api_key", cfg.api_key)
            cfg.workspace_slug = section.get("workspace_slug", cfg.workspace_slug)
            # project_id는 최종 결정 로직에서 처리하므로 별도 변수에 저장
            _toml_project_id = section.get("project_id", "")
            cfg.output = section.get("output", cfg.output)
            cfg.linear_api_key = section.get("linear_api_key", cfg.linear_api_key)
            cfg.linear_team_id = section.get("linear_team_id", cfg.linear_team_id)
            if "drift_sensitivity" in section:
                cfg.drift_sensitivity = max(0.0, min(1.0, float(section["drift_sensitivity"])))
            if "drift_cooldown" in section:
                cfg.drift_cooldown = max(0, int(section["drift_cooldown"]))
            if "task_mode" in section:
                cfg.task_mode = str(section["task_mode"])
            if "upload_level" in section:
                cfg.upload_level = str(section["upload_level"])
            if "auto_archive_days" in section:
                cfg.auto_archive_days = max(0, int(section["auto_archive_days"]))
            if "auto_complete_subtasks" in section:
                cfg.auto_complete_subtasks = bool(section["auto_complete_subtasks"])
            if "session_retention_days" in section:
                cfg.session_retention_days = max(1, int(section["session_retention_days"]))
        except (OSError, tomllib.TOMLDecodeError) as e:
            print(f"경고: 설정 파일 파싱 오류 ({CONFIG_FILE}): {e}", file=sys.stderr)

    # 2. 환경변수 오버라이드 (빈 문자열은 무시하여 config 값 보호, project_id 제외)
    if env_val := os.environ.get("PLANE_BASE_URL"):
        cfg.base_url = env_val
    if env_val := os.environ.get("PLANE_API_KEY"):
        cfg.api_key = env_val
    if env_val := os.environ.get("PLANE_WORKSPACE_SLUG"):
        cfg.workspace_slug = env_val
    if env_val := os.environ.get("LINEAR_API_KEY"):
        cfg.linear_api_key = env_val
    if env_val := os.environ.get("LINEAR_TEAM_ID"):
        cfg.linear_team_id = env_val
    if env_val := os.environ.get("OMK_DRIFT_SENSITIVITY"):
        try:
            # 유효 범위 0.0 ~ 1.0으로 제한 (경계값 방어)
            cfg.drift_sensitivity = max(0.0, min(1.0, float(env_val)))
        except ValueError:
            print(
                f"경고: OMK_DRIFT_SENSITIVITY='{env_val}' 은 유효한 float 값이 아닙니다. "
                f"기본값 {cfg.drift_sensitivity} 사용.",
                file=sys.stderr,
            )
    if env_val := os.environ.get("OMK_TASK_MODE"):
        cfg.task_mode = env_val
    if env_val := os.environ.get("OMK_UPLOAD_LEVEL"):
        cfg.upload_level = env_val
    if env_val := os.environ.get("OMK_DRIFT_COOLDOWN"):
        try:
            # 음수 방지 (0 이상 정수)
            cfg.drift_cooldown = max(0, int(env_val))
        except ValueError:
            print(
                f"경고: OMK_DRIFT_COOLDOWN='{env_val}' 은 유효한 정수 값이 아닙니다. "
                f"기본값 {cfg.drift_cooldown} 사용.",
                file=sys.stderr,
            )

    # base_url 스키마 검증 (SSRF 방지): http(s)://만 허용
    if cfg.base_url and not (
        cfg.base_url.startswith("http://") or cfg.base_url.startswith("https://")
    ):
        print(
            f"[omk] 경고: base_url '{cfg.base_url}'은 http:// 또는 https://로 시작해야 합니다. "
            f"기본값 '{DEFAULT_BASE_URL}'으로 대체합니다.",
            file=sys.stderr,
        )
        cfg.base_url = DEFAULT_BASE_URL

    # 3. project_id 최종 결정: env > .omk/project.toml > CLAUDE.md > config.toml
    if env_project_id := os.environ.get("PLANE_PROJECT_ID"):
        cfg.project_id = env_project_id
        cfg.project_id_source = "env"
    else:
        omk_pid, _omk_provider = detect_project_toml()
        if omk_pid:
            cfg.project_id = omk_pid
            cfg.project_id_source = "omk_project_toml"
        else:
            claude_pid = detect_project_id()
            if claude_pid:
                cfg.project_id = claude_pid
                cfg.project_id_source = "claude_md"
            elif _toml_project_id:
                cfg.project_id = _toml_project_id
                cfg.project_id_source = "config_toml"
                print(
                    "경고: config.toml의 project_id는 향후 제거 예정입니다. "
                    "'omk project bind'로 프로젝트별 설정을 권장합니다.",
                    file=sys.stderr,
                )

    return cfg


def escape_toml_string(v: str) -> str:
    """TOML 기본 문자열에 포함될 값의 특수문자를 이스케이프한다 (TOML v1.0 사양 준수)."""
    result = v.replace("\\", "\\\\").replace('"', '\\"')
    result = result.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    # U+0000-U+0008, U+000B-U+000C, U+000E-U+001F, U+007F 제어 문자 이스케이프
    # 참고: \t/\n/\r은 위에서 이미 \\t/\\n/\\r로 치환되어 여기선 나타나지 않음
    return "".join(
        c if (ord(c) >= 0x20 and ord(c) != 0x7F) else f"\\u{ord(c):04X}"
        for c in result
    )


def save_config(data: dict, profile: str = "default") -> None:
    """설정을 TOML 파일에 저장한다."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # 기존 설정 로드
    existing: dict = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as f:
                existing = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as e:
            raise OSError(
                f"Cannot read config file ({CONFIG_FILE}): {e}. "
                "Refusing to overwrite to prevent data loss."
            ) from e

    # 허용 키만 필터링 (임의 키 인젝션 방지), 불변 방식으로 병합
    filtered = {k: v for k, v in data.items() if k in ALLOWED_CONFIG_KEYS}
    section = {**existing.get(profile, {}), **filtered}
    existing = {**existing, profile: section}

    # TOML 직렬화 (tomllib은 읽기 전용이므로 직접 작성)
    # 값에 따옴표/백슬래시/개행이 포함될 수 있으므로 이스케이프 처리
    lines = []
    for prof, values in existing.items():
        if not _PROFILE_NAME_RE.match(prof):
            raise ValueError(
                f"Invalid profile name '{prof}': only letters, digits, hyphens, and underscores are allowed."
            )
        lines.append(f"[{prof}]")
        for k, v in values.items():
            lines.append(f'{k} = "{escape_toml_string(str(v))}"')
        lines.append("")

    CONFIG_FILE.write_text("\n".join(lines), encoding="utf-8")
    # API 키가 포함되므로 소유자만 읽기/쓰기 가능하도록 권한 제한 (0o600)
    try:
        CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows 등 chmod 미지원 환경에서는 무시


# ── Preset 시스템 ─────────────────────────────────────────────────────────────

PRESETS_DIR = CONFIG_DIR / "presets"


@dataclass
class Preset:
    """설정 프리셋."""

    name: str
    description: str = ""
    task_mode: str = "main-sub"
    upload_level: str = "metadata"
    drift_sensitivity: float = 0.5
    drift_cooldown: int = 3


BUILTIN_PRESETS: dict[str, Preset] = {
    "minimal": Preset(
        name="minimal",
        description="최소 설정",
        task_mode="flat",
        upload_level="none",
    ),
    "standard": Preset(
        name="standard",
        description="표준 설정",
        task_mode="main-sub",
        upload_level="metadata",
    ),
    "verbose": Preset(
        name="verbose",
        description="상세 기록",
        task_mode="main-sub",
        upload_level="full",
    ),
}


def _parse_preset(section: dict, default_name: str) -> "Preset":
    """TOML 섹션 딕셔너리에서 Preset 객체를 생성한다."""
    return Preset(
        name=section.get("name", default_name),
        description=section.get("description", ""),
        task_mode=section.get("task_mode", "main-sub"),
        upload_level=section.get("upload_level", "metadata"),
        drift_sensitivity=max(0.0, min(1.0, float(section.get("drift_sensitivity", 0.5)))),
        drift_cooldown=max(0, int(section.get("drift_cooldown", 3))),
    )


def list_presets() -> list[Preset]:
    """빌트인 + 사용자 프리셋 목록을 반환한다."""
    presets = list(BUILTIN_PRESETS.values())

    # 사용자 프리셋 로드
    if PRESETS_DIR.exists():
        for p in sorted(PRESETS_DIR.glob("*.toml")):
            try:
                with open(p, "rb") as f:
                    data = tomllib.load(f)
                preset_section = data.get("preset", {})
                if not isinstance(preset_section, dict):
                    continue
                preset = _parse_preset(preset_section, p.stem)
                presets.append(preset)
            except (OSError, tomllib.TOMLDecodeError, ValueError) as e:
                print(f"경고: 프리셋 파일 파싱 오류 ({p}): {e}", file=sys.stderr)
                continue

    return presets


def load_preset(name: str) -> Preset | None:
    """이름으로 프리셋을 로드한다. 빌트인 우선, 사용자 프리셋 검색."""
    if name in BUILTIN_PRESETS:
        return BUILTIN_PRESETS[name]

    # 이름 형식 검증 (경로 트래버설 방지): 영문자, 숫자, 하이픈, 밑줄만 허용
    if not _PROFILE_NAME_RE.match(name):
        return None

    # 사용자 프리셋 파일 검색
    preset_file = PRESETS_DIR / f"{name}.toml"

    # 경로 트래버설 최종 방어 (resolve 후 PRESETS_DIR 하위인지 확인)
    try:
        if not preset_file.resolve().is_relative_to(PRESETS_DIR.resolve()):
            return None
    except ValueError:
        return None

    if not preset_file.exists():
        return None

    try:
        with open(preset_file, "rb") as f:
            data = tomllib.load(f)
        preset_section = data.get("preset", {})
        if not isinstance(preset_section, dict):
            return None
        return _parse_preset(preset_section, name)
    except (OSError, tomllib.TOMLDecodeError, ValueError):
        return None


def save_preset(preset: Preset) -> None:
    """사용자 프리셋을 TOML 파일로 저장한다."""
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)

    # 프리셋 이름 검증
    if not _PROFILE_NAME_RE.match(preset.name):
        raise ValueError(
            f"프리셋 이름 '{preset.name}'에 허용되지 않는 문자가 포함되어 있습니다. "
            "영문자, 숫자, 하이픈, 밑줄만 사용 가능합니다."
        )

    preset_file = PRESETS_DIR / f"{preset.name}.toml"
    # 경로 트래버설 최종 방어 (load_preset과 동일한 수준)
    if not preset_file.resolve().is_relative_to(PRESETS_DIR.resolve()):
        raise ValueError(f"프리셋 경로가 허용 디렉토리를 벗어남: {preset.name!r}")
    lines = [
        "[preset]",
        f'name = "{escape_toml_string(preset.name)}"',
        f'description = "{escape_toml_string(preset.description)}"',
        f'task_mode = "{escape_toml_string(preset.task_mode)}"',
        f'upload_level = "{escape_toml_string(preset.upload_level)}"',
        f"drift_sensitivity = {preset.drift_sensitivity}",
        f"drift_cooldown = {preset.drift_cooldown}",
        "",
    ]
    preset_file.write_text("\n".join(lines), encoding="utf-8")


def apply_preset(preset: Preset, profile: str = "default") -> None:
    """프리셋을 현재 프로필에 적용한다."""
    save_config(
        {
            "task_mode": preset.task_mode,
            "upload_level": preset.upload_level,
            "drift_sensitivity": str(preset.drift_sensitivity),
            "drift_cooldown": str(preset.drift_cooldown),
        },
        profile=profile,
    )


def list_profiles() -> list[str]:
    """저장된 프로필 목록을 반환한다."""
    if not CONFIG_FILE.exists():
        return []
    try:
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        return list(data.keys())
    except (OSError, tomllib.TOMLDecodeError) as e:
        print(f"경고: 프로필 목록 읽기 실패 ({CONFIG_FILE}): {e}", file=sys.stderr)
        return []
