"""
Very simple in-memory session store.
Fine for a college project / demo. If you ever deploy this for real,
swap this dict for Redis or a database — in-memory state disappears
whenever the server restarts and won't work across multiple server processes.
"""

import uuid

SESSIONS: dict[str, dict] = {}


def create_session() -> str:
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "stage": "ideation",          # ideation -> planning -> documentation -> done
        "ideation_history": [],
        "planning_history": [],
        "documentation_history": [],
        "idea_brief": None,
        "plan_brief": None,
        "doc_content": None,
    }
    return session_id


def get_session(session_id: str) -> dict:
    if session_id not in SESSIONS:
        raise KeyError("Unknown session_id. Start a new session first.")
    return SESSIONS[session_id]
