"""ST-10: Label 컨벤션 초기화 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from oh_my_kanban.hooks.label_conventions import (
    OMK_LABELS,
    OmkLabel,
    ensure_omk_labels,
    get_label_id_by_name,
)


# ── OMK_LABELS 상수 검증 ──────────────────────────────────────────────────────

def test_omk_labels_has_session_label():
    """omk:session 라벨이 정의되어 있어야 한다."""
    names = {lbl.name for lbl in OMK_LABELS}
    assert "omk:session" in names


def test_omk_labels_has_type_main():
    """omk:type:main 라벨이 정의되어 있어야 한다."""
    names = {lbl.name for lbl in OMK_LABELS}
    assert "omk:type:main" in names


def test_omk_labels_has_type_sub():
    """omk:type:sub 라벨이 정의되어 있어야 한다."""
    names = {lbl.name for lbl in OMK_LABELS}
    assert "omk:type:sub" in names


def test_omk_labels_colors():
    """표준 라벨 색상이 올바르게 정의되어 있어야 한다."""
    label_map = {lbl.name: lbl.color for lbl in OMK_LABELS}
    assert label_map["omk:session"] == "#6366F1"
    assert label_map["omk:type:main"] == "#10B981"
    assert label_map["omk:type:sub"] == "#6EE7B7"


def test_omk_label_is_frozen():
    """OmkLabel이 frozen dataclass여야 한다."""
    lbl = OmkLabel(name="test", color="#000000", description="test")
    with pytest.raises((AttributeError, TypeError)):
        lbl.name = "changed"  # type: ignore[misc]


# ── ensure_omk_labels 테스트 ─────────────────────────────────────────────────

_TEST_PROJECT_UUID = "00000000-0000-0000-0000-000000000001"


class _FakeCfg:
    api_key = "test_key"
    workspace_slug = "test_ws"
    base_url = "https://plane.example.com"
    project_id = _TEST_PROJECT_UUID


def _make_mock_response(status_code: int, json_data) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def test_ensure_omk_labels_creates_missing(capsys):
    """존재하지 않는 라벨은 생성되어야 한다."""
    cfg = _FakeCfg()
    mock_client = MagicMock()

    # GET labels — 빈 목록 반환
    mock_client.get.return_value = _make_mock_response(200, {"results": []})
    # POST label — 성공
    mock_client.post.return_value = _make_mock_response(201, {"id": "new-label-id"})

    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_cm):
        ensure_omk_labels(_TEST_PROJECT_UUID, cfg)

    # 3개 라벨 생성 시도
    assert mock_client.post.call_count == len(OMK_LABELS)
    posted_names = {
        call.kwargs["json"]["name"]
        for call in mock_client.post.call_args_list
    }
    assert posted_names == {label.name for label in OMK_LABELS}


def test_ensure_omk_labels_idempotent(capsys):
    """이미 존재하는 라벨은 재생성하지 않아야 한다."""
    cfg = _FakeCfg()
    mock_client = MagicMock()

    # GET labels — 모든 표준 라벨 이미 존재
    existing = [{"name": lbl.name, "id": f"id-{i}"} for i, lbl in enumerate(OMK_LABELS)]
    mock_client.get.return_value = _make_mock_response(200, {"results": existing})

    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_cm):
        ensure_omk_labels(_TEST_PROJECT_UUID, cfg)

    # POST 없어야 함
    mock_client.post.assert_not_called()


def test_ensure_omk_labels_no_api_key():
    """API 키 없으면 아무것도 하지 않아야 한다."""
    cfg = MagicMock()
    cfg.api_key = ""
    cfg.workspace_slug = "ws"
    cfg.project_id = "proj"

    with patch("httpx.Client") as mock_httpx:
        ensure_omk_labels("proj", cfg)
        mock_httpx.assert_not_called()


def test_ensure_omk_labels_fail_open(capsys):
    """API 실패 시 예외를 전파하지 않아야 한다 (fail-open)."""
    cfg = _FakeCfg()

    with patch("httpx.Client", side_effect=Exception("연결 실패")):
        # 예외가 전파되지 않아야 한다
        ensure_omk_labels(_TEST_PROJECT_UUID, cfg)


def test_ensure_omk_labels_partial_create(capsys):
    """일부 라벨만 없으면 없는 것만 생성해야 한다."""
    cfg = _FakeCfg()
    mock_client = MagicMock()

    # omk:session만 존재
    existing = [{"name": "omk:session", "id": "existing-id"}]
    mock_client.get.return_value = _make_mock_response(200, {"results": existing})
    mock_client.post.return_value = _make_mock_response(201, {"id": "new-id"})

    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_cm):
        ensure_omk_labels(_TEST_PROJECT_UUID, cfg)

    # omk:type:main, omk:type:sub 2개만 생성
    assert mock_client.post.call_count == 2


# ── get_label_id_by_name 테스트 ───────────────────────────────────────────────

def test_get_label_id_by_name_found():
    """라벨이 있으면 UUID를 반환해야 한다."""
    cfg = _FakeCfg()
    mock_client = MagicMock()
    mock_client.get.return_value = _make_mock_response(
        200,
        {"results": [{"name": "omk:session", "id": "label-uuid-123"}]},
    )
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_cm):
        result = get_label_id_by_name("omk:session", _TEST_PROJECT_UUID, cfg)

    assert result == "label-uuid-123"


def test_get_label_id_by_name_not_found():
    """라벨이 없으면 None을 반환해야 한다."""
    cfg = _FakeCfg()
    mock_client = MagicMock()
    mock_client.get.return_value = _make_mock_response(200, {"results": []})
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_cm):
        result = get_label_id_by_name("omk:session", _TEST_PROJECT_UUID, cfg)

    assert result is None
