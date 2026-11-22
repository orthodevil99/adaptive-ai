"""Test environment. Set BEFORE any `app.*` import so a developer's real .env / key is never used."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_TMP = tempfile.mkdtemp(prefix="adaptive-ai-tests-")
os.environ.update(
    {
        "APP_ENV": "test",
        "PROVIDER": "mock",
        "GROQ_API_KEY": "",
        "APP_API_KEYS": "test-key",
        "DATABASE_URL": f"sqlite:///{_TMP}/test.db",
        "RATE_LIMIT_PER_MINUTE": "100000",
        "RESPOND_RATE_LIMIT_PER_MINUTE": "0",
        "SESSION_TTL_DAYS": "0",
        "LOG_LEVEL": "WARNING",
    }
)
