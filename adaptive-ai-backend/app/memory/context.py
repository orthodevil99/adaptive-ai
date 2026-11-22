def trim_context(messages: list[dict[str, str]], max_messages: int, max_chars: int) -> list[dict[str, str]]:
    """Keep the newest messages that fit both a count and a character budget.

    The newest message is always kept (truncated if needed). Output is chronological and
    never starts with an assistant turn.
    """
    if max_messages <= 0 or max_chars <= 0 or not messages:
        return []
    selected: list[dict[str, str]] = []
    used = 0
    for message in reversed(messages[-max_messages:]):
        content = message["content"]
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(content) > remaining:
            if selected:
                break
            content = content[:remaining] + " …[truncated]"
        selected.append({"role": message["role"], "content": content})
        used += len(content)
    selected.reverse()
    while selected and selected[0]["role"] != "user":
        selected.pop(0)
    return selected
