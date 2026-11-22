"""End-to-end check against a RUNNING server: python scripts/smoke_test.py [base_url]

Reads APP_API_KEYS' first key from the environment variable SMOKE_API_KEY (if the server uses auth).
Needs no third-party packages. It verifies that your Groq key + model actually work.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
KEY = os.environ.get("SMOKE_API_KEY", "")


def call(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if KEY:
        request.add_header("X-API-Key", KEY)
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"null")


def step(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    if not ok:
        sys.exit(1)


status, health = call("GET", "/health")
step("health", status == 200, f"provider={health.get('provider')} configured={health.get('provider_configured')}")

status, probe = call("GET", "/health/model?probe=true")
info = (probe or {}).get("probe", {})
step("Groq key + model reachable", status == 200 and info.get("reachable") is True, json.dumps(info))
step("primary model available", info.get("model_available") is True, f"({probe.get('model')})")

status, data = call("POST", "/api/v1/assistant/respond",
                    {"message": "Explain what a REST API is in three sentences.", "user_id": "smoke-test"})
step("respond", status == 200 and data.get("status") == "completed", f"HTTP {status}")
print("   model:", data["meta"]["model"], "| latency ms:", data["meta"]["latency_ms"],
      "| tokens:", data["meta"]["prompt_tokens"], "+", data["meta"]["completion_tokens"])
print("   answer:", data["answer"][:300].replace("\n", " "))

status, fb = call("POST", "/api/v1/assistant/feedback", {"interaction_id": data["interaction_id"], "rating": 5})
step("feedback", status == 200)
status, _ = call("DELETE", "/api/v1/users/smoke-test")
step("cleanup", status == 200)
print("All checks passed.")
