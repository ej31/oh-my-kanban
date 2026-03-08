from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parent.parent
ROOT_SKILL = ROOT / "skills" / "omk-github-projects" / "SKILL.md"
PACKAGED_SKILL = (
    ROOT / "src" / "oh_my_kanban" / "plugin_data" / "skills" / "omk-github-projects" / "SKILL.md"
)
HELP_SKILLS = [
    ROOT / "skills" / "omk-help" / "SKILL.md",
    ROOT / "src" / "oh_my_kanban" / "plugin_data" / "skills" / "omk-help" / "SKILL.md",
]


def test_github_projects_skill_exists_in_root_and_package() -> None:
    assert ROOT_SKILL.exists()
    assert PACKAGED_SKILL.exists()


def test_github_projects_skill_covers_required_workflow() -> None:
    root_content = ROOT_SKILL.read_text(encoding="utf-8")
    packaged_content = PACKAGED_SKILL.read_text(encoding="utf-8")

    assert root_content == packaged_content
    content = root_content

    required_terms = [
        "gh auth status",
        "gh auth refresh -s project",
        "gh project list",
        "gh project field-list",
        "gh project item-edit",
        "gh api graphql",
        "gh issue create",
        "gh issue comment",
        "gh issue close",
        "GitHub Projects",
        "omk gh",
        "organization(login: $owner)",
        "user(login: $owner)",
        "--limit 100",
        "--limit 200",
    ]

    for term in required_terms:
        assert term in content, f"missing required guidance: {term}"


def test_help_mentions_github_projects_skill() -> None:
    expected_row = (
        "| `/oh-my-kanban:github-projects` | Manage GitHub Projects WIs with `gh` CLI "
        "(`/omk:gh` alias) |"
    )

    for help_file in HELP_SKILLS:
        content = help_file.read_text(encoding="utf-8")
        assert expected_row in content
