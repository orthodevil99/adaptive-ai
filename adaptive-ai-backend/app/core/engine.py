from app.core.classifier import classify_task
from app.core.clarification import clarification_check
from app.core.complexity import estimate_complexity
from app.core.persona_engine import choose_persona
from app.core.strategy_engine import candidate_strategies, choose_strategy
from app.utils.security import detect_injection


def analyze_request(
    message: str,
    preferred_persona: str | None = None,
    *,
    has_history: bool = False,
) -> dict:
    """Pure, provider-independent analysis. Strategy here is the rule-based default;
    `apply_selection` later swaps in the feedback-adapted one."""
    classification = classify_task(message)
    task = classification["task_type"]
    complexity = estimate_complexity(message)
    persona, persona_reason = choose_persona(task, preferred_persona)
    needs_clarification, question = clarification_check(message, task, has_history)
    strategy, strategy_reason = choose_strategy(task, complexity["complexity"], needs_clarification)
    return {
        **classification,
        **complexity,
        "selected_persona": persona,
        "persona_reason": persona_reason,
        "default_strategy": strategy,
        "selected_strategy": strategy,
        "strategy_reason": strategy_reason,
        "candidate_strategies": [] if needs_clarification else candidate_strategies(strategy),
        "adaptation": {"method": "not_applied"},
        "needs_clarification": needs_clarification,
        "clarification_question": question,
        "risk_flags": detect_injection(message),
    }


def apply_selection(analysis: dict, selection: dict) -> dict:
    """Record the adaptation decision on the analysis (mutates and returns it)."""
    analysis["adaptation"] = selection
    if selection["chosen"] != analysis["selected_strategy"]:
        analysis["selected_strategy"] = selection["chosen"]
        analysis["strategy_reason"] = selection["reason"]
    return analysis
