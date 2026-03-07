"""project_id 우선순위 체계 + detect_project_toml() + auto-detect 테스트."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from oh_my_kanban.config import Config, detect_project_toml, load_config


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _write_config(tmp_path: Path, content: str) -> Path:
    """임시 설정 파일을 작성하고 경로를 반환한다."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(content, encoding="utf-8")
    return config_file


def _write_project_toml(base: Path, project_id: str, provider: str = "plane") -> Path:
    """base/.omk/project.toml을 생성한다."""
    omk_dir = base / ".omk"
    omk_dir.mkdir(parents=True, exist_ok=True)
    toml_file = omk_dir / "project.toml"
    toml_file.write_text(
        f'[project]\nproject_id = "{project_id}"\nprovider = "{provider}"\n',
        encoding="utf-8",
    )
    return toml_file


# ── detect_project_toml() 테스트 ──────────────────────────────────────────────

class TestDetectProjectToml:
    """detect_project_toml() 함수 단위 테스트."""

    def test_finds_project_toml_in_cwd(self, tmp_path: Path) -> None:
        """cwd에 .omk/project.toml이 있으면 project_id를 반환한다."""
        pid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        _write_project_toml(tmp_path, pid, "plane")

        with patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path):
            result_pid, result_provider = detect_project_toml()

        assert result_pid == pid
        assert result_provider == "plane"

    def test_finds_project_toml_in_parent(self, tmp_path: Path) -> None:
        """상위 디렉토리에 .omk/project.toml이 있으면 찾는다."""
        pid = "11111111-2222-3333-4444-555555555555"
        _write_project_toml(tmp_path, pid, "linear")
        child = tmp_path / "sub" / "dir"
        child.mkdir(parents=True)

        with patch("oh_my_kanban.config.Path.cwd", return_value=child):
            result_pid, result_provider = detect_project_toml()

        assert result_pid == pid
        assert result_provider == "linear"

    def test_returns_empty_when_not_found(self, tmp_path: Path) -> None:
        """파일이 없으면 빈 튜플을 반환한다."""
        with patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path):
            result_pid, result_provider = detect_project_toml()

        assert result_pid == ""
        assert result_provider == ""

    def test_returns_empty_on_malformed_toml(self, tmp_path: Path) -> None:
        """TOML 파싱 실패 시 빈 튜플을 반환한다."""
        omk_dir = tmp_path / ".omk"
        omk_dir.mkdir()
        (omk_dir / "project.toml").write_text("이것은 = 올바르지 않은\nTOML", encoding="utf-8")

        with patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path):
            result_pid, result_provider = detect_project_toml()

        assert result_pid == ""
        assert result_provider == ""

    def test_returns_empty_on_wrong_structure(self, tmp_path: Path) -> None:
        """[project] 섹션이 dict가 아닌 잘못된 구조면 빈 튜플을 반환한다."""
        omk_dir = tmp_path / ".omk"
        omk_dir.mkdir()
        # project가 문자열이면 .get() 호출 시 AttributeError 가능 — 방어 필요
        (omk_dir / "project.toml").write_text('project = "oops"\n', encoding="utf-8")

        with patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path):
            result_pid, result_provider = detect_project_toml()

        assert result_pid == ""
        assert result_provider == ""

    def test_default_provider_is_plane(self, tmp_path: Path) -> None:
        """provider 필드가 없으면 기본값 plane을 반환한다."""
        omk_dir = tmp_path / ".omk"
        omk_dir.mkdir()
        (omk_dir / "project.toml").write_text(
            '[project]\nproject_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"\n',
            encoding="utf-8",
        )

        with patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path):
            _, provider = detect_project_toml()

        assert provider == "plane"


# ── load_config() 우선순위 테스트 ──────────────────────────────────────────────

class TestLoadConfigProjectIdPriority:
    """load_config()의 project_id 결정 우선순위 검증."""

    def test_env_has_highest_priority(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """환경변수 PLANE_PROJECT_ID가 모든 것보다 우선한다."""
        env_pid = "env-00000-0000-0000-000000000000"
        toml_pid = "toml-0000-0000-0000-000000000000"

        config_file = _write_config(
            tmp_path, f'[default]\nproject_id = "{toml_pid}"\n'
        )
        monkeypatch.setenv("PLANE_PROJECT_ID", env_pid)

        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            cfg = load_config()

        assert cfg.project_id == env_pid
        assert cfg.project_id_source == "env"

    def test_omk_project_toml_over_claude_md(self, tmp_path: Path) -> None:
        """.omk/project.toml이 CLAUDE.md보다 우선한다."""
        omk_pid = "aabbccdd-0000-0000-0000-000000000000"
        claude_pid = "eeff0011-0000-0000-0000-000000000000"

        _write_project_toml(tmp_path, omk_pid)

        # CLAUDE.md 생성
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(f"project_id: {claude_pid}", encoding="utf-8")

        config_file = _write_config(tmp_path, "[default]\n")

        with (
            patch("oh_my_kanban.config.CONFIG_FILE", config_file),
            patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path),
        ):
            cfg = load_config()

        assert cfg.project_id == omk_pid
        assert cfg.project_id_source == "omk_project_toml"

    def test_claude_md_over_config_toml(self, tmp_path: Path) -> None:
        """CLAUDE.md가 config.toml보다 우선한다."""
        claude_pid = "cafeface-1111-1111-1111-111111111111"
        toml_pid = "deadbeef-2222-2222-2222-222222222222"

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(f"project_id: {claude_pid}", encoding="utf-8")

        config_file = _write_config(
            tmp_path, f'[default]\nproject_id = "{toml_pid}"\n'
        )

        with (
            patch("oh_my_kanban.config.CONFIG_FILE", config_file),
            patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path),
        ):
            cfg = load_config()

        assert cfg.project_id == claude_pid
        assert cfg.project_id_source == "claude_md"

    def test_config_toml_fallback_with_deprecation_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """config.toml의 project_id는 fallback이며 deprecated 경고를 출력한다."""
        toml_pid = "tml-22222-2222-2222-222222222222"
        config_file = _write_config(
            tmp_path, f'[default]\nproject_id = "{toml_pid}"\n'
        )

        with (
            patch("oh_my_kanban.config.CONFIG_FILE", config_file),
            patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path),
        ):
            cfg = load_config()

        assert cfg.project_id == toml_pid
        assert cfg.project_id_source == "config_toml"

        captured = capsys.readouterr()
        assert "향후 제거 예정" in captured.err

    def test_no_project_id_anywhere(self, tmp_path: Path) -> None:
        """어디에도 project_id가 없으면 빈 문자열이다."""
        config_file = _write_config(tmp_path, "[default]\n")

        with (
            patch("oh_my_kanban.config.CONFIG_FILE", config_file),
            patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path),
        ):
            cfg = load_config()

        assert cfg.project_id == ""
        assert cfg.project_id_source == ""

    def test_project_id_source_field_exists(self) -> None:
        """Config dataclass에 project_id_source 필드가 존재한다."""
        cfg = Config()
        assert hasattr(cfg, "project_id_source")
        assert cfg.project_id_source == ""


# ── project_cmd CLI 테스트 ────────────────────────────────────────────────────

class TestProjectCmd:
    """omk project CLI 명령어 테스트."""

    def test_project_help(self, runner) -> None:
        """omk project --help는 bind, unbind, show, opt-out, opt-in을 보여야 한다."""
        from oh_my_kanban.cli import cli

        result = runner.invoke(cli, ["project", "--help"])
        assert result.exit_code == 0
        assert "bind" in result.output
        assert "unbind" in result.output
        assert "show" in result.output
        assert "opt-out" in result.output
        assert "opt-in" in result.output

    def test_project_bind_creates_toml(self, runner, tmp_path: Path) -> None:
        """omk project bind는 .omk/project.toml을 생성한다."""
        from oh_my_kanban.cli import cli

        pid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        with patch("oh_my_kanban.commands.project_cmd.Path.cwd", return_value=tmp_path):
            # _ensure_omk_gitignore에서 git 명령 실패해도 무시되도록
            with patch("oh_my_kanban.commands.project_cmd.subprocess.run", side_effect=OSError):
                result = runner.invoke(cli, ["project", "bind", pid])

        assert result.exit_code == 0
        assert "바인딩 완료" in result.output

        toml_path = tmp_path / ".omk" / "project.toml"
        assert toml_path.exists()
        content = toml_path.read_text(encoding="utf-8")
        assert pid in content
        assert 'provider = "plane"' in content

    def test_project_bind_invalid_uuid(self, runner) -> None:
        """잘못된 UUID 형식이면 에러를 출력한다."""
        from oh_my_kanban.cli import cli

        result = runner.invoke(cli, ["project", "bind", "not-a-uuid"])
        assert result.exit_code != 0

    def test_project_unbind_removes_toml(self, runner, tmp_path: Path) -> None:
        """omk project unbind는 .omk/project.toml을 삭제한다."""
        from oh_my_kanban.cli import cli

        _write_project_toml(tmp_path, "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        assert (tmp_path / ".omk" / "project.toml").exists()

        with patch("oh_my_kanban.commands.project_cmd.Path.cwd", return_value=tmp_path):
            result = runner.invoke(cli, ["project", "unbind"])

        assert result.exit_code == 0
        assert not (tmp_path / ".omk" / "project.toml").exists()

    def test_project_unbind_no_toml(self, runner, tmp_path: Path) -> None:
        """바인딩이 없을 때 unbind는 안내만 출력한다."""
        from oh_my_kanban.cli import cli

        with patch("oh_my_kanban.commands.project_cmd.Path.cwd", return_value=tmp_path):
            result = runner.invoke(cli, ["project", "unbind"])

        assert result.exit_code == 0
        assert "바인딩된 프로젝트가 없습니다" in result.output

    def test_project_show_with_binding(self, runner, tmp_path: Path) -> None:
        """바인딩이 있으면 show에서 project_id와 소스를 표시한다."""
        from oh_my_kanban.cli import cli

        pid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        _write_project_toml(tmp_path, pid)
        config_file = _write_config(tmp_path, "[default]\n")

        with (
            patch("oh_my_kanban.commands.project_cmd.Path.cwd", return_value=tmp_path),
            patch("oh_my_kanban.config.CONFIG_FILE", config_file),
            patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path),
        ):
            result = runner.invoke(cli, ["project", "show"])

        assert result.exit_code == 0
        assert pid in result.output

    def test_project_show_with_wrong_structure_toml(self, runner, tmp_path: Path) -> None:
        """project.toml 구조가 잘못되어도 show는 크래시하지 않는다."""
        from oh_my_kanban.cli import cli

        omk_dir = tmp_path / ".omk"
        omk_dir.mkdir()
        (omk_dir / "project.toml").write_text('project = "oops"\n', encoding="utf-8")
        config_file = _write_config(tmp_path, "[default]\n")

        with (
            patch("oh_my_kanban.commands.project_cmd.Path.cwd", return_value=tmp_path),
            patch("oh_my_kanban.config.CONFIG_FILE", config_file),
            patch("oh_my_kanban.config.Path.cwd", return_value=tmp_path),
        ):
            result = runner.invoke(cli, ["project", "show"])

        assert result.exit_code == 0
        assert "읽기 오류" in result.output

    def test_project_opt_out_creates_disabled(self, runner, tmp_path: Path) -> None:
        """omk project opt-out은 .omk/disabled 파일을 생성한다."""
        from oh_my_kanban.cli import cli

        with patch("oh_my_kanban.commands.project_cmd.Path.cwd", return_value=tmp_path):
            result = runner.invoke(cli, ["project", "opt-out"])

        assert result.exit_code == 0
        assert (tmp_path / ".omk" / "disabled").exists()
        assert "비활성화" in result.output

    def test_project_opt_in_removes_disabled(self, runner, tmp_path: Path) -> None:
        """omk project opt-in은 .omk/disabled 파일을 삭제한다."""
        from oh_my_kanban.cli import cli

        omk_dir = tmp_path / ".omk"
        omk_dir.mkdir()
        (omk_dir / "disabled").write_text("2026-01-01T00:00:00Z", encoding="utf-8")

        with patch("oh_my_kanban.commands.project_cmd.Path.cwd", return_value=tmp_path):
            result = runner.invoke(cli, ["project", "opt-in"])

        assert result.exit_code == 0
        assert not (tmp_path / ".omk" / "disabled").exists()
        assert "활성화" in result.output

    def test_project_opt_in_already_active(self, runner, tmp_path: Path) -> None:
        """이미 활성 상태이면 opt-in은 안내만 출력한다."""
        from oh_my_kanban.cli import cli

        with patch("oh_my_kanban.commands.project_cmd.Path.cwd", return_value=tmp_path):
            result = runner.invoke(cli, ["project", "opt-in"])

        assert result.exit_code == 0
        assert "이미 활성화 상태" in result.output


# ── SessionStart auto-detect 테스트 ──────────────────────────────────────────

class TestSessionStartAutoDetect:
    """SessionStart 훅의 프로젝트 opt-out 및 안내 주입 테스트."""

    def test_disabled_project_skips_session(self, tmp_path: Path) -> None:
        """프로젝트 disabled 마커가 있으면 세션 처리를 건너뛴다."""
        omk_dir = tmp_path / ".omk"
        omk_dir.mkdir()
        (omk_dir / "disabled").write_text("2026-01-01T00:00:00Z", encoding="utf-8")

        from oh_my_kanban.hooks.session_start import _is_project_disabled

        with patch("oh_my_kanban.hooks.session_start.Path.cwd", return_value=tmp_path):
            assert _is_project_disabled() is True

    def test_no_disabled_means_active(self, tmp_path: Path) -> None:
        """disabled 마커가 없으면 활성 상태이다."""
        from oh_my_kanban.hooks.session_start import _is_project_disabled

        with patch("oh_my_kanban.hooks.session_start.Path.cwd", return_value=tmp_path):
            assert _is_project_disabled() is False

    def test_guidance_injected_when_no_project_toml(self, tmp_path: Path) -> None:
        """project.toml이 없고 .prompted도 없으면 안내를 주입한다."""
        from oh_my_kanban.hooks.session_start import _inject_project_guidance

        captured = StringIO()
        with (
            patch("oh_my_kanban.hooks.session_start.Path.cwd", return_value=tmp_path),
            patch("sys.stdout", captured),
        ):
            _inject_project_guidance()

        output = captured.getvalue()
        assert output.strip()  # 뭔가 출력됨
        result = json.loads(output)
        assert "연결되지 않았습니다" in result["hookSpecificOutput"]["additionalContext"]

        # .omk/.prompted 마커가 생성되었는지 확인
        assert (tmp_path / ".omk" / ".prompted").exists()

    def test_guidance_skipped_when_project_toml_exists(self, tmp_path: Path) -> None:
        """project.toml이 있으면 안내를 주입하지 않는다."""
        from oh_my_kanban.hooks.session_start import _inject_project_guidance

        _write_project_toml(tmp_path, "a1b2c3d4-e5f6-7890-abcd-ef1234567890")

        captured = StringIO()
        with (
            patch("oh_my_kanban.hooks.session_start.Path.cwd", return_value=tmp_path),
            patch("sys.stdout", captured),
        ):
            _inject_project_guidance()

        assert captured.getvalue().strip() == ""  # 아무것도 출력 안 됨

    def test_guidance_skipped_when_already_prompted(self, tmp_path: Path) -> None:
        """.prompted 마커가 있으면 안내를 주입하지 않는다."""
        from oh_my_kanban.hooks.session_start import _inject_project_guidance

        omk_dir = tmp_path / ".omk"
        omk_dir.mkdir()
        (omk_dir / ".prompted").write_text("already-prompted", encoding="utf-8")

        captured = StringIO()
        with (
            patch("oh_my_kanban.hooks.session_start.Path.cwd", return_value=tmp_path),
            patch("sys.stdout", captured),
        ):
            _inject_project_guidance()

        assert captured.getvalue().strip() == ""  # 아무것도 출력 안 됨
