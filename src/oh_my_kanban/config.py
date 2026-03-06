"""설정 관리: TOML 프로필 + 환경변수 + CLAUDE.md 자동 감지."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
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

    # 프로필 업데이트
    existing.setdefault(profile, {}).update(data)

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
            lines.append(f'{k} = "{_escape_toml_string(str(v))}"')
        lines.append("")

    CONFIG_FILE.write_text("\n".join(lines), encoding="utf-8")


def list_profiles() -> list[str]:
    """저장된 프로필 목록을 반환한다."""
    if not CONFIG_FILE.exists():
        return []
    try:
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        return list(data.keys())
    except (OSError, tomllib.TOMLDecodeError) as e:
        import sys
        print(f"경고: 프로필 목록 읽기 실패 ({CONFIG_FILE}): {e}", file=sys.stderr)
        return []
