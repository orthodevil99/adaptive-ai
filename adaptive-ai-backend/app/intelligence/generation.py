"""Choose generation parameters (reasoning effort, token budget, temperature) from the analysis."""

_LENGTH_TOKENS = {"short": 600, "medium": 1500, "detailed": 3000}
_HEADROOM = {"low": 400, "medium": 1000, "high": 2000}  # gpt-oss reasoning tokens count against the budget
_PRECISE_TASKS = {"coding", "mathematics", "technical_troubleshooting"}


def plan_generation(
    analysis: dict, response_length: str | None, *, cap: int, preferences: dict | None = None
) -> dict:
    length = response_length or (preferences or {}).get("response_length") or "medium"
    task = analysis["task_type"]
    complexity = analysis["complexity"]
    strategy = analysis["selected_strategy"]

    if complexity == "high" or task == "mathematics":
        effort = "high"
    elif complexity == "low" and strategy == "DIRECT_ANSWER":
        effort = "low"
    elif analysis["selected_persona"] in {"concise", "creative"} and complexity != "medium":
        effort = "low"
    else:
        effort = "medium"

    if task in _PRECISE_TASKS:
        temperature = 0.2
    elif task == "creative_writing" or analysis["selected_persona"] == "creative":
        temperature = 0.9
    else:
        temperature = 0.5

    budget = _LENGTH_TOKENS.get(length, 1500)
    if complexity == "high":
        budget = int(budget * 1.5)
    max_tokens = min(cap, budget + _HEADROOM[effort])
    return {
        "reasoning_effort": effort,
        "max_tokens": max(256, max_tokens),
        "temperature": temperature,
        "max_tokens_ceiling": cap,
    }
