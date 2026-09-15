"""
In-memory session store. Fine for a college project/demo — swap for
Redis/Postgres if this ever needs to survive a server restart or run
across multiple processes.
"""

import uuid

SESSIONS: dict[str, dict] = {}


def create_session() -> str:
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "stage": "ideation",  # ideation -> feasibility -> planning -> documentation
        "ideation_history": [],
        "feasibility_history": [],
        "planning_history": [],
        "documentation_history": [],
        "idea_brief": None,
        "related_work": None,       # raw dict: {"papers": [...], "repos": [...]}
        "related_work_text": None,  # formatted Markdown, reused across stages
        "feasibility_brief": None,
        "plan_brief": None,
        "doc_content": None,
    }
    return session_id


def get_session(session_id: str) -> dict:
    if session_id not in SESSIONS:
        raise KeyError("Unknown session_id. Start a new session first.")
    return SESSIONS[session_id]
