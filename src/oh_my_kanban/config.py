"""설정 관리: TOML 프로필 + 환경변수 + CLAUDE.md 자동 감지."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# 프로필 이름 허용 문자: 영문자, 숫자, 하이픈, 밑줄만 허용 (TOML 섹션 헤더 인젝션 방지)
_PROFILE_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')

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
_ROOT_SCALAR_KEYS = {"output", "active_profile"}
_LEGACY_PLANE_KEYS = ("base_url", "api_key", "workspace_slug", "project_id")
_LEGACY_LINEAR_KEYS = ("linear_api_key", "linear_team_id")
_INTERNAL_KEY_MAP = {
    "output": ("output",),
    "base_url": ("plane", "base_url"),
    "api_key": ("plane", "api_key"),
    "workspace_slug": ("plane", "workspace_slug"),
    "project_id": ("plane", "project_id"),
    "linear_api_key": ("linear", "api_key"),
    "linear_team_id": ("linear", "team_id"),
    "plane.base_url": ("plane", "base_url"),
    "plane.api_key": ("plane", "api_key"),
    "plane.workspace_slug": ("plane", "workspace_slug"),
    "plane.project_id": ("plane", "project_id"),
    "linear.api_key": ("linear", "api_key"),
    "linear.team_id": ("linear", "team_id"),
}


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


def _empty_profile_section() -> dict:
    """Return normalized profile storage."""

    return {
        "output": "table",
        "plane": {
            "base_url": DEFAULT_BASE_URL,
            "api_key": "",
            "workspace_slug": "",
            "project_id": "",
        },
        "linear": {
            "api_key": "",
            "team_id": "",
        },
        "_other_root": {},
        "_other_sections": {},
    }


def _normalize_profile_section(section: dict) -> dict:
    """Normalize a raw TOML profile section into the canonical nested shape."""

    normalized = _empty_profile_section()
    plane = section.get("plane", {}) if isinstance(section.get("plane"), dict) else {}
    linear = section.get("linear", {}) if isinstance(section.get("linear"), dict) else {}

    normalized["output"] = str(section.get("output", normalized["output"]))
    normalized["plane"]["base_url"] = str(plane.get("base_url", section.get("base_url", DEFAULT_BASE_URL)))
    normalized["plane"]["api_key"] = str(plane.get("api_key", section.get("api_key", "")))
    normalized["plane"]["workspace_slug"] = str(
        plane.get("workspace_slug", section.get("workspace_slug", ""))
    )
    normalized["plane"]["project_id"] = str(plane.get("project_id", section.get("project_id", "")))
    normalized["linear"]["api_key"] = str(
        linear.get("api_key", section.get("linear_api_key", ""))
    )
    normalized["linear"]["team_id"] = str(
        linear.get("team_id", section.get("linear_team_id", ""))
    )

    reserved = _ROOT_SCALAR_KEYS | set(_LEGACY_PLANE_KEYS) | set(_LEGACY_LINEAR_KEYS) | {"plane", "linear"}
    for key, value in section.items():
        if key in reserved:
            continue
        if isinstance(value, dict):
            normalized["_other_sections"][key] = value
        else:
            normalized["_other_root"][key] = value
    return normalized


def _toml_literal(value: object) -> str:
    """Serialize a Python scalar to a TOML literal."""

    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return f'"{_escape_toml_string(str(value))}"'


def _serialize_nested_tables(lines: list[str], prefix: str, data: dict) -> None:
    """Recursively serialize nested TOML tables."""

    lines.append(f"[{prefix}]")
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_toml_literal(value)}")
    lines.append("")

    for key, value in data.items():
        if isinstance(value, dict):
            _serialize_nested_tables(lines, f"{prefix}.{key}", value)


def _set_profile_value(profile_data: dict, key: str, value: object) -> None:
    """Apply an internal or dotted config key to normalized profile data."""

    target = _INTERNAL_KEY_MAP.get(key)
    if target is None:
        profile_data["_other_root"][key] = value
        return
    if len(target) == 1:
        profile_data[target[0]] = value
        return
    section_name, field_name = target
    profile_data[section_name][field_name] = value


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
            section = _normalize_profile_section(data.get(profile, data.get("default", {})))
            cfg.output = str(section["output"])
            cfg.base_url = str(section["plane"]["base_url"])
            cfg.api_key = str(section["plane"]["api_key"])
            cfg.workspace_slug = str(section["plane"]["workspace_slug"])
            cfg.project_id = str(section["plane"]["project_id"])
            cfg.linear_api_key = str(section["linear"]["api_key"])
            cfg.linear_team_id = str(section["linear"]["team_id"])
        except (OSError, tomllib.TOMLDecodeError) as e:
            import sys
            print(f"경고: 설정 파일 파싱 오류 ({CONFIG_FILE}): {e}", file=sys.stderr)

    # 2. 환경변수 오버라이드
    cfg.base_url = os.environ.get("PLANE_BASE_URL", cfg.base_url)
    cfg.api_key = os.environ.get("PLANE_API_KEY", cfg.api_key)
    cfg.workspace_slug = os.environ.get("PLANE_WORKSPACE_SLUG", cfg.workspace_slug)
    cfg.project_id = os.environ.get("PLANE_PROJECT_ID", cfg.project_id)
    if env_val := os.environ.get("LINEAR_API_KEY"):
        cfg.linear_api_key = env_val
    if env_val := os.environ.get("LINEAR_TEAM_ID"):
        cfg.linear_team_id = env_val

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

    normalized_profiles: dict[str, dict] = {}
    for prof, values in existing.items():
        if not isinstance(values, dict):
            continue
        normalized_profiles[prof] = _normalize_profile_section(values)

    profile_data = normalized_profiles.setdefault(profile, _empty_profile_section())
    for key, value in data.items():
        _set_profile_value(profile_data, key, value)

    lines = []
    for prof, values in normalized_profiles.items():
        if not _PROFILE_NAME_RE.match(prof):
            raise ValueError(
                f"Invalid profile name '{prof}': only letters, digits, hyphens, and underscores are allowed."
            )
        lines.append(f"[{prof}]")
        lines.append(f'output = "{_escape_toml_string(str(values["output"]))}"')
        for key, value in values["_other_root"].items():
            lines.append(f"{key} = {_toml_literal(value)}")
        lines.append("")

        if any(str(value) for value in values["plane"].values()):
            _serialize_nested_tables(lines, f"{prof}.plane", values["plane"])
        if any(str(value) for value in values["linear"].values()):
            _serialize_nested_tables(lines, f"{prof}.linear", values["linear"])
        for key, value in values["_other_sections"].items():
            _serialize_nested_tables(lines, f"{prof}.{key}", value)

    CONFIG_FILE.write_text("\n".join(lines), encoding="utf-8")


def list_profiles() -> list[str]:
    """저장된 프로필 목록을 반환한다."""
    if not CONFIG_FILE.exists():
        return []
    try:
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        return [name for name in data.keys() if name != "_meta"]
    except (OSError, tomllib.TOMLDecodeError) as e:
        import sys
        print(f"경고: 프로필 목록 읽기 실패 ({CONFIG_FILE}): {e}", file=sys.stderr)
        return []
