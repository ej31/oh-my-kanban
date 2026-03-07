"""드리프트 감지 알고리즘 — 세션 범위 이탈 측정."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from oh_my_kanban.session.state import DriftResult, SessionState, ScopeState

# ── 가중치 상수 (일반 모드) ──────────────────────────────────────────────────
WEIGHT_TF_COSINE = 0.4
WEIGHT_KEYWORD_JACCARD = 0.3
WEIGHT_FILE_JACCARD = 0.3

# ── 가중치 상수 (콜드스타트 모드: files_touched 비어있을 때) ─────────────────
WEIGHT_TF_COSINE_COLDSTART = 0.55
WEIGHT_KEYWORD_JACCARD_COLDSTART = 0.45
WEIGHT_FILE_JACCARD_COLDSTART = 0.0

# ── 드리프트 레벨 임계값 (sensitivity=0.5 기준) ─────────────────────────────
THRESHOLD_NONE = 0.575
THRESHOLD_MINOR = 0.375
THRESHOLD_SIGNIFICANT = 0.225
# score < 0.225 → major

SENSITIVITY_OFFSET_SCALE = 0.2  # sensitivity 1단위당 임계값 이동

# ── 스코프 토큰 제한 ────────────────────────────────────────────────────────
MIN_SCOPE_TOKENS = 3
MAX_SCOPE_TOKENS = 500

# ── 토큰화 ──────────────────────────────────────────────────────────────────
_TOKEN_PATTERN = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*|[가-힣]+")

_STOPWORDS = frozenset({
    "is", "a", "the", "of", "in", "to", "for", "with", "and", "or",
    "be", "it", "this", "that", "an", "as", "at", "by", "on", "not",
    "are", "was", "were", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "can",
    "may", "might", "shall", "if", "but", "so", "no", "from",
})

# ── 전환 패턴 (should_suppress_warning) ─────────────────────────────────────
_TRANSITION_PATTERNS_KO = ["이제", "다음으로", "다음은", "이제부터", "그 다음"]
_TRANSITION_PATTERNS_EN = [
    "switch to", "now let", "let's move", "moving on", "next up", "next task",
]


def tokenize_text(text: str) -> list[str]:
    """텍스트를 토큰 리스트로 분리한다. 불용어를 제거한다."""
    raw = _TOKEN_PATTERN.findall(text)
    return [t.lower() for t in raw if t.lower() not in _STOPWORDS]


# ── 내부 유사도 함수 ────────────────────────────────────────────────────────

def _tf_cosine(a_tokens: list[str], b_tokens: list[str]) -> float:
    """TF 기반 코사인 유사도를 계산한다."""
    if not a_tokens or not b_tokens:
        return 0.0
    a_tf = Counter(a_tokens)
    b_tf = Counter(b_tokens)
    dot = sum(a_tf[t] * b_tf[t] for t in a_tf if t in b_tf)
    norm_a = math.sqrt(sum(v * v for v in a_tf.values()))
    norm_b = math.sqrt(sum(v * v for v in b_tf.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _jaccard(a: set, b: set) -> float:
    """Jaccard 유사도를 계산한다."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ── 드리프트 분류 ───────────────────────────────────────────────────────────

def classify_drift(score: float, sensitivity: float) -> str:
    """점수와 감도를 기반으로 드리프트 레벨을 분류한다."""
    offset = (sensitivity - 0.5) * SENSITIVITY_OFFSET_SCALE
    adjusted_none = THRESHOLD_NONE + offset
    adjusted_minor = THRESHOLD_MINOR + offset
    adjusted_significant = THRESHOLD_SIGNIFICANT + offset

    if score >= adjusted_none:
        return "none"
    if score >= adjusted_minor:
        return "minor"
    if score >= adjusted_significant:
        return "significant"
    return "major"


# ── 드리프트 점수 계산 ─────────────────────────────────────────────────────

def compute_drift_score(
    scope: "ScopeState",
    prompt_text: str,
    files_touched: list[str],
    sensitivity: float = 0.5,
) -> "DriftResult":
    """현재 스코프 대비 프롬프트의 드리프트 점수를 계산한다.

    sensitivity는 세션 설정값(state.config.sensitivity)을 전달해야 한다.
    """
    from oh_my_kanban.session.state import DriftResult

    # 스코프가 비어있으면 비교 불가 — 이탈 없음으로 처리
    if not scope.tokens:
        return DriftResult(
            score=1.0,
            level="none",
            components={"tf_cosine": 1.0, "keyword_jaccard": 1.0, "file_jaccard": 1.0},
            suppressed=False,
        )

    prompt_tokens = tokenize_text(prompt_text)
    prompt_keywords = set(_top_keywords(prompt_tokens, 20))

    tf_cos = _tf_cosine(scope.tokens, prompt_tokens)
    kw_jac = _jaccard(set(scope.keywords), prompt_keywords)
    file_jac = _jaccard(set(scope.file_refs), set(files_touched))

    coldstart = len(files_touched) == 0
    if coldstart:
        w1 = WEIGHT_TF_COSINE_COLDSTART
        w2 = WEIGHT_KEYWORD_JACCARD_COLDSTART
        w3 = WEIGHT_FILE_JACCARD_COLDSTART
    else:
        w1 = WEIGHT_TF_COSINE
        w2 = WEIGHT_KEYWORD_JACCARD
        w3 = WEIGHT_FILE_JACCARD

    score = w1 * tf_cos + w2 * kw_jac + w3 * file_jac

    # 동일 텍스트 허용 오차 — 거의 같으면 1.0 처리
    if score >= 0.9:
        score = 1.0

    # 세션 sensitivity를 적용하여 드리프트 레벨 결정
    level = classify_drift(score, sensitivity)

    return DriftResult(
        score=score,
        level=level,
        components={
            "tf_cosine": tf_cos,
            "keyword_jaccard": kw_jac,
            "file_jaccard": file_jac,
        },
        suppressed=False,
    )


# ── 전환 패턴 감지 ─────────────────────────────────────────────────────────

def should_suppress_warning(prompt_text: str) -> bool:
    """프롬프트에 명시적 전환 패턴이 있으면 True를 반환한다."""
    lower = prompt_text.lower()
    for pattern in _TRANSITION_PATTERNS_EN:
        if pattern in lower:
            return True
    # 한국어 패턴은 원본 텍스트에서 검색 (대소문자 구분 없음)
    for pattern in _TRANSITION_PATTERNS_KO:
        if pattern in prompt_text:
            return True
    return False


# ── 스코프 초기화/확장 ─────────────────────────────────────────────────────

def _top_keywords(tokens: list[str], n: int) -> list[str]:
    """빈도 상위 n개 키워드를 반환한다."""
    if not tokens:
        return []
    counter = Counter(tokens)
    return [word for word, _ in counter.most_common(n)]


def init_scope(state: "SessionState", prompt_text: str) -> None:
    """첫 프롬프트로 세션 스코프를 초기화한다."""
    tokens = tokenize_text(prompt_text)
    if len(tokens) < MIN_SCOPE_TOKENS:
        return  # 토큰 부족 — 보류
    state.scope.tokens = tokens[:MAX_SCOPE_TOKENS]
    state.scope.keywords = _top_keywords(tokens, 20)
    state.scope.topics = []
    state.scope.expanded_topics = []


def expand_scope(state: "SessionState", prompt_text: str) -> None:
    """기존 스코프에 새 프롬프트 토큰을 추가한다."""
    new_tokens = tokenize_text(prompt_text)
    remaining = MAX_SCOPE_TOKENS - len(state.scope.tokens)
    if remaining > 0:
        state.scope.tokens.extend(new_tokens[:remaining])

    # 새 토픽 추가
    new_keywords = _top_keywords(new_tokens, 10)
    for kw in new_keywords:
        if kw not in state.scope.expanded_topics:
            state.scope.expanded_topics.append(kw)

    # 키워드 재계산
    state.scope.keywords = _top_keywords(state.scope.tokens, 20)
