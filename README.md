# Multi-Agent Academic Project Mentor

A multi-agent AI system that takes a final-year student from a vague project idea to submittable
academic documentation — **Ideation → Feasibility → Planning → Documentation** — powered by four
specialized LLM agents, a real literature/code search step, and a lightweight orchestrator.

Built with **FastAPI**, **React**, **Llama-class models via the Groq API**
(`openai/gpt-oss-120b`), **Semantic Scholar** and **GitHub** search for grounding.

---

## How it works

```
User input (rough idea)
    │
    ▼
┌──────────────┐  finalize    ┌────────────────┐  finalize     ┌──────────────┐  finalize    ┌────────────────────┐
│  1. Ideation  │ ───────────▶│  2. Feasibility │ ─────────────▶│  3. Planning │ ────────────▶│  4. Documentation   │
│  Agent        │              │  Agent (+ RAG)  │  (only if      │  Agent       │               │  Agent              │
│               │              │                 │  [APPROVED])   │              │               │                     │
└──────────────┘              └────────────────┘                └──────────────┘               └────────────────────┘
```

1. **Ideation Agent** — refines a rough idea into a structured brief through conversation.
2. **Feasibility Agent** — on finalize, the system automatically searches **Semantic Scholar**
   (papers) and **GitHub** (repos) for the 3 closest existing matches, then the agent compares
   the idea against them. If it's a near-duplicate, it explains why and proposes a differentiating
   twist — the idea can't move to Planning until the agent's response contains `[APPROVED]`.
3. **Planning Agent** — builds a week-by-week milestone plan and tech stack. Paste your grading
   rubric into the chat here and it allocates an approximate word-count target per report section
   based on the rubric's weighting.
4. **Documentation Agent** — writes the full report, grounded to **only** cite the verified
   sources found in step 2 (real titles + real URLs) — never fabricated citations — and follows
   the word-count targets from step 3.

Each stage keeps its own conversation history and only receives a *finalized, summarized brief*
of the stage before it, never the raw upstream chat — this stops later agents from drifting based
on rejected ideas or side conversations.

---

## Why this design (novelty vs. existing work)

Multi-agent LLM coordination for education already exists as a research pattern (AdvisingWise,
PersonalPlan, Instructional Agents), but none of it combines a **real-time novelty check against
live search results** with a hard approval gate before planning begins. That's the differentiator
here — it's not just "ask an AI for project ideas," it's "verify the idea isn't a duplicate of
something that already exists, using actual search data, before any planning work happens."

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| LLM | `openai/gpt-oss-120b` via Groq | Fast inference for chained calls (chat + summarization + generation). |
| Retrieval | Semantic Scholar API (papers) + GitHub Search API (repos) | Both free, no local vector DB needed — retrieval happens live at request time. |
| Backend | FastAPI | Async-friendly, interactive API docs at `/docs`. |
| Orchestration | Custom Python state machine (no LangGraph — yet, see Future Work) | Explicit, debuggable stage routing. |
| State | In-memory session dict | Scoped intentionally for a college project — see Limitations. |
| Frontend | React + Vite | Component-based chat UI with 4 independently-viewable stage tabs. |
| Markdown rendering | `react-markdown` + `remark-gfm` | GFM needed specifically for table support. |
| Doc export | `python-docx`, hand-written Markdown→docx converter | Real Word tables and bold formatting, not literal text. |

---

## Project structure

```
academic-mentor/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── ideation_agent.py
│   │   │   ├── feasibility_agent.py
│   │   │   ├── planning_agent.py
│   │   │   └── documentation_agent.py
│   │   ├── main.py          ← orchestrator (FastAPI routes)
│   │   ├── rag.py           ← Semantic Scholar + GitHub search
│   │   ├── groq_client.py   ← single wrapper around the Groq API
│   │   ├── state.py         ← in-memory session store
│   │   ├── models.py        ← request/response schemas
│   │   └── export.py        ← Markdown → .docx conversion
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/
    └── package.json
```

---

## Setup

### 1. Get a Groq API key
Free tier at https://console.groq.com/keys.

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
cp .env.example .env         # paste your Groq key in
uvicorn app.main:app --reload --port 8000
```
Check `http://localhost:8000/api/health` → `{"status":"ok"}`.

`GITHUB_TOKEN` in `.env` is optional — raises GitHub's search rate limit if you hit it
during heavy testing. Not required to run the project.

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

---

## Run in VS Code (Windows)

1. `File → Open Folder…` and pick the `academic-mentor` folder (the one containing `backend` and `frontend`).
2. Open two terminals (`` Ctrl+` ``, then the split icon).
3. **Terminal 1 — backend**
   ```
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```
   Open `backend\.env` and paste your Groq key after `GROQ_API_KEY=`, then:
   ```
   uvicorn app.main:app --reload --port 8000
   ```
   `http://localhost:8000/api/health` should return `{"status":"ok"}`.
4. **Terminal 2 — frontend**
   ```
   cd frontend
   npm install
   npm run dev
   ```
5. Open `http://localhost:5173`.

Every new terminal needs `venv\Scripts\activate` again before running `uvicorn`.

---

## Deploy

Backend (FastAPI) and frontend (static Vite build) deploy separately.

**Backend — e.g. Render "Web Service"**
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (keep a single worker — sessions live in memory)
- Environment variables: `GROQ_API_KEY`, `FRONTEND_ORIGINS` (your frontend URL, no trailing slash), optional `GITHUB_TOKEN`

**Frontend — e.g. Vercel / Netlify**
- Root directory: `frontend`, build command: `npm run build`, output directory: `dist`
- Environment variable: `VITE_API_URL` = your backend URL (baked in at build time — redeploy after changing it)

Deploy the backend first, then the frontend, then set `FRONTEND_ORIGINS` on the backend to the frontend URL.

Known deployment limits: sessions are in memory (lost on restart or idle spin-down), and all users share one Groq key and its rate limit.

---

## Usage

1. **Ideation** — describe your idea; finalize once the agent's brief matches what you meant.
2. **Feasibility** — the system searches for related papers/repos automatically and shows you
   the closest matches plus a verdict. If not approved, discuss a twist with the agent until you
   see `[APPROVED]`, then click **Finalize Feasibility**.
3. **Planning** — discuss timeline/stack, paste your grading rubric if you have one, then
   **Finalize Plan** — this auto-generates the first documentation draft.
4. **Documentation** — ask for revisions to any section. **Export as .docx** any time.

---

## Limitations

- **In-memory session state** — resets on server restart, single-process only.
- **Search quality varies by idea phrasing** — very niche or newly-coined project names may
  return few/no matches; the pipeline degrades gracefully (shows "no related work found")
  rather than failing.
- **No local vector DB / persistent citation corpus** — retrieval is live per-request, not
  pre-indexed.
- Single-user sessions, no authentication.

## Future work

- Migrate orchestration to **LangGraph** — graph-based state persistence and easier conditional
  branching (e.g. auto-loop back to Planning if a future Critic Agent rejects a plan).
- Add a small local vector index (ChromaDB/FAISS) over a curated corpus, so citation quality
  doesn't depend entirely on live API search results.
- Persistent storage (Redis/Postgres) so sessions survive a restart.
- Streaming responses instead of waiting for the full reply.
