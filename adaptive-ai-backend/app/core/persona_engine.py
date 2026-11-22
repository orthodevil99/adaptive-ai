DEFAULTS = {
    "coding": "technical", "technical_troubleshooting": "technical", "education": "educational",
    "writing": "professional", "creative_writing": "creative", "planning": "planner",
    "research": "researcher", "analysis": "analyst", "mathematics": "educational",
    "summarization": "concise", "general_assistance": "balanced", "multi_intent": "balanced",
}
VALID_PERSONAS = {
    "balanced", "educational", "technical", "concise", "creative", "professional",
    "researcher", "planner", "analyst",
}


def choose_persona(task: str, preferred: str | None = None) -> tuple[str, str]:
    if preferred and preferred in VALID_PERSONAS:
        return preferred, "Selected from the user's saved or explicit preference."
    persona = DEFAULTS.get(task, "balanced")
    return persona, f"Selected the {persona} persona based on the detected task."
