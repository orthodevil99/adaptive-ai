"""API integration tests using the mock provider (no Groq key or network needed).

Requires the full dependency set: pip install -r requirements.txt
"""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.providers.base import ProviderRateLimited  # noqa: E402
from app.providers.mock_provider import MockProvider  # noqa: E402
from app.utils.ratelimit import SlidingWindowLimiter  # noqa: E402

BASE = "/api/v1"
MSG = "Explain how recursion works in Python with an example"


@pytest.fixture(scope="module")
def client():
    with TestClient(app, headers={"X-API-Key": "test-key"}) as c:
        yield c


def respond(client, **extra):
    body = {"message": MSG, **extra}
    response = client.post(f"{BASE}/assistant/respond", json=body)
    assert response.status_code == 200, response.text
    return response.json()


# ---- basics, auth, validation --------------------------------------------------
def test_root_and_health_are_public(client):
    no_key = {"X-API-Key": ""}
    assert client.get("/", headers=no_key).status_code == 200
    health = client.get("/health", headers=no_key).json()
    assert health["status"] == "ok" and health["provider"] == "mock" and health["auth_enabled"] is True
    assert "key" not in str(health).lower().replace("auth_enabled", "")
    assert client.get("/health/ready", headers=no_key).json()["status"] == "ready"


def test_api_requires_a_valid_key(client):
    assert client.post(f"{BASE}/assistant/analyze", json={"message": "hello"}, headers={"X-API-Key": "nope"}).status_code == 401
    assert client.post(f"{BASE}/assistant/analyze", json={"message": "hello"}, headers={"X-API-Key": ""}).status_code == 401
    bearer = client.post(f"{BASE}/assistant/analyze", json={"message": "hello world"},
                         headers={"X-API-Key": "", "Authorization": "Bearer test-key"})
    assert bearer.status_code == 200


def test_open_mode_when_no_keys_configured(client, monkeypatch):
    from pydantic import SecretStr

    monkeypatch.setattr(settings, "app_api_keys", SecretStr(""))
    assert client.post(f"{BASE}/assistant/analyze", json={"message": "hello world"}, headers={"X-API-Key": ""}).status_code == 200


def test_validation_rejects_bad_input(client):
    assert client.post(f"{BASE}/assistant/analyze", json={"message": "Explain this", "unexpected": 1}).status_code == 422
    assert client.post(f"{BASE}/assistant/analyze", json={"message": "hi", "session_id": "bad id!"}).status_code == 422
    assert client.post(f"{BASE}/assistant/analyze", json={"message": ""}).status_code == 422


def test_oversized_body_is_rejected(client):
    response = client.post(f"{BASE}/assistant/analyze", content=b"x" * 70_000,
                           headers={"content-type": "application/json"})
    assert response.status_code == 413


def test_request_id_is_returned_and_echoed(client):
    assert client.get("/", headers={"X-Request-ID": "abc-123"}).headers["x-request-id"] == "abc-123"
    assert len(client.get("/", headers={"X-Request-ID": "bad id with spaces"}).headers["x-request-id"]) == 16


def test_analyze_returns_decision_without_provider(client):
    data = client.post(f"{BASE}/assistant/analyze", json={"message": "Help me debug this Python API"}).json()
    assert data["task_type"] == "coding" and data["selected_persona"] == "technical"
    assert data["adaptation"]["method"] in {"insufficient_feedback", "thompson", "greedy", "disabled"}


# ---- respond / sessions / ownership -----------------------------------------------
def test_respond_persists_and_reuses_context(client):
    first = respond(client, user_id="ctx-user")
    assert first["status"] == "completed" and first["meta"]["model"] == "mock-1"
    sid = first["session_id"]
    second = respond(client, user_id="ctx-user", session_id=sid)
    assert "Context turns received: 2" in second["answer"]
    messages = client.get(f"{BASE}/sessions/{sid}", params={"user_id": "ctx-user"}).json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    listed = client.get(f"{BASE}/users/ctx-user/sessions").json()["sessions"]
    assert any(s["session_id"] == sid for s in listed)


def test_short_context_free_request_asks_for_clarification(client):
    data = client.post(f"{BASE}/assistant/respond", json={"message": "Plan my week"}).json()
    assert data["status"] == "needs_clarification" and data["answer"]
    assert data["interaction_id"] is None


def test_sessions_are_bound_to_their_owner(client):
    sid = respond(client, user_id="alice")["session_id"]
    assert client.post(f"{BASE}/assistant/respond", json={"message": MSG, "session_id": sid, "user_id": "bob"}).status_code == 403
    assert client.get(f"{BASE}/sessions/{sid}").status_code == 403
    assert client.get(f"{BASE}/sessions/{sid}", params={"user_id": "bob"}).status_code == 403
    assert client.delete(f"{BASE}/sessions/{sid}", params={"user_id": "bob"}).status_code == 403
    assert client.get(f"{BASE}/sessions/{sid}", params={"user_id": "alice"}).status_code == 200
    assert client.delete(f"{BASE}/sessions/{sid}", params={"user_id": "alice"}).status_code == 200
    assert client.get(f"{BASE}/sessions/{sid}", params={"user_id": "alice"}).status_code == 404


def test_erase_user_removes_everything(client):
    sid = respond(client, user_id="erase-me")["session_id"]
    client.put(f"{BASE}/preferences/erase-me", json={"response_length": "short"})
    assert client.delete(f"{BASE}/users/erase-me").json()["sessions_removed"] >= 1
    assert client.get(f"{BASE}/sessions/{sid}", params={"user_id": "erase-me"}).status_code == 404
    assert client.get(f"{BASE}/preferences/erase-me").json()["preferences"] == {}


def test_preferences_roundtrip_and_influence_prompt(client):
    put = client.put(f"{BASE}/preferences/pref-user", json={"preferred_persona": "concise", "response_length": "short"})
    assert put.json()["preferences"]["preferred_persona"] == "concise"
    data = respond(client, user_id="pref-user")
    assert data["analysis"]["selected_persona"] == "concise"
    assert client.put(f"{BASE}/preferences/pref-user", json={"preferred_persona": "nonsense"}).status_code == 422
    assert client.delete(f"{BASE}/preferences/pref-user").status_code == 200


# ---- feedback & adaptation -----------------------------------------------------------
def test_feedback_rules(client):
    data = respond(client)
    payload = {"interaction_id": data["interaction_id"], "session_id": data["session_id"], "rating": 4}
    assert client.post(f"{BASE}/assistant/feedback", json=payload).status_code == 200
    assert client.post(f"{BASE}/assistant/feedback", json=payload).status_code == 409
    other = respond(client)
    wrong = {"interaction_id": other["interaction_id"], "session_id": "someone-else", "rating": 3}
    assert client.post(f"{BASE}/assistant/feedback", json=wrong).status_code == 403
    assert client.post(f"{BASE}/assistant/feedback", json={"interaction_id": "nope", "rating": 3}).status_code == 404
    assert client.post(f"{BASE}/assistant/feedback", json={"interaction_id": other["interaction_id"], "rating": 9}).status_code == 422


def test_ratings_feed_back_into_strategy_selection(client):
    math = "Solve 3x + 12 = 45 please"
    for _ in range(3):
        data = client.post(f"{BASE}/assistant/respond", json={"message": math}).json()
        client.post(f"{BASE}/assistant/feedback", json={"interaction_id": data["interaction_id"], "rating": 1})
    analysis = client.post(f"{BASE}/assistant/analyze", json={"message": math}).json()
    adaptation = analysis["adaptation"]
    assert adaptation["method"] in {"thompson", "greedy"}
    assert adaptation["arms"][0]["ratings"] == 3 and adaptation["arms"][0]["avg_rating"] == 1.0
    summary = client.get(f"{BASE}/analytics/summary").json()
    assert summary["interactions"] >= 3
    assert any(r["task_type"] == "mathematics" and r["ratings"] >= 3 for r in summary["strategy_ratings"])


# ---- streaming ---------------------------------------------------------------------------
def test_streaming_emits_meta_deltas_and_done(client):
    with client.stream("POST", f"{BASE}/assistant/respond/stream", json={"message": MSG}) as response:
        assert response.status_code == 200 and response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())
    assert body.index("event: meta") < body.index("event: delta") < body.index("event: done")
    assert '"interaction_id"' in body and '"answer"' not in body.split("event: done")[1]


# ---- limits & failures ----------------------------------------------------------------------
def test_generation_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "respond_rate_limit_per_minute", 2)
    client.app.state.limiter = SlidingWindowLimiter()
    codes = [client.post(f"{BASE}/assistant/respond", json={"message": MSG}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
    blocked = client.post(f"{BASE}/assistant/respond", json={"message": MSG})
    assert blocked.headers["retry-after"].isdigit()
    assert client.post(f"{BASE}/assistant/analyze", json={"message": MSG}).status_code == 200  # analyze not limited


def test_provider_errors_map_to_http_errors(client):
    orchestrator = client.app.state.orchestrator
    original = orchestrator.provider
    try:
        orchestrator.provider = MockProvider(fail_with=ProviderRateLimited("slow down", retry_after=7))
        response = client.post(f"{BASE}/assistant/respond", json={"message": MSG})
        assert response.status_code == 429 and response.headers["retry-after"] == "7"
        assert response.json()["code"] == "provider_rate_limited"
        orchestrator.provider = None
        assert client.post(f"{BASE}/assistant/respond", json={"message": MSG}).status_code == 503
    finally:
        orchestrator.provider = original


def test_failed_generation_is_not_persisted(client):
    orchestrator = client.app.state.orchestrator
    original = orchestrator.provider
    try:
        orchestrator.provider = MockProvider(fail_with=ProviderRateLimited("x"))
        sid = "failed-gen-session"
        client.post(f"{BASE}/assistant/respond", json={"message": MSG, "session_id": sid})
    finally:
        orchestrator.provider = original
    assert client.get(f"{BASE}/sessions/{sid}").status_code == 404


def test_model_health_probe(client):
    info = client.get("/health/model", params={"probe": "true"}).json()
    assert info["configured"] is True and info["probe"]["reachable"] is True
    assert client.get("/health/model", headers={"X-API-Key": "bad"}).status_code == 401


# ---- migration -----------------------------------------------------------------------------------
def test_v2_database_is_migrated_in_place(tmp_path):
    from sqlalchemy import create_engine, inspect, text

    from app.database.migrate import add_missing_columns

    engine = create_engine(f"sqlite:///{tmp_path}/old.db")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE interactions (id VARCHAR(36) PRIMARY KEY, session_id VARCHAR(100), user_id VARCHAR(100),"
            " user_message TEXT, assistant_response TEXT, analysis JSON, created_at DATETIME)"
        ))
    added = add_missing_columns(engine)
    columns = {c["name"] for c in inspect(engine).get_columns("interactions")}
    assert {"model", "latency_ms", "prompt_tokens", "completion_tokens", "finish_reason", "evaluation"} <= columns
    assert "interactions.model" in added
