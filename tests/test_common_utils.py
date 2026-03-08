"""common.py 공유 유틸리티 유닛 테스트."""

import random
import string

from oh_my_kanban.hooks.common import sanitize_comment


def _random_alnum(n: int) -> str:
    """테스트용 랜덤 영숫자 문자열을 생성한다."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


# sanitize_comment 테스트

def test_sanitize_plane_api_key():
    fake_key = "plane_api_" + _random_alnum(32).lower()[:32]
    # plane_api_ 패턴은 hex만 매칭하므로 hex로 생성
    fake_key = "plane_api_" + "".join(random.choices("0123456789abcdef", k=32))
    text = f"key: {fake_key}"
    result = sanitize_comment(text)
    assert "[PLANE_API_KEY]" in result
    assert fake_key not in result


def test_sanitize_github_pat():
    fake_pat = "ghp_" + _random_alnum(36)
    text = f"token: {fake_pat}"
    result = sanitize_comment(text)
    assert "[GITHUB_PAT]" in result
    assert fake_pat not in result


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
    fake_key = "plane_api_" + "".join(random.choices("0123456789abcdef", k=32))
    text = f"{fake_key} and password=secret"
    result = sanitize_comment(text)
    assert "[PLANE_API_KEY]" in result
    assert "[PASSWORD_REDACTED]" in result


def test_sanitize_empty_string():
    assert sanitize_comment("") == ""
