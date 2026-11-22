"""Weighted rule classifier: keyword weights plus structural signals (code, tracebacks, math)."""

import re

# category -> {term: weight}. Weight 2 = strong signal, 1 = normal, 0.5 = weak.
RULES: dict[str, dict[str, float]] = {
    "coding": {
        "python": 1, "javascript": 1, "typescript": 1, "java": 1, "c++": 1, "rust": 1, "golang": 1,
        "code": 1, "function": 1, "class": 0.5, "api": 1, "backend": 1, "frontend": 1,
        "database": 1, "sql": 1, "compile": 1, "refactor": 1.5, "script": 1, "fastapi": 1,
        "program": 1, "algorithm": 1, "regex": 1, "endpoint": 1, "unit test": 1.5, "implement": 1,
    },
    "technical_troubleshooting": {
        "not working": 2, "doesn't work": 2, "does not work": 2, "crash": 1.5, "crashes": 1.5,
        "exception": 1.5, "traceback": 2, "stack trace": 2, "install error": 2, "bug": 1,
        "debug": 1.5, "error": 1, "fails": 1, "failing": 1, "broken": 1, "fix": 1,
    },
    "education": {
        "explain": 1, "teach": 1.5, "homework": 1.5, "learn": 1, "study": 1, "concept": 1,
        "what is": 1, "what are": 1, "how does": 1, "how do": 0.5, "lesson": 1.5, "tutorial": 1.5,
        "eli5": 2, "understand": 1, "why does": 1,
    },
    "writing": {
        "write": 1, "draft": 1.5, "email": 1.5, "rewrite": 1.5, "essay": 1.5, "paragraph": 1,
        "proofread": 2, "cover letter": 2, "blog post": 1.5, "tone": 0.5, "edit": 0.5, "reply": 0.5,
    },
    "planning": {
        "plan": 1.5, "schedule": 1.5, "roadmap": 2, "organize": 1, "routine": 1, "timeline": 1.5,
        "milestone": 1.5, "checklist": 1, "itinerary": 1.5, "strategy": 1, "prioritize": 1,
    },
    "research": {
        "research": 2, "sources": 1.5, "evidence": 1.5, "latest": 1, "investigate": 1.5,
        "literature": 1.5, "studies": 1, "state of the art": 2, "survey": 1,
    },
    "summarization": {
        "summarize": 2, "summarise": 2, "summary": 2, "tl;dr": 2, "key points": 2,
        "recap": 1.5, "condense": 1.5, "main ideas": 1.5,
    },
    "analysis": {
        "analyze": 1.5, "analyse": 1.5, "analysis": 1.5, "compare": 1.5, "evaluate": 1.5,
        "pros and cons": 2, "trade-off": 1.5, "tradeoff": 1.5, "versus": 1, "vs": 1,
        "which is better": 2, "should i": 0.5, "critique": 1.5, "review": 1,
    },
    "creative_writing": {
        "story": 1.5, "poem": 2, "fiction": 1.5, "character": 1, "creative": 1.5, "lyrics": 1.5,
        "screenplay": 2, "worldbuilding": 2, "haiku": 2, "plot": 1,
    },
    "mathematics": {
        "calculate": 1.5, "equation": 1.5, "solve": 1.5, "integral": 2, "derivative": 2,
        "probability": 1.5, "matrix": 1.5, "theorem": 1.5, "proof": 1, "algebra": 1.5,
        "geometry": 1.5, "statistics": 1,
    },
}

_COMPILED: dict[str, list[tuple[re.Pattern[str], float]]] = {
    category: [
        (re.compile(rf"(?<![\w]){re.escape(term)}(?![\w])"), weight) for term, weight in terms.items()
    ]
    for category, terms in RULES.items()
}

# Structural signals: (category, pattern, weight)
_STRUCTURAL: tuple[tuple[str, re.Pattern[str], float], ...] = (
    ("coding", re.compile(r"```"), 2.0),
    ("coding", re.compile(r"(?m)^\s*(def|class|import|from|function|const|let|var|public|private)\s+\w+"), 1.5),
    ("coding", re.compile(r"[\w\])]\.\w+\(.*\)|=>|;\s*$"), 0.5),
    ("technical_troubleshooting", re.compile(r"(?i)traceback \(most recent call last\)|\b\w+(Error|Exception)\b"), 2.0),
    ("mathematics", re.compile(r"\d\s*[\+\-\*/\^=]\s*\d|\b\d+\s*%\s*of\b|\bx\^?\d\b"), 1.5),
)

_MULTI_MIN_SCORE = 2.0
_MULTI_RATIO = 0.75


def score_categories(message: str) -> dict[str, float]:
    text = re.sub(r"[ \t]+", " ", message.casefold())
    scores: dict[str, float] = {}
    for category, patterns in _COMPILED.items():
        total = sum(weight for pattern, weight in patterns if pattern.search(text))
        scores[category] = total
    for category, pattern, weight in _STRUCTURAL:
        # Run structure checks on the original text (case matters for identifiers).
        if pattern.search(message):
            scores[category] = scores.get(category, 0.0) + weight
    return scores


def classify_task(message: str) -> dict:
    scores = score_categories(message)
    ranked = sorted(
        ((category, score) for category, score in scores.items() if score > 0),
        key=lambda item: (-item[1], item[0]),
    )
    if not ranked:
        return {
            "task_type": "general_assistance", "primary_intent": "general_assistance",
            "secondary_intents": [], "confidence": 0.5, "classification_method": "weighted_rules",
            "intent_scores": {},
        }
    primary, top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    secondary = [category for category, score in ranked[1:] if score >= 0.4 * top]
    # multi_intent only when two categories are both strong and close to each other.
    is_multi = len(ranked) > 1 and second >= _MULTI_MIN_SCORE and second >= _MULTI_RATIO * top
    margin = (top - second) / top if top else 0.0
    confidence = min(0.95, 0.5 + 0.08 * min(top, 4.0) + 0.15 * margin)
    if is_multi:
        confidence = min(confidence, 0.7)
    return {
        "task_type": "multi_intent" if is_multi else primary,
        "primary_intent": primary,
        "secondary_intents": secondary,
        "confidence": round(confidence, 2),
        "classification_method": "weighted_rules",
        "intent_scores": {category: round(score, 2) for category, score in ranked[:4]},
    }
