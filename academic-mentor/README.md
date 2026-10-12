# Multi-Agent Academic Project Mentor

A multi-agent AI system that takes a final-year student from a vague project idea to submittable
academic documentation — **Ideation → Planning → Documentation** — powered by three specialized
LLM agents coordinated by a lightweight orchestrator, instead of one general-purpose chatbot
prompt.

Built with **FastAPI**, **React**, and **Llama-class models via the Groq API** (currently
`openai/gpt-oss-120b`).

---

## Why this exists

Existing AI-for-education tools tend to help with one phase in isolation — an idea generator, a
planning assistant, or a doc-formatter — but not the full pipeline a student actually needs for a
capstone project. Multi-agent LLM coordination is an active research pattern (see
**AdvisingWise** for academic advising, **PersonalPlan** for agent-based task planning, and
**Instructional Agents** for role-based ed-tech collaboration), but none of it targets the
specific *idea → plan → documentation* workflow of a final-year project. That gap is what this
project fills.

**Input:** a rough idea or domain of interest.
**Output:** a refined, feasibility-checked project brief → a week-by-week execution plan with a
suggested tech stack → a full academic report (Abstract, Introduction, Problem Statement,
Literature Review skeleton, Methodology, Architecture, Tech Stack, Expected Outcomes, Timeline),
exportable as a `.docx`.

---

## Architecture

```
User input
    │
    ▼
Orchestrator (main.py) — reads session["stage"], routes accordingly
    │
    ├──────────────┐  finalize (summarize)   ┌──────────────┐  finalize (summarize +   ┌────────────────────┐
    │  Ideation     │ ───────────────────────▶│  Planning    │  auto-generate)          │  Documentation      │
    │  Agent        │                          │  Agent       │ ────────────────────────▶│  Agent              │
    └──────────────┘                          └──────────────┘                          └────────────────────┘
```

This is **not a linear pipeline** — it's a stateful loop. Each stage keeps its own conversation
history, and a stage only ever receives the *finalized, summarized brief* of the stage before it
— never the raw upstream chat. That scoping is the actual design decision worth highlighting: it
stops the Planning Agent from drifting based on ideation small-talk, and stops the Documentation
Agent from inventing scope the student never agreed to.

The frontend mirrors this with three independently-viewable tabs — you can switch back to a
completed stage to review it (read-only) without losing your place in the active one.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| LLM | `openai/gpt-oss-120b` via Groq | Fast inference matters when a single turn can trigger multiple chained LLM calls (chat + summarization). Originally built on Llama 3.3 70B; migrated after Groq deprecated it. |
| Backend | FastAPI | Async-friendly, and auto-generates an interactive API tester at `/docs`. |
| Orchestration | Custom Python router (no LangChain/LangGraph) | Explicit stage-routing logic in `main.py`, written by hand rather than pulled from a framework. |
| State | In-memory session dict | Deliberately scoped for a college project — see [Limitations](#limitations). |
| Frontend | React + Vite | Fast dev loop, component-based chat UI. |
| Markdown rendering | `react-markdown` + `remark-gfm` | GFM extension needed specifically for table support. |
| Doc export | `python-docx`, hand-written Markdown→docx converter | Renders headings, bold, and Markdown tables as real Word elements — not literal text. |

---

## How the agents work

Each "agent" is a system prompt + a small Python function — same underlying model, different
role and different slice of context:

- **Ideation Agent** — asks short clarifying questions, proposes 2–3 scoped project ideas with
  feasibility and novelty notes, and explicitly confirms before finishing. Constrained from
  jumping into planning.
- **Planning Agent** — receives only the *finalized* idea brief (not the raw chat), produces a
  week-by-week milestone plan and tech stack suggestion. Constrained from writing documentation.
- **Documentation Agent** — receives both finalized briefs, generates strict-section Markdown,
  and is explicitly instructed never to fabricate citations, statistics, or prior work.

No agent calls another directly — the orchestrator is the only component that sees all three,
which keeps each agent independently testable.

---

## Project structure

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

---

## Setup

### 1. Get a Groq API key
Free tier available at https://console.groq.com/keys.

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
cp .env.example .env         # then paste your key into .env
uvicorn app.main:app --reload --port 8000
```
Check `http://localhost:8000/api/health` → should return `{"status":"ok"}`.

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

---

## Usage

1. **Ideation** — describe a domain or rough idea; the agent asks clarifying questions and
   proposes concrete options. Click **Finalize Idea** once you're happy with one.
2. **Planning** — discuss timeline, tech stack, and team roles. Click **Finalize Plan** — this
   auto-generates the first full documentation draft immediately.
3. **Documentation** — ask for revisions to any section. Click **Export as .docx** any time.

---

## Challenges & solutions

| Challenge | Root cause | Fix |
|---|---|---|
| `TypeError: got an unexpected keyword argument 'proxies'` | `groq` SDK version incompatible with a newer auto-installed `httpx` | Pinned `httpx==0.27.2` |
| `404 model_not_found` | Groq deprecated `llama-3.3-70b-versatile` | Migrated to `openai/gpt-oss-120b` |
| Markdown printing as literal `**text**` | Chat UI had no Markdown parser | Added `react-markdown` |
| Tables printing as raw `\| pipe \| text \|` | Pipe-tables are a GFM extension, not core Markdown | Added `remark-gfm` |
| Documentation cut off mid-section | `max_tokens` too low for a full report | Raised to 4096 for the Documentation Agent |
| Chat history vanishing between stages | State was replaced instead of appended on each transition | Restructured into per-stage message arrays |
| Exported `.docx` had literal `**bold**` and no real tables | Naive line-by-line Markdown parser | Rewrote to detect table blocks and inline bold, generate real Word tables/runs |

---

## Limitations

- **Session state is in-memory** — resets on server restart, doesn't scale across multiple
  server processes. A production version would swap this for Redis or Postgres.
- **No RAG** — the Literature Review section describes *areas* to research rather than citing
  real papers, by design (to avoid fabricated citations).
- **Single-user sessions** — no authentication or multi-user isolation.

## Future work

- A fourth **Feasibility/Critic Agent** that reviews the Planning Agent's output before showing
  it to the student — genuine agent-to-agent review, not just a pipeline.
- RAG over a corpus of past final-year project reports to ground the Literature Review in real
  citations.
- Streaming responses (Groq supports this) instead of waiting for the full reply.
- Persistent storage so sessions survive a server restart.
