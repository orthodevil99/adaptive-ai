# Adaptive AI — Integrated Full-Stack Project (Design 3 Circuit Glass + v3 Backend)

This archive combines:
- **`adaptive-ai-backend/`** — Your team's production-grade `adaptive_ai_v3` FastAPI backend (Thompson-sampling adaptation, SSE streaming, SQLAlchemy + SQLite, Groq + offline `mock` provider, Docker, CI, pytest).
- **`adaptive-ai-web/`** — The **Design 3 (Circuit Glass)** React 18 + TypeScript + Tailwind frontend wired natively to all `/api/v1` endpoints, including 1–5 star adaptation feedback and the radial A-Score gauge.

---

## Quick Start (Runs Immediately Without an API Key)

### Terminal 1 — Backend (pre-configured in `PROVIDER=mock` mode)
```bash
cd adaptive-ai-backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Terminal 2 — Frontend (Design 3 Circuit Glass UI)
```bash
cd adaptive-ai-web
npm install
npm run dev
```

Open **http://localhost:5173**.

---

## Switching to Live Groq Responses Later
When you're ready to add your API key, edit `adaptive-ai-backend/.env`:
```env
PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```
Then restart `uvicorn`—no frontend changes needed!
