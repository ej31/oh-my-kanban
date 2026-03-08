"""common.py 공유 유틸리티 유닛 테스트."""

from oh_my_kanban.hooks.common import sanitize_comment


# sanitize_comment 테스트

def test_sanitize_plane_api_key():
    text = "key: plane_api_081e8676160f42db9e17eef2eb12c0b2"
    result = sanitize_comment(text)
    assert "[PLANE_API_KEY]" in result
    assert "plane_api_081e8676160f42db9e17eef2eb12c0b2" not in result


def test_sanitize_github_pat():
    # 더미 PAT (36자 영숫자) — 실제 토큰이 아님
    fake_pat = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
    text = f"token: {fake_pat}"
    result = sanitize_comment(text)
    assert "[GITHUB_PAT]" in result
    assert "ghp_" not in result


def test_sanitize_bearer_token():
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"
    result = sanitize_comment(text)
    assert "Bearer [REDACTED]" in result
    assert "eyJhbGci" not in result


def test_sanitize_password():
    text = "password: mysecretpass123"
    result = sanitize_comment(text)
    assert "[PASSWORD_REDACTED]" in result
    assert "mysecretpass123" not in result


def test_sanitize_normal_text_unchanged():
    text = "일반적인 댓글 내용입니다."
    assert sanitize_comment(text) == text


def test_sanitize_multiple_patterns():
    text = "plane_api_081e8676160f42db9e17eef2eb12c0b2 and password=secret"
    result = sanitize_comment(text)
    assert "[PLANE_API_KEY]" in result
    assert "[PASSWORD_REDACTED]" in result


def test_sanitize_empty_string():
    assert sanitize_comment("") == ""
