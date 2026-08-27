# Multi-Agent Academic Project Mentor

Three agents (Ideation → Planning → Documentation) orchestrated through a FastAPI backend,
powered by Llama 3.3 70B via the Groq API, with a React chat UI on top.

```
academic-mentor/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── ideation_agent.py
│   │   │   ├── planning_agent.py
│   │   │   └── documentation_agent.py
│   │   ├── main.py          ← orchestrator (FastAPI routes)
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

## Step 1 — Open the project in VS Code

Unzip this folder, then in VS Code: `File → Open Folder…` and select `academic-mentor`.
Open two terminals side by side (`` Ctrl+` `` then click the split-terminal icon) — one for
backend, one for frontend.

## Step 2 — Get a free Groq API key

Go to https://console.groq.com/keys, sign up/log in, and create an API key. Groq is free-tier
friendly and fast — this is why the project brief specified it over a slower/paid provider.

## Step 3 — Backend setup (Terminal 1)

```bash
cd backend
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

Now create your real `.env` file from the example and paste your key in:

```bash
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
```

Open `backend/.env` and replace the placeholder with your actual Groq key:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
```

Run the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

You should see `Uvicorn running on http://127.0.0.1:8000`. Visit
http://localhost:8000/api/health in a browser — you should get `{"status":"ok"}`.
Also check out http://localhost:8000/docs — FastAPI auto-generates an interactive
API tester, which is genuinely useful for demoing the backend on its own in a viva.

## Step 4 — Frontend setup (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — that's your app.

## Step 5 — Using it

1. **Ideation stage**: chat with the Ideation Agent about a domain or rough idea. It'll ask
   clarifying questions and propose 2-3 concrete ideas. When you're happy, click
   **"Finalize Idea → Move to Planning"**.
2. **Planning stage**: the Planning Agent already knows your finalized idea. Discuss timeline,
   tech stack, team split. Click **"Finalize Plan → Generate Documentation"** when ready — this
   auto-generates a full first draft of your report.
3. **Documentation stage**: ask the Documentation Agent to revise any section ("expand the
   literature review", "make the abstract shorter"). Click **"Export as .docx"** any time to
   download a Word file.

## How the orchestration actually works (for your viva/interview)

There's no single mega-prompt. `app/main.py` is a lightweight **orchestrator**: it looks at
`session["stage"]` and routes the message to the matching agent module, using only that stage's
own conversation history. Each agent has its own system prompt scoping it to one job — the
Planning Agent, for example, is explicitly told not to write documentation content, and is fed
the *finalized* idea brief (not the raw chat) so it can't drift from what was actually agreed on.

State is deliberately simple — an in-memory dict keyed by `session_id` (see `state.py`). That's
a conscious scope decision for a 10-week project, not an oversight; the file says so, and you
should be ready to say the same thing if asked "how would you make this production-ready?"
(answer: swap the dict for Redis/Postgres, since in-memory state disappears on restart and
doesn't work across multiple server processes).

## Extending it further (good "future work" talking points)

- Swap the in-memory store for SQLite/Postgres so sessions persist across restarts.
- Add a fourth **Feasibility/Critic Agent** that reviews the Planning Agent's output before it's
  shown to the student — a real multi-agent debate step, not just a pipeline.
- Add RAG over a small corpus of past final-year project reports so the Documentation Agent's
  literature review section is grounded in real papers instead of just describing areas to look at.
- Stream responses token-by-token (Groq supports streaming) instead of waiting for the full reply.