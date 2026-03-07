"""ST-14: TaskFormat - _get_task_mode, _apply_task_labels 테스트."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, call, patch

import pytest

from oh_my_kanban.hooks.session_start import _apply_task_labels, _get_task_mode


# ── _get_task_mode ────────────────────────────────────────────────────────────


class _FakeCfg:
    task_mode: str = "main-sub"
    api_key: str = "key"
    workspace_slug: str = "ws"
    project_id: str = "proj-uuid"
    base_url: str = "https://plane.example.com"


def test_get_task_mode_default():
    """task_mode 속성이 없으면 'main-sub'를 반환한다."""

    class _NoCfg:
        pass

    assert _get_task_mode(_NoCfg()) == "main-sub"


def test_get_task_mode_main_sub():
    """task_mode='main-sub'이면 그대로 반환한다."""
    cfg = _FakeCfg()
    cfg.task_mode = "main-sub"
    assert _get_task_mode(cfg) == "main-sub"


def test_get_task_mode_module_task_sub():
    """task_mode='module-task-sub'이면 그대로 반환한다."""
    cfg = _FakeCfg()
    cfg.task_mode = "module-task-sub"
    assert _get_task_mode(cfg) == "module-task-sub"


def test_get_task_mode_empty_string_fallback():
    """task_mode=''이면 falsy이므로 'main-sub'를 반환한다."""
    cfg = _FakeCfg()
    cfg.task_mode = ""
    assert _get_task_mode(cfg) == "main-sub"


def test_get_task_mode_none_fallback():
    """task_mode=None이면 falsy이므로 'main-sub'를 반환한다."""
    cfg = _FakeCfg()
    cfg.task_mode = None  # type: ignore[assignment]
    assert _get_task_mode(cfg) == "main-sub"


# ── _apply_task_labels ────────────────────────────────────────────────────────


def _make_mock_client(label_id: str | None = "label-uuid-session"):
    """httpx.Client 컨텍스트 매니저를 모의한다."""
    mock_client = MagicMock()
    mock_client.patch.return_value = MagicMock(status_code=200)

    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)
    return mock_client, mock_cm


def test_apply_task_labels_main_patches_wi():
    """is_main=True 이면 omk:session + omk:type:main 라벨로 PATCH 한다."""
    cfg = _FakeCfg()
    mock_client, mock_cm = _make_mock_client()

    label_ids_by_name = {
        "omk:session": "id-session",
        "omk:type:main": "id-main",
        "omk:type:sub": "id-sub",
    }

    def fake_get_label_id(name, project_id, c):
        return label_ids_by_name.get(name)

    # _apply_task_labels 안에서 from label_conventions import get_label_id_by_name 하므로
    # 소스 모듈인 label_conventions를 패치한다
    with (
        patch("httpx.Client", return_value=mock_cm),
        patch(
            "oh_my_kanban.hooks.label_conventions.get_label_id_by_name",
            side_effect=fake_get_label_id,
        ),
    ):
        _apply_task_labels("wi-uuid-001", cfg, is_main=True)

    # PATCH 한 번 호출됐는지
    mock_client.patch.assert_called_once()
    _, kwargs = mock_client.patch.call_args
    patched_ids = kwargs["json"]["label_ids"]
    assert "id-session" in patched_ids
    assert "id-main" in patched_ids
    assert "id-sub" not in patched_ids


def test_apply_task_labels_sub_uses_type_sub():
    """is_main=False 이면 omk:session + omk:type:sub 라벨을 적용한다."""
    cfg = _FakeCfg()
    mock_client, mock_cm = _make_mock_client()

    label_ids_by_name = {
        "omk:session": "id-session",
        "omk:type:main": "id-main",
        "omk:type:sub": "id-sub",
    }

    def fake_get_label_id(name, project_id, c):
        return label_ids_by_name.get(name)

    with (
        patch("httpx.Client", return_value=mock_cm),
        patch(
            "oh_my_kanban.hooks.label_conventions.get_label_id_by_name",
            side_effect=fake_get_label_id,
        ),
    ):
        _apply_task_labels("wi-uuid-002", cfg, is_main=False)

    _, kwargs = mock_client.patch.call_args
    patched_ids = kwargs["json"]["label_ids"]
    assert "id-session" in patched_ids
    assert "id-sub" in patched_ids
    assert "id-main" not in patched_ids


def test_apply_task_labels_no_api_key_returns_early():
    """api_key가 없으면 아무것도 하지 않는다."""
    cfg = _FakeCfg()
    cfg.api_key = ""

    with patch("httpx.Client") as mock_httpx:
        _apply_task_labels("wi-uuid-003", cfg, is_main=True)
        mock_httpx.assert_not_called()


def test_apply_task_labels_no_project_id_returns_early():
    """project_id가 없으면 아무것도 하지 않는다."""
    cfg = _FakeCfg()
    cfg.project_id = ""

    with patch("httpx.Client") as mock_httpx:
        _apply_task_labels("wi-uuid-004", cfg, is_main=True)
        mock_httpx.assert_not_called()


def test_apply_task_labels_label_not_found_skips_patch():
    """라벨 ID를 조회하지 못하면 PATCH 하지 않는다."""
    cfg = _FakeCfg()
    mock_client, mock_cm = _make_mock_client()

    with (
        patch("httpx.Client", return_value=mock_cm),
        patch(
            "oh_my_kanban.hooks.label_conventions.get_label_id_by_name",
            return_value=None,
        ),
    ):
        _apply_task_labels("wi-uuid-005", cfg, is_main=True)

    mock_client.patch.assert_not_called()


def test_apply_task_labels_fail_open_on_exception():
    """PATCH 중 예외가 발생해도 전파되지 않는다 (fail-open)."""
    cfg = _FakeCfg()
    mock_client, mock_cm = _make_mock_client()
    mock_client.patch.side_effect = Exception("서버 오류")

    label_ids_by_name = {"omk:session": "id-s", "omk:type:main": "id-m"}

    def fake_get_label_id(name, project_id, c):
        return label_ids_by_name.get(name)

    with (
        patch("httpx.Client", return_value=mock_cm),
        patch(
            "oh_my_kanban.hooks.label_conventions.get_label_id_by_name",
            side_effect=fake_get_label_id,
        ),
    ):
        # 예외가 전파되지 않아야 한다
        _apply_task_labels("wi-uuid-006", cfg, is_main=True)
