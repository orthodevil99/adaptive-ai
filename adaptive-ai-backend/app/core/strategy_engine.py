BASE_STRATEGIES = {
    "analysis": "DEEP_ANALYSIS", "planning": "STRUCTURED_PLAN", "education": "STEP_BY_STEP",
    "mathematics": "STEP_BY_STEP", "research": "RESEARCH_SUMMARY",
    "summarization": "DIRECT_ANSWER", "writing": "EXAMPLE_BASED",
    "creative_writing": "EXAMPLE_BASED", "coding": "STEP_BY_STEP",
    "technical_troubleshooting": "STEP_BY_STEP", "general_assistance": "DIRECT_ANSWER",
    "multi_intent": "STRUCTURED_PLAN",
}

# Arms the adaptation layer may choose between (first = the rule-based default).
CANDIDATES: dict[str, tuple[str, ...]] = {
    "DIRECT_ANSWER": ("DIRECT_ANSWER", "STEP_BY_STEP", "EXAMPLE_BASED"),
    "STEP_BY_STEP": ("STEP_BY_STEP", "EXAMPLE_BASED", "DIRECT_ANSWER"),
    "DEEP_ANALYSIS": ("DEEP_ANALYSIS", "STRUCTURED_PLAN", "STEP_BY_STEP"),
    "EXAMPLE_BASED": ("EXAMPLE_BASED", "STEP_BY_STEP", "DIRECT_ANSWER"),
    "RESEARCH_SUMMARY": ("RESEARCH_SUMMARY", "DEEP_ANALYSIS", "DIRECT_ANSWER"),
    "STRUCTURED_PLAN": ("STRUCTURED_PLAN", "STEP_BY_STEP", "DEEP_ANALYSIS"),
}


def choose_strategy(task: str, complexity: str, needs_clarification: bool = False) -> tuple[str, str]:
    if needs_clarification:
        return "CLARIFICATION_FIRST", "Essential information is missing."
    if complexity == "high" and task not in {"writing", "creative_writing"}:
        return "DEEP_ANALYSIS", "The request has multiple or technically demanding requirements."
    strategy = BASE_STRATEGIES.get(task, "DIRECT_ANSWER")
    if complexity == "medium" and strategy == "DIRECT_ANSWER":
        strategy = "STEP_BY_STEP"
    return strategy, "Selected from task type and estimated complexity."


def candidate_strategies(strategy: str) -> list[str]:
    return list(CANDIDATES.get(strategy, (strategy,)))
