"""Secret redaction and lightweight prompt-injection signals (pure functions)."""

import re

_SECRET_PATTERNS = (
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{16,}"),
)

_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ignore_previous_instructions", re.compile(
        r"(?i)\bignore\b.{0,20}\b(previous|prior|above|earlier)\b.{0,20}\b(instructions?|prompts?|rules?)\b")),
    ("reveal_system_prompt", re.compile(
        r"(?i)\b(reveal|show|print|repeat|leak|output)\b.{0,40}\b(system|hidden|initial)\s+(prompt|instructions?|message)\b")),
    ("credential_request", re.compile(
        r"(?i)\b(reveal|show|print|give|tell|leak)\b.{0,30}\b(api[ _-]?keys?|secrets?|passwords?|credentials?)\b")),
    ("role_override", re.compile(r"(?i)\b(you are now|from now on you are|pretend to be)\b.{0,40}\b(unrestricted|unfiltered|dan)\b")),
    ("jailbreak_keyword", re.compile(r"(?i)\b(jailbreak|dan mode|developer mode)\b")),
)


def redact(text: str) -> str:
    """Replace anything that looks like an API key / bearer token."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda m: (m.group(1) if m.lastindex else "") + "[REDACTED]", text)
    return text


def contains_secret(text: str) -> bool:
    return redact(text) != text


def detect_injection(text: str) -> list[str]:
    """Return flag names for common injection phrasing. Informational only; never blocks."""
    return [name for name, pattern in _INJECTION_PATTERNS if pattern.search(text)]
