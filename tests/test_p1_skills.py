"""ST-23: P1 스킬 파일 존재 여부 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest


# 프로젝트 루트에서 .claude/skills 경로 탐색
_SKILLS_DIR = Path(__file__).parent.parent / ".claude" / "skills"

_P1_SKILLS = [
    "omk-subtask.md",
    "omk-done.md",
    "omk-switch-task.md",
    "omk-decision.md",
    "omk-handoff.md",
    "omk-comments.md",
    "omk-me.md",
]


@pytest.mark.parametrize("skill_file", _P1_SKILLS)
def test_p1_skill_file_exists(skill_file: str):
    """P1 스킬 파일이 .claude/skills/ 디렉토리에 존재해야 한다."""
    skill_path = _SKILLS_DIR / skill_file
    assert skill_path.exists(), f"{skill_file} 스킬 파일이 없습니다: {skill_path}"


@pytest.mark.parametrize("skill_file", _P1_SKILLS)
def test_p1_skill_file_has_content(skill_file: str):
    """P1 스킬 파일이 비어있지 않아야 한다."""
    skill_path = _SKILLS_DIR / skill_file
    content = skill_path.read_text(encoding="utf-8")
    assert len(content.strip()) > 50, f"{skill_file}이 너무 짧습니다."


@pytest.mark.parametrize("skill_file,expected_keyword", [
    ("omk-subtask.md", "Sub-task"),
    ("omk-done.md", "완료"),
    ("omk-switch-task.md", "On Hold"),
    ("omk-decision.md", "결정"),
    ("omk-handoff.md", "핸드오프"),
    ("omk-comments.md", "댓글"),
    ("omk-me.md", "세션"),
])
def test_p1_skill_file_contains_key_concept(skill_file: str, expected_keyword: str):
    """P1 스킬 파일이 핵심 키워드를 포함해야 한다."""
    skill_path = _SKILLS_DIR / skill_file
    content = skill_path.read_text(encoding="utf-8")
    assert expected_keyword in content, f"{skill_file}에 '{expected_keyword}' 키워드가 없습니다."
