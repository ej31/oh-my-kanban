"""common.py 공유 유틸리티 유닛 테스트."""
import sys
import json
from unittest.mock import patch, MagicMock
import pytest
from oh_my_kanban.hooks.common import (
    HookDiagnostic, SuccessNudge, HUD_TASK_NAME_MAX,
    notify_and_exit, notify_success, classify_api_error,
    build_wi_url, build_wi_identifier, sanitize_comment,
    update_hud, reset_hud, create_plane_http_client,
)

# HookDiagnostic 테스트
def test_hook_diagnostic_fields():
    d = HookDiagnostic(category="config_missing", message="설정 없음")
    assert d.category == "config_missing"
    assert d.wi_url == ""
    assert d.recovery_hint == ""

def test_hook_diagnostic_frozen():
    d = HookDiagnostic(category="auth_failure", message="인증 실패")
    with pytest.raises(Exception):  # frozen=True이므로 수정 불가
        d.category = "other"

# SuccessNudge 테스트
def test_success_nudge_fields():
    n = SuccessNudge(wi_identifier="OMK-5", wi_name="테스트 작업")
    assert n.wi_identifier == "OMK-5"
    assert n.wi_url == ""

# classify_api_error 테스트
def test_classify_404():
    d = classify_api_error(None, 404)
    assert d.category == "wi_deleted"

def test_classify_410():
    d = classify_api_error(None, 410)
    assert d.category == "wi_deleted"

def test_classify_401():
    d = classify_api_error(None, 401)
    assert d.category == "auth_failure"

def test_classify_429():
    d = classify_api_error(None, 429)
    assert d.category == "rate_limit"

def test_classify_500():
    d = classify_api_error(None, 500)
    assert d.category == "server_error"

def test_classify_timeout():
    import httpx
    exc = httpx.TimeoutException("timeout")
    d = classify_api_error(exc, None)
    assert d.category == "network_error"

# build_wi_url 테스트
def test_build_wi_url():
    url = build_wi_url("https://plane.example.com", "my-ws", "proj-id", 42)
    assert url == "https://plane.example.com/my-ws/projects/proj-id/issues/42/"

def test_build_wi_url_trailing_slash():
    url = build_wi_url("https://plane.example.com/", "my-ws", "proj-id", 1)
    assert not url.startswith("https://plane.example.com//")

# build_wi_identifier 테스트
def test_build_wi_identifier():
    assert build_wi_identifier(5) == "OMK-5"
    assert build_wi_identifier(100) == "OMK-100"

# sanitize_comment 테스트
def test_sanitize_hex_string():
    text = "key: abcdef1234567890abcdef1234567890"  # 32자 hex
    result = sanitize_comment(text)
    assert "[REDACTED]" in result
    assert "abcdef1234567890abcdef1234567890" not in result

def test_sanitize_short_hex_not_redacted():
    text = "id: abc123def456"  # 14자, 짧으므로 그대로 유지
    result = sanitize_comment(text)
    assert "abc123def456" in result

def test_sanitize_normal_text():
    text = "일반적인 댓글 내용입니다."
    assert sanitize_comment(text) == text

# update_hud / reset_hud 테스트
def test_update_hud_no_tmux(capsys):
    with patch.dict("os.environ", {}, clear=False):
        # TMUX 없는 환경에서 에러 없이 동작
        if "TMUX" in __import__("os").environ:
            import os
            del os.environ["TMUX"]
        update_hud("OMK-1", "테스트", "In Progress")
    # stderr에 ANSI 이스케이프가 출력됨
    captured = capsys.readouterr()
    assert "OMK-1" in captured.err or len(captured.err) > 0

def test_reset_hud_no_error():
    # 에러 없이 동작하는지만 확인
    reset_hud()
