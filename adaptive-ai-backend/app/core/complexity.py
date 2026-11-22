import re

SIGNALS = {
    "architecture": 2, "comprehensive": 2, "integrate": 2, "migration": 2, "end-to-end": 2,
    "scalab": 2, "production": 1, "security": 1, "step by step": 1, "compare": 1, "multiple": 1,
    "debug": 1, "implement": 1, "evaluate": 1, "optimize": 1, "trade-off": 1, "refactor": 1,
}


def estimate_complexity(message: str) -> dict:
    text = message.casefold()
    words = len(text.split())
    score = 0
    signals: list[str] = []
    if words > 150:
        score += 3
        signals.append("very_long_request")
    elif words > 70:
        score += 2
        signals.append("long_request")
    elif words > 25:
        score += 1
        signals.append("moderate_length")
    for phrase, weight in SIGNALS.items():
        if phrase in text:
            score += weight
            signals.append(phrase.replace(" ", "_"))
    if len(re.findall(r"\b(and|then|also|additionally|plus)\b", text)) >= 2:
        score += 1
        signals.append("multiple_requirements")
    if len(re.findall(r"(?m)^\s*(\d+[.)]|[-*•])\s+\S", message)) >= 3:
        score += 1
        signals.append("enumerated_requirements")
    if text.count("?") >= 3:
        score += 1
        signals.append("multiple_questions")
    if "```" in message:
        score += 1
        signals.append("contains_code_block")
    level = "high" if score >= 5 else "medium" if score >= 2 else "low"
    return {"complexity": level, "complexity_score": score, "complexity_signals": signals}
