def clarification_check(message: str, task: str, has_history: bool = False) -> tuple[bool, str | None]:
    """Ask for detail only on very short, context-free requests.

    Inside an ongoing conversation short follow-ups ("make it shorter") are fine.
    """
    if has_history:
        return False, None
    words = len(message.split())
    if task == "planning" and words <= 5:
        return True, "What is the goal of the plan, and what deadline should it fit?"
    if task == "writing" and words <= 3:
        return True, "What would you like written, and who is the intended audience?"
    if task == "general_assistance" and words <= 2:
        return True, "Could you add a little more detail about what you need?"
    return False, None
