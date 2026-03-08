from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).parent.parent
SKILLS_DIR = ROOT / "skills"
PACKAGED_SKILLS_DIR = ROOT / "src" / "oh_my_kanban" / "plugin_data" / "skills"
MARKETPLACE_JSON = ROOT / "src" / "oh_my_kanban" / "plugin_data" / ".claude-plugin" / "marketplace.json"
PLUGIN_JSON = ROOT / "src" / "oh_my_kanban" / "plugin_data" / ".claude-plugin" / "plugin.json"
KOREAN_RE = re.compile(r"[가-힣]")

ROOT_TO_PACKAGED_SKILLS = sorted(
    path.parent.name
    for path in PACKAGED_SKILLS_DIR.glob("*/SKILL.md")
    if (SKILLS_DIR / path.parent.name / "SKILL.md").exists()
)


def test_marketplace_skill_docs_are_english() -> None:
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        content = path.read_text(encoding="utf-8")
        assert not KOREAN_RE.search(content), f"Korean text remains in {path}"

    for path in sorted(PACKAGED_SKILLS_DIR.glob("*/SKILL.md")):
        content = path.read_text(encoding="utf-8")
        assert not KOREAN_RE.search(content), f"Korean text remains in {path}"


def test_packaged_marketplace_skill_docs_match_root_sources() -> None:
    for skill_name in ROOT_TO_PACKAGED_SKILLS:
        root_skill = SKILLS_DIR / skill_name / "SKILL.md"
        packaged_skill = PACKAGED_SKILLS_DIR / skill_name / "SKILL.md"
        assert root_skill.read_text(encoding="utf-8") == packaged_skill.read_text(encoding="utf-8")


def test_known_skill_doc_drifts_are_removed() -> None:
    assert "main_task_id" not in (SKILLS_DIR / "omk-create-task" / "SKILL.md").read_text(encoding="utf-8")
    assert "main_task_id" not in (SKILLS_DIR / "omk-status" / "SKILL.md").read_text(encoding="utf-8")
    assert "main_task_id" not in (SKILLS_DIR / "omk-subtask" / "SKILL.md").read_text(encoding="utf-8")
    assert "update_hud()" not in (SKILLS_DIR / "omk-focus" / "SKILL.md").read_text(encoding="utf-8")
    assert "--delete-tasks" not in (SKILLS_DIR / "omk-new-session" / "SKILL.md").read_text(encoding="utf-8")
    assert "--delete-tasks" not in (PACKAGED_SKILLS_DIR / "omk-off" / "SKILL.md").read_text(encoding="utf-8")
    assert "omk setup" not in (SKILLS_DIR / "omk-setup" / "SKILL.md").read_text(encoding="utf-8")
    setup_content = (SKILLS_DIR / "omk-setup" / "SKILL.md").read_text(encoding="utf-8")
    assert "omk config init" in setup_content
    assert "omk hooks install" in setup_content
    assert "omk hooks status" in setup_content
    focus_content = (SKILLS_DIR / "omk-focus" / "SKILL.md").read_text(encoding="utf-8")
    status_content = (SKILLS_DIR / "omk-status" / "SKILL.md").read_text(encoding="utf-8")
    snapshot_content = (SKILLS_DIR / "omk-snapshot" / "SKILL.md").read_text(encoding="utf-8")
    session_summary_content = (SKILLS_DIR / "omk-session-summary" / "SKILL.md").read_text(encoding="utf-8")
    new_session_content = (SKILLS_DIR / "omk-new-session" / "SKILL.md").read_text(encoding="utf-8")

    assert "~/.config/oh-my-kanban/sessions/" in focus_content
    assert "~/.local/share/oh-my-kanban" not in focus_content
    assert "~/.config/oh-my-kanban/sessions/" in status_content
    assert "~/.local/share/oh-my-kanban" not in status_content
    assert "omk snapshot save" not in snapshot_content
    assert "omk snapshot restore" not in snapshot_content
    assert "not implemented in the current release" in snapshot_content
    assert "does **not** post the full SessionEnd summary comment" in session_summary_content
    assert "does **not** post the normal SessionEnd summary comment" in new_session_content


def test_marketplace_metadata_is_english() -> None:
    marketplace = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    plugin = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))

    assert not KOREAN_RE.search(marketplace["description"])
    assert not KOREAN_RE.search(marketplace["plugins"][0]["description"])
    assert not KOREAN_RE.search(plugin["description"])
