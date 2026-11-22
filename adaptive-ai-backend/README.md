# Adaptive AI Backend v3

FastAPI backend that decides **how** to answer before it calls the model: it classifies the request, picks a persona and response strategy, learns from user ratings which strategies work, then calls Groq (`openai/gpt-oss-120b` by default) and checks the result.

```
request ─► classify ─► complexity ─► persona ─► strategy ─► adaptation (ratings) ─► prompt + params
                                                                                        │
 SQLite/Postgres ◄── persist ◄── evaluate/redact ◄── provider (Groq, fallback, stream) ◄┘
```

The orchestration engine (`app/core`, `app/intelligence`, `app/services`) only knows the `TextProvider` interface (`app/providers/base.py`). Groq is one implementation, `mock` is another; adding another provider means one new file.

## What changed from v2

| Area | v3 |
|---|---|
| **Groq calls** | Real `system` + chat-turn messages (history is no longer pasted into one prompt). `reasoning_effort` and token budget chosen per request. Automatic fallback model (`openai/gpt-oss-20b`) on rate limit / 5xx / timeout. Recovers when reasoning eats the whole token budget. Concurrency cap. Provider errors map to proper HTTP codes (429 + `Retry-After`, 502, 503, 504). |
| **Streaming** | `POST /api/v1/assistant/respond/stream` (Server-Sent Events). |
| **Adaptation** | Thompson-sampling bandit per task type over candidate strategies (modes: `thompson`, `greedy`, `off`). Every response reports the evidence behind the choice. Replaces the old single "score < 0.4" rule. |
| **Classifier** | Weighted terms + structural signals (code fences, tracebacks, math). `multi_intent` now needs two strong, close intents, so "Explain how a Python API works" is no longer treated as multi-intent. |
| **Evaluator** | Truncation, empty output, credential-like text, and strategy-specific structure checks, with a 0-1 quality score. |
| **Security** | API-key auth, per-caller rate limits, body-size limit, request IDs, secret redaction in logs and answers, session ownership checks, injection flags, safe-alphabet IDs, docs off in production, startup refuses unsafe production config. |
| **Data** | Session table with ownership, per-interaction model / latency / token telemetry, unique feedback per interaction, SQLite WAL + foreign keys, automatic in-place migration of v2 databases, retention (`SESSION_TTL_DAYS`), user-data erasure endpoint. |
| **Ops** | `/health`, `/health/ready`, `/health/model?probe=true` (validates your key and model), JSON logs, Dockerfile, CI on Python 3.12 and 3.14, `scripts/smoke_test.py`. |

## Setup (Windows PowerShell)

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_key_here
APP_API_KEYS=<output of: python -c "import secrets; print(secrets.token_urlsafe(32))">
```

Run it, then verify against the real Groq API:

```powershell
uvicorn app.main:app --reload
$env:SMOKE_API_KEY = "<the APP_API_KEYS value>"
python scripts/smoke_test.py
```

No key yet? Set `PROVIDER=mock` to get deterministic offline answers for front-end work. Swagger UI is at `http://127.0.0.1:8000/docs`.

## Calling the API

Send your `APP_API_KEYS` value as `X-API-Key` (or `Authorization: Bearer ...`). Leave `APP_API_KEYS` empty only for local development.

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/assistant/respond `
  -H "X-API-Key: $env:SMOKE_API_KEY" -H "Content-Type: application/json" `
  -d '{\"message\":\"Explain Python decorators\",\"user_id\":\"demo\"}'
```

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` · `/health/ready` | Liveness (+ safe config summary) · DB readiness (public) |
| GET | `/health/model?probe=true` | Provider config; `probe` checks key + model availability (needs key) |
| POST | `/api/v1/assistant/analyze` | Decision only: intent, complexity, persona, strategy, adaptation evidence |
| POST | `/api/v1/assistant/respond` | Full pipeline, returns answer, evaluation, model/latency/token `meta` |
| POST | `/api/v1/assistant/respond/stream` | Same, as SSE: `meta` → `delta`* → `done` (or `error`) |
| POST | `/api/v1/assistant/feedback` | 1-5 rating; feeds strategy adaptation (one per interaction) |
| GET / DELETE | `/api/v1/sessions/{id}?user_id=` | Read (paged) / delete a session |
| GET | `/api/v1/users/{user_id}/sessions` | List a user's sessions |
| DELETE | `/api/v1/users/{user_id}` | Erase all of a user's data |
| GET / PUT / DELETE | `/api/v1/preferences/{user_id}` | Persona, response length, explanation style |
| GET | `/api/v1/analytics/summary` | Usage, latency, per-task strategy ratings |

Streaming example (browser/JS): read the response body as `text/event-stream`; `delta` events carry `{"text": "..."}`; the final `done` event carries `interaction_id`, `evaluation`, and `meta` (use `interaction_id` for feedback).

## How adaptation works

For each task type, the rule-based strategy is the default "arm" and two alternatives are the others. Ratings become rewards (`(rating-1)/4`) updating a Beta posterior per arm.

- The default is always used until it has `MIN_FEEDBACK_SAMPLES` ratings.
- `thompson`: sample each posterior, pick the highest. The default has an optimistic prior and untested alternatives a sceptical one, so exploration is rare (a few percent) unless the default is rated poorly.
- `greedy`: best posterior mean. `off`: always the default.

This tunes prompting strategy only. It does not fine-tune the model, and feedback is pooled per task type across users.

## Configuration

All settings are environment variables / `.env` (see `.env.example`, which documents each one). Notable: `GROQ_FALLBACK_MODEL`, `GROQ_REASONING` (set `false` if a future model rejects `reasoning_effort`), `MAX_CONCURRENT_GENERATIONS` (protects free-tier limits), `RESPOND_RATE_LIMIT_PER_MINUTE`, `ADAPTATION_MODE`, `SESSION_TTL_DAYS`.

## Tests

```powershell
pytest -q
```

- `test_core.py`, `test_providers.py`: pure logic and the Groq provider against a scripted fake client. No network or key.
- `test_api.py`: full API flows (auth, ownership, streaming, rate limits, feedback → adaptation, migration) against the mock provider.
- Tests never call Groq. Run `scripts/smoke_test.py` for a real end-to-end check of your key, model access and limits.

## Security notes and limits

- **Rotate any key that has been pasted into a chat, ticket, or commit.** Keep keys in `.env` / environment variables only.
- `user_id` is a caller-supplied label, not authentication. One shared API key protects the whole API; session ownership prevents accidental cross-user access but not a caller who knows another user's id. For real multi-user exposure, put your own auth in front and derive `user_id` from it.
- The rate limiter is in-process (per worker). Behind several workers, enforce limits at a gateway or add a shared store.
- Streamed text is sent as generated, so answer-level secret redaction applies to stored/non-streamed answers only. The model is never given your keys.
- The evaluator checks form (structure, truncation, leaks), not factual correctness. The classifier is rule-based and English-centric.
- Not implemented: semantic/vector memory, rolling conversation summaries, tool use / web access, Alembic migrations (a small additive auto-migration covers v2 → v3), distributed rate limiting.
- SQLite is fine for a demo or single instance; use PostgreSQL for concurrent hosted use (`DATABASE_URL`).

## Docker (untested here)

```bash
docker build -t adaptive-ai .
docker run -p 8000:8000 -e GROQ_API_KEY=... -e APP_API_KEYS=... -e CORS_ORIGINS=https://your.app -v adaptive-data:/srv/data adaptive-ai
```

`APP_ENV=production` is set in the image; the server refuses to start in production without `APP_API_KEYS`.
