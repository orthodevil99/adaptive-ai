"""Heuristic response checks. These verify form, not factual correctness."""

import re

from app.utils.security import contains_secret

_LIST_RE = re.compile(r"(?m)^\s*(\d+[.)]|[-*•])\s+\S")
_NUMBERED_RE = re.compile(r"(?m)^\s*\d+[.)]\s+\S")
_HEADING_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s+\S|\*\*[^*\n]+\*\*\s*:?\s*$")
_CODE_REQUEST_RE = re.compile(r"(?i)\b(write|implement|create|build|give me|show me)\b.{0,40}\b(code|function|script|class|endpoint|query)\b")


def evaluate_response(
    answer: str,
    strategy: str,
    *,
    finish_reason: str | None = None,
    task_type: str | None = None,
    user_message: str = "",
) -> dict:
    text = answer.strip() if isinstance(answer, str) else ""
    words = len(text.split())
    checks = {
        "has_answer": bool(text),
        "length_valid": words >= 3,
        "not_truncated": finish_reason != "length",
        "no_secret_leak": not contains_secret(text),
    }
    warnings: list[str] = []
    if checks["has_answer"] and words < 8:
        warnings.append("Response is short; check whether it fully addresses the request.")
    if not checks["not_truncated"]:
        warnings.append("Output hit the token limit and may be cut off; ask to continue or raise the length.")
    if not checks["no_secret_leak"]:
        warnings.append("Response contained something resembling a credential; it was redacted.")

    if checks["has_answer"] and words >= 8:
        if strategy == "STEP_BY_STEP" and not _NUMBERED_RE.search(text) and words > 60:
            warnings.append("Expected numbered steps for the step-by-step strategy.")
        elif strategy == "STRUCTURED_PLAN" and not (_LIST_RE.search(text) or _HEADING_RE.search(text)):
            warnings.append("Expected a list or headings for the structured-plan strategy.")
        elif strategy == "DEEP_ANALYSIS" and words < 80:
            warnings.append("Analysis is brief for the deep-analysis strategy.")
        if task_type in {"coding", "technical_troubleshooting"} and _CODE_REQUEST_RE.search(user_message) \
                and "```" not in text:
            warnings.append("Code was requested but no fenced code block was returned.")

    hard_fail = not checks["has_answer"]
    soft_fail = not (checks["length_valid"] and checks["not_truncated"])
    if hard_fail:
        status = "failed"
    elif soft_fail:
        status = "review_required"
    elif warnings:
        status = "passed_with_warnings"
    else:
        status = "passed"
    quality = max(0.0, 1.0 - 0.15 * len(warnings) - (0.3 if soft_fail else 0.0) - (1.0 if hard_fail else 0.0))
    return {
        **checks,
        "word_count": words,
        "strategy": strategy,
        "evaluation_status": status,
        "quality_score": round(quality, 2),
        "warnings": warnings,
        "scope": "Structural checks only; factual correctness is not established.",
    }
