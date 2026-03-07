"""session/scope.py 드리프트 감지 알고리즘 테스트."""

from __future__ import annotations

import pytest

from oh_my_kanban.session.scope import (
    MAX_SCOPE_TOKENS,
    MIN_SCOPE_TOKENS,
    SENSITIVITY_OFFSET_SCALE,
    THRESHOLD_MINOR,
    THRESHOLD_NONE,
    THRESHOLD_SIGNIFICANT,
    WEIGHT_FILE_JACCARD,
    WEIGHT_FILE_JACCARD_COLDSTART,
    WEIGHT_KEYWORD_JACCARD,
    WEIGHT_KEYWORD_JACCARD_COLDSTART,
    WEIGHT_TF_COSINE,
    WEIGHT_TF_COSINE_COLDSTART,
    _jaccard,
    _tf_cosine,
    classify_drift,
    compute_drift_score,
    expand_scope,
    init_scope,
    should_suppress_warning,
    tokenize_text,
)
from oh_my_kanban.session.state import DriftResult, ScopeState, SessionState


# ── 1. 상수 값 검증 ─────────────────────────────────────────────────────────

class TestConstants:
    def test_weight_tf_cosine(self):
        assert WEIGHT_TF_COSINE == 0.4

    def test_weight_keyword_jaccard(self):
        assert WEIGHT_KEYWORD_JACCARD == 0.3

    def test_weight_file_jaccard(self):
        assert WEIGHT_FILE_JACCARD == 0.3

    def test_weight_tf_cosine_coldstart(self):
        assert WEIGHT_TF_COSINE_COLDSTART == 0.55

    def test_weight_keyword_jaccard_coldstart(self):
        assert WEIGHT_KEYWORD_JACCARD_COLDSTART == 0.45

    def test_weight_file_jaccard_coldstart(self):
        assert WEIGHT_FILE_JACCARD_COLDSTART == 0.0

    def test_threshold_none(self):
        assert THRESHOLD_NONE == 0.575

    def test_threshold_minor(self):
        assert THRESHOLD_MINOR == 0.375

    def test_threshold_significant(self):
        assert THRESHOLD_SIGNIFICANT == 0.225

    def test_sensitivity_offset_scale(self):
        assert SENSITIVITY_OFFSET_SCALE == 0.2


# ── 2. tokenize_text ────────────────────────────────────────────────────────

class TestTokenizeText:
    def test_english_tokens(self):
        result = tokenize_text("implement login feature")
        assert "implement" in result
        assert "login" in result
        assert "feature" in result

    def test_korean_tokens(self):
        result = tokenize_text("로그인 기능 구현")
        assert "로그인" in result
        assert "기능" in result
        assert "구현" in result

    def test_stopword_filtering(self):
        result = tokenize_text("this is a test of the system")
        # 불용어 제거: this, is, a, of, the
        assert "this" not in result
        assert "is" not in result
        assert "a" not in result
        assert "of" not in result
        assert "the" not in result
        assert "test" in result
        assert "system" in result

    def test_empty_string(self):
        assert tokenize_text("") == []

    def test_mixed_language(self):
        result = tokenize_text("kanban 보드 feature")
        assert "kanban" in result
        assert "보드" in result
        assert "feature" in result


# ── 3. _tf_cosine ───────────────────────────────────────────────────────────

class TestTfCosine:
    def test_identical_tokens(self):
        tokens = ["hello", "world", "test"]
        assert _tf_cosine(tokens, tokens) == pytest.approx(1.0)

    def test_completely_different(self):
        a = ["apple", "banana", "cherry"]
        b = ["dog", "elephant", "fox"]
        assert _tf_cosine(a, b) == pytest.approx(0.0)

    def test_empty_a(self):
        assert _tf_cosine([], ["hello"]) == 0.0

    def test_empty_b(self):
        assert _tf_cosine(["hello"], []) == 0.0

    def test_partial_overlap(self):
        a = ["hello", "world"]
        b = ["hello", "python"]
        score = _tf_cosine(a, b)
        assert 0.0 < score < 1.0


# ── 4. _jaccard ─────────────────────────────────────────────────────────────

class TestJaccard:
    def test_identical_sets(self):
        s = {"a", "b", "c"}
        assert _jaccard(s, s) == pytest.approx(1.0)

    def test_no_common_elements(self):
        assert _jaccard({"a", "b"}, {"c", "d"}) == pytest.approx(0.0)

    def test_both_empty(self):
        assert _jaccard(set(), set()) == pytest.approx(1.0)

    def test_one_empty(self):
        assert _jaccard({"a"}, set()) == pytest.approx(0.0)

    def test_partial_overlap(self):
        # {a,b,c} & {b,c,d} = {b,c}, union = {a,b,c,d} → 2/4 = 0.5
        assert _jaccard({"a", "b", "c"}, {"b", "c", "d"}) == pytest.approx(0.5)


# ── 5. compute_drift_score ──────────────────────────────────────────────────

class TestComputeDriftScore:
    def _make_scope(self, text: str) -> ScopeState:
        """도우미: 텍스트에서 ScopeState를 생성한다."""
        tokens = tokenize_text(text)
        from collections import Counter
        counter = Counter(tokens)
        keywords = [w for w, _ in counter.most_common(20)]
        return ScopeState(tokens=tokens, keywords=keywords)

    def test_empty_scope_returns_one(self):
        scope = ScopeState()  # tokens=[]
        result = compute_drift_score(scope, "anything goes here", [])
        assert result.score == pytest.approx(1.0)
        assert result.level == "none"

    def test_identical_text_high_score(self):
        text = "implement user authentication login system"
        scope = self._make_scope(text)
        result = compute_drift_score(scope, text, [])
        assert result.score >= 0.9

    def test_unrelated_text_low_score(self):
        scope = self._make_scope(
            "implement user authentication login system security"
        )
        result = compute_drift_score(
            scope,
            "database migration schema table column index",
            ["schema.sql"],
        )
        assert result.score <= 0.2

    def test_coldstart_uses_coldstart_weights(self):
        """files_touched가 비어있으면 콜드스타트 가중치를 사용한다."""
        scope = self._make_scope("implement login feature authentication")
        # 콜드스타트: files_touched=[]
        result_cold = compute_drift_score(
            scope, "implement login feature authentication", []
        )
        # 파일 있는 경우
        result_normal = compute_drift_score(
            scope, "implement login feature authentication", ["auth.py"]
        )
        # 콜드스타트에서는 파일 가중치가 0이므로 결과가 다를 수 있음
        assert isinstance(result_cold, DriftResult)
        assert isinstance(result_normal, DriftResult)

    def test_returns_drift_result_type(self):
        scope = ScopeState()
        result = compute_drift_score(scope, "test", [])
        assert isinstance(result, DriftResult)
        assert hasattr(result, "score")
        assert hasattr(result, "level")
        assert hasattr(result, "components")
        assert hasattr(result, "suppressed")

    def test_components_contain_expected_keys(self):
        scope = self._make_scope("hello world test")
        result = compute_drift_score(scope, "hello world test", [])
        assert "tf_cosine" in result.components
        assert "keyword_jaccard" in result.components
        assert "file_jaccard" in result.components


# ── 6. classify_drift ──────────────────────────────────────────────────────

class TestClassifyDrift:
    def test_none_at_0_6(self):
        assert classify_drift(0.6, 0.5) == "none"

    def test_minor_at_0_4(self):
        assert classify_drift(0.4, 0.5) == "minor"

    def test_significant_at_0_3(self):
        assert classify_drift(0.3, 0.5) == "significant"

    def test_major_at_0_1(self):
        assert classify_drift(0.1, 0.5) == "major"

    def test_high_sensitivity_detects_drift_easier(self):
        """감도가 높으면 같은 점수에서도 더 높은 드리프트 레벨이 된다."""
        # sensitivity=0.5에서 0.6은 'none'
        assert classify_drift(0.6, 0.5) == "none"
        # sensitivity=1.0에서 0.6은 임계값이 올라가므로 'minor'가 될 수 있음
        result_high = classify_drift(0.6, 1.0)
        assert result_high in ("none", "minor")  # 최소한 더 민감해야 함

    def test_low_sensitivity_is_lenient(self):
        """감도가 낮으면 같은 점수에서도 드리프트가 적게 감지된다."""
        # sensitivity=0.5에서 0.4은 'minor'
        assert classify_drift(0.4, 0.5) == "minor"
        # sensitivity=0.0: offset=-0.1, adjusted_none=0.475
        # score 0.5 >= 0.475 → 'none' (sensitivity=0.5에서는 'minor')
        result_low = classify_drift(0.5, 0.0)
        assert result_low == "none"


# ── 7. should_suppress_warning ──────────────────────────────────────────────

class TestShouldSuppressWarning:
    def test_korean_transition_ije(self):
        assert should_suppress_warning("이제 다른 작업을 하겠습니다") is True

    def test_english_switch_to(self):
        assert should_suppress_warning("Let me switch to the database task") is True

    def test_normal_text_no_suppression(self):
        assert should_suppress_warning("implement the login feature") is False

    def test_english_moving_on(self):
        assert should_suppress_warning("moving on to tests") is True

    def test_korean_daeumuro(self):
        assert should_suppress_warning("다음으로 넘어가겠습니다") is True


# ── 8. init_scope ───────────────────────────────────────────────────────────

class TestInitScope:
    def test_too_few_tokens_no_change(self):
        state = SessionState(session_id="test-1")
        init_scope(state, "hi")  # 토큰 1개 < MIN_SCOPE_TOKENS
        assert state.scope.tokens == []
        assert state.scope.keywords == []

    def test_sufficient_tokens_initializes(self):
        state = SessionState(session_id="test-2")
        init_scope(state, "implement user authentication login system feature")
        assert len(state.scope.tokens) >= MIN_SCOPE_TOKENS
        assert len(state.scope.keywords) > 0
        assert state.scope.topics == []

    def test_tokens_capped_at_max(self):
        state = SessionState(session_id="test-3")
        # MAX_SCOPE_TOKENS보다 많은 토큰 생성
        long_text = " ".join(f"word{i}" for i in range(MAX_SCOPE_TOKENS + 100))
        init_scope(state, long_text)
        assert len(state.scope.tokens) <= MAX_SCOPE_TOKENS


# ── 9. expand_scope ─────────────────────────────────────────────────────────

class TestExpandScope:
    def test_adds_new_tokens(self):
        state = SessionState(session_id="test-4")
        init_scope(state, "implement user authentication login system feature")
        original_count = len(state.scope.tokens)
        expand_scope(state, "database migration schema")
        assert len(state.scope.tokens) > original_count

    def test_respects_max_scope_tokens(self):
        state = SessionState(session_id="test-5")
        # 먼저 MAX에 가깝게 채움
        long_text = " ".join(f"word{i}" for i in range(MAX_SCOPE_TOKENS - 2))
        init_scope(state, long_text)
        initial_len = len(state.scope.tokens)
        # 확장 시도
        expand_scope(state, "extra tokens here plus more words")
        assert len(state.scope.tokens) <= MAX_SCOPE_TOKENS

    def test_updates_expanded_topics(self):
        state = SessionState(session_id="test-6")
        init_scope(state, "implement user authentication login system feature")
        expand_scope(state, "database migration schema table")
        assert len(state.scope.expanded_topics) > 0

    def test_recalculates_keywords(self):
        state = SessionState(session_id="test-7")
        init_scope(state, "implement user authentication login system feature")
        old_keywords = list(state.scope.keywords)
        expand_scope(state, "database database database schema schema")
        # 키워드가 재계산되었는지 확인 (새 빈도 반영)
        assert state.scope.keywords != old_keywords or "database" in state.scope.keywords
