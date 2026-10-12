from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.models import ChatRequest, ChatResponse, FinalizeResponse, SessionResponse
from app.state import create_session, get_session
from app.agents import ideation_agent, feasibility_agent, planning_agent, documentation_agent
from app import rag
from app.export import markdown_to_docx_bytes

app = FastAPI(title="Multi-Agent Academic Project Mentor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RuntimeError)
def runtime_error_handler(request, exc: RuntimeError):
    """
    Converts the friendly RuntimeErrors raised in groq_client.py (timeouts, 413s)
    into a proper JSON error response instead of a raw 500/'Failed to fetch' on
    the frontend with no explanation.
    """
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.post("/api/session", response_model=SessionResponse)
def new_session():
    session_id = create_session()
    return SessionResponse(session_id=session_id, stage="ideation")


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Orchestrator: routes the message to whichever agent owns the current stage."""
    try:
        session = get_session(req.session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    stage = session["stage"]

    if stage == "ideation":
        session["ideation_history"].append({"role": "user", "content": req.message})
        reply = ideation_agent.chat(session["ideation_history"])
        session["ideation_history"].append({"role": "assistant", "content": reply})

    elif stage == "feasibility":
        session["feasibility_history"].append({"role": "user", "content": req.message})
        reply = feasibility_agent.chat(
            session["idea_brief"], session["related_work_text"], session["feasibility_history"]
        )
        session["feasibility_history"].append({"role": "assistant", "content": reply})

    elif stage == "planning":
        session["planning_history"].append({"role": "user", "content": req.message})
        reply = planning_agent.chat(session["idea_brief"], session["planning_history"])
        session["planning_history"].append({"role": "assistant", "content": reply})

    elif stage == "documentation":
        session["documentation_history"].append({"role": "user", "content": req.message})
        reply = documentation_agent.revise(
            session["idea_brief"],
            session["plan_brief"],
            session["related_work_text"],
<<<<<<< HEAD:backend/app/main.py
            session["documentation_history"],
=======
            session["doc_content"],
            req.message,
>>>>>>> 95add18 (Integrated feasibility agent):academic-mentor/backend/app/main.py
        )
        session["documentation_history"].append({"role": "assistant", "content": reply})
        session["doc_content"] = reply

    else:
        raise HTTPException(status_code=400, detail=f"No agent handles stage '{stage}'")

    return ChatResponse(stage=stage, reply=reply)


@app.post("/api/finalize-idea", response_model=FinalizeResponse)
def finalize_idea(req: ChatRequest):
    """
    Step 1 -> Step 2 handoff: locks in the idea, runs a real search (Semantic
    Scholar + GitHub) for related work, and immediately gets the Feasibility
    Agent's first verdict — this is the RAG step.
    """
    session = get_session(req.session_id)
    if session["stage"] != "ideation":
        raise HTTPException(status_code=400, detail="Session is not in the ideation stage")

    idea_brief = ideation_agent.summarize(session["ideation_history"])
    session["idea_brief"] = idea_brief

    query = rag.extract_search_query(idea_brief)
    related = rag.gather_related_work(query)
    related_text = rag.format_related_work(related)
    session["related_work"] = related
    session["related_work_text"] = related_text

    verdict = feasibility_agent.initial_verdict(idea_brief, related_text)
    auto_message = f"{related_text}\n\n---\n\n{verdict}"
    session["feasibility_history"].append({"role": "assistant", "content": auto_message})

    session["stage"] = "feasibility"
    return FinalizeResponse(stage="feasibility", brief=idea_brief, auto_message=auto_message)


@app.post("/api/finalize-feasibility", response_model=FinalizeResponse)
def finalize_feasibility(req: ChatRequest):
    """
    Step 2 -> Step 3 handoff: only allowed once the Feasibility Agent's most
    recent message actually contains the [APPROVED] token.
    """
    session = get_session(req.session_id)
    if session["stage"] != "feasibility":
        raise HTTPException(status_code=400, detail="Session is not in the feasibility stage")

    history = session["feasibility_history"]
    if not history or "[approved]" not in history[-1]["content"].lower():
        raise HTTPException(
            status_code=400,
            detail="The Feasibility Agent hasn't approved this idea yet — keep refining "
                   "(or adopt a suggested twist) until you get [APPROVED].",
        )

    session["feasibility_brief"] = history[-1]["content"]
    session["stage"] = "planning"
    return FinalizeResponse(stage="planning", brief=session["feasibility_brief"])


@app.post("/api/finalize-plan", response_model=FinalizeResponse)
def finalize_plan(req: ChatRequest):
    """Step 3 -> Step 4 handoff: locks the plan, auto-generates the first documentation draft."""
    session = get_session(req.session_id)
    if session["stage"] != "planning":
        raise HTTPException(status_code=400, detail="Session is not in the planning stage")

    plan_brief = planning_agent.summarize(session["idea_brief"], session["planning_history"])
    session["plan_brief"] = plan_brief

    doc = documentation_agent.generate(
        session["idea_brief"], plan_brief, session["related_work_text"]
    )
    session["doc_content"] = doc
    session["documentation_history"].append({"role": "assistant", "content": doc})

    session["stage"] = "documentation"
    return FinalizeResponse(stage="documentation", brief=plan_brief)


@app.get("/api/document/{session_id}")
def get_document(session_id: str):
    session = get_session(session_id)
    return {"content": session["doc_content"] or ""}


@app.get("/api/export/{session_id}")
def export_docx(session_id: str):
    session = get_session(session_id)
    if not session["doc_content"]:
        raise HTTPException(status_code=400, detail="No documentation generated yet")

    docx_bytes = markdown_to_docx_bytes(session["doc_content"])
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=project_documentation.docx"},
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}
