from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.models import ChatRequest, ChatResponse, FinalizeResponse, SessionResponse
from app.state import create_session, get_session
from app.agents import ideation_agent, planning_agent, documentation_agent
from app.export import markdown_to_docx_bytes

app = FastAPI(title="Multi-Agent Academic Project Mentor")

# Allow the local React dev server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/session", response_model=SessionResponse)
def new_session():
    session_id = create_session()
    return SessionResponse(session_id=session_id, stage="ideation")


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    The orchestrator: routes the incoming message to whichever agent
    owns the session's current stage, using that stage's own history.
    """
    try:
        session = get_session(req.session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    stage = session["stage"]

    if stage == "ideation":
        session["ideation_history"].append({"role": "user", "content": req.message})
        reply = ideation_agent.chat(session["ideation_history"])
        session["ideation_history"].append({"role": "assistant", "content": reply})

    elif stage == "planning":
        session["planning_history"].append({"role": "user", "content": req.message})
        reply = planning_agent.chat(session["idea_brief"], session["planning_history"])
        session["planning_history"].append({"role": "assistant", "content": reply})

    elif stage == "documentation":
        session["documentation_history"].append({"role": "user", "content": req.message})
        reply = documentation_agent.revise(
            session["idea_brief"], session["plan_brief"], session["documentation_history"]
        )
        session["documentation_history"].append({"role": "assistant", "content": reply})
        session["doc_content"] = reply

    else:
        raise HTTPException(status_code=400, detail=f"No agent handles stage '{stage}'")

    return ChatResponse(stage=stage, reply=reply)


@app.post("/api/finalize-idea", response_model=FinalizeResponse)
def finalize_idea(req: ChatRequest):
    """Locks in the idea brief and advances the session to the planning stage."""
    session = get_session(req.session_id)
    if session["stage"] != "ideation":
        raise HTTPException(status_code=400, detail="Session is not in the ideation stage")

    brief = ideation_agent.summarize(session["ideation_history"])
    session["idea_brief"] = brief
    session["stage"] = "planning"
    return FinalizeResponse(stage="planning", brief=brief)


@app.post("/api/finalize-plan", response_model=FinalizeResponse)
def finalize_plan(req: ChatRequest):
    """Locks in the plan brief, generates the first documentation draft, advances stage."""
    session = get_session(req.session_id)
    if session["stage"] != "planning":
        raise HTTPException(status_code=400, detail="Session is not in the planning stage")

    plan_brief = planning_agent.summarize(session["idea_brief"], session["planning_history"])
    session["plan_brief"] = plan_brief

    doc = documentation_agent.generate(session["idea_brief"], plan_brief)
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
