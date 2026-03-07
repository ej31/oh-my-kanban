"""설정 관리: TOML 프로필 + 환경변수 + CLAUDE.md 자동 감지."""

from __future__ import annotations

import os
import re
import stat
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

# 프로필 이름 허용 문자: 영문자, 숫자, 하이픈, 밑줄만 허용 (TOML 섹션 헤더 인젝션 방지)
_PROFILE_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')

# workspace_slug 허용 형식: 영문자, 숫자, 하이픈 (Plane slug 형식)
_SLUG_RE = re.compile(r'^[a-zA-Z0-9_-]+$')

# 허용 태스크 모드 / 업로드 레벨 / 형식 프리셋
_VALID_TASK_MODES = frozenset({"main-sub", "module-task-sub"})
_VALID_UPLOAD_LEVELS = frozenset({"metadata", "full"})
_VALID_FORMAT_PRESETS = frozenset({"detailed", "normal", "eco"})

# 저장 허용 설정 키 화이트리스트 (임의 키 TOML 인젝션 방지)
_ALLOWED_CONFIG_KEYS = frozenset({
    "base_url", "api_key", "workspace_slug", "project_id",
    "output", "linear_api_key", "linear_team_id",
    "drift_sensitivity", "drift_cooldown",
    "task_mode", "upload_level", "auto_archive_days",
    "auto_complete_subtasks", "session_retention_days", "format_preset",
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
    # WI 워크플로우 설정
    task_mode: str = "main-sub"          # "main-sub" | "module-task-sub"
    upload_level: str = "metadata"       # "metadata" | "full"
    auto_archive_days: int = 7           # 0이면 비활성화
    auto_complete_subtasks: bool = True
    session_retention_days: int = 30
    format_preset: str = "normal"        # "detailed" | "normal" | "eco"


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


def load_config(profile: str = "default") -> Config:
    """설정을 로드한다. 우선순위: env vars > TOML 파일."""
    cfg = Config(profile=profile)

    # 1. TOML 파일에서 기본값 로드
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as f:
                data = tomllib.load(f)
            section = data.get(profile, data.get("default", {}))
            cfg.base_url = section.get("base_url", cfg.base_url)
            cfg.api_key = section.get("api_key", cfg.api_key)
            cfg.workspace_slug = section.get("workspace_slug", cfg.workspace_slug)
            cfg.project_id = section.get("project_id", cfg.project_id)
            cfg.output = section.get("output", cfg.output)
            cfg.linear_api_key = section.get("linear_api_key", cfg.linear_api_key)
            cfg.linear_team_id = section.get("linear_team_id", cfg.linear_team_id)
            if "drift_sensitivity" in section:
                cfg.drift_sensitivity = max(0.0, min(1.0, float(section["drift_sensitivity"])))
            if "drift_cooldown" in section:
                cfg.drift_cooldown = max(0, int(section["drift_cooldown"]))
            if "task_mode" in section:
                val = section["task_mode"]
                if val in _VALID_TASK_MODES:
                    cfg.task_mode = val
                else:
                    print(
                        f"경고: task_mode='{val}'은 유효하지 않습니다. "
                        f"허용 값: {', '.join(sorted(_VALID_TASK_MODES))}. 기본값 유지.",
                        file=sys.stderr,
                    )
            if "upload_level" in section:
                val = section["upload_level"]
                if val in _VALID_UPLOAD_LEVELS:
                    cfg.upload_level = val
                else:
                    print(
                        f"경고: upload_level='{val}'은 유효하지 않습니다. "
                        f"허용 값: {', '.join(sorted(_VALID_UPLOAD_LEVELS))}. 기본값 유지.",
                        file=sys.stderr,
                    )
            if "auto_archive_days" in section:
                cfg.auto_archive_days = max(0, int(section["auto_archive_days"]))
            if "auto_complete_subtasks" in section:
                val = section["auto_complete_subtasks"]
                cfg.auto_complete_subtasks = (
                    val if isinstance(val, bool) else str(val).lower() == "true"
                )
            if "session_retention_days" in section:
                cfg.session_retention_days = max(1, int(section["session_retention_days"]))
            if "format_preset" in section:
                val = section["format_preset"]
                if val in _VALID_FORMAT_PRESETS:
                    cfg.format_preset = val
                else:
                    print(
                        f"경고: format_preset='{val}'은 유효하지 않습니다. "
                        f"허용 값: {', '.join(sorted(_VALID_FORMAT_PRESETS))}. 기본값 유지.",
                        file=sys.stderr,
                    )
        except (OSError, tomllib.TOMLDecodeError) as e:
            print(f"경고: 설정 파일 파싱 오류 ({CONFIG_FILE}): {e}", file=sys.stderr)

    # 2. 환경변수 오버라이드
    if env_val := os.environ.get("PLANE_BASE_URL"):
        parsed = urllib.parse.urlparse(env_val)
        if parsed.scheme in ("https", "http") and parsed.hostname:
            cfg.base_url = env_val
        else:
            print(
                f"경고: PLANE_BASE_URL='{env_val}'이 유효하지 않습니다. "
                "https:// 또는 http:// 스킴과 호스트가 필요합니다. 기본값 유지.",
                file=sys.stderr,
            )
    cfg.api_key = os.environ.get("PLANE_API_KEY", cfg.api_key)
    if env_val := os.environ.get("PLANE_WORKSPACE_SLUG"):
        if _SLUG_RE.match(env_val):
            cfg.workspace_slug = env_val
        else:
            print(
                f"경고: PLANE_WORKSPACE_SLUG='{env_val}'은 유효하지 않습니다. "
                "영문자, 숫자, 하이픈, 밑줄만 허용됩니다. 기본값 유지.",
                file=sys.stderr,
            )
    cfg.project_id = os.environ.get("PLANE_PROJECT_ID", cfg.project_id)
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
    if env_val := os.environ.get("OMK_TASK_MODE"):
        if env_val in _VALID_TASK_MODES:
            cfg.task_mode = env_val
        else:
            print(
                f"경고: OMK_TASK_MODE='{env_val}'은 유효하지 않습니다. "
                f"허용 값: {', '.join(sorted(_VALID_TASK_MODES))}. 기본값 유지.",
                file=sys.stderr,
            )
    if env_val := os.environ.get("OMK_UPLOAD_LEVEL"):
        if env_val in _VALID_UPLOAD_LEVELS:
            cfg.upload_level = env_val
        else:
            print(
                f"경고: OMK_UPLOAD_LEVEL='{env_val}'은 유효하지 않습니다. "
                f"허용 값: {', '.join(sorted(_VALID_UPLOAD_LEVELS))}. 기본값 유지.",
                file=sys.stderr,
            )
    if env_val := os.environ.get("OMK_FORMAT_PRESET"):
        if env_val in _VALID_FORMAT_PRESETS:
            cfg.format_preset = env_val
        else:
            print(
                f"경고: OMK_FORMAT_PRESET='{env_val}'은 유효하지 않습니다. "
                f"허용 값: {', '.join(sorted(_VALID_FORMAT_PRESETS))}. 기본값 유지.",
                file=sys.stderr,
            )

    # 3. CLAUDE.md에서 project_id 자동 감지 (env/config에 없을 때)
    if not cfg.project_id:
        cfg.project_id = detect_project_id()

    return cfg


def _escape_toml_string(v: str) -> str:
    """TOML 기본 문자열에 포함될 값의 특수문자를 이스케이프한다."""
    return v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


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
    filtered = {k: v for k, v in data.items() if k in _ALLOWED_CONFIG_KEYS}
    section = {**existing.get(profile, {}), **filtered}
    existing = {**existing, profile: section}

    # TOML 직렬화 (tomllib은 읽기 전용이므로 직접 작성)
    # 값에 따옴표/백슬래시/개행이 포함될 수 있으므로 이스케이프 처리
    lines = []
    for prof, values in existing.items():
        if not _PROFILE_NAME_RE.match(prof):
            raise ValueError(
                f"Invalid profile name '{prof}':"
                " only letters, digits, hyphens, and underscores are allowed."
            )
        lines.append(f"[{prof}]")
        for k, v in values.items():
            if not re.match(r'^[a-zA-Z0-9_-]+$', str(k)):
                raise ValueError(f"Invalid config key: {k!r}")
            # TOML 네이티브 타입 사용 (bool/int/float)
            if isinstance(v, bool):
                lines.append(f'{k} = {"true" if v else "false"}')
            elif isinstance(v, int):
                lines.append(f'{k} = {v}')
            elif isinstance(v, float):
                lines.append(f'{k} = {v}')
            else:
                lines.append(f'{k} = "{_escape_toml_string(str(v))}"')
        lines.append("")

    CONFIG_FILE.write_text("\n".join(lines), encoding="utf-8")
    # API 키가 포함되므로 소유자만 읽기/쓰기 가능하도록 권한 제한 (0o600)
    try:
        CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows 등 chmod 미지원 환경에서는 무시


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
