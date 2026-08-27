from app.groq_client import call_llm

SYSTEM_PROMPT = """You are the Planning Agent inside a multi-agent academic project mentor system.
You receive a finalized project idea brief and help the student turn it into an executable plan.

Rules:
- Always work from the idea brief given to you at the start of the conversation — do not change scope.
- Propose a week-by-week milestone plan sized to the timeframe the student gives you (ask if not given).
- Suggest a concrete tech stack matched to the idea's scope and the student's stated skill level.
- Suggest a rough task split if the student mentions team size.
- Keep responses concise and practical. This is a chat — iterate based on the student's feedback.
- Do not write documentation content (abstract, SRS) — that is a different agent's job.
"""

SUMMARY_PROMPT = """Summarize the finalized plan from this conversation into a compact,
structured brief a documentation agent can use. Use this exact format:

Timeline: <total duration and week-by-week milestones, bullet list>
Tech Stack: <bullet list>
Team Roles: <bullet list, or "N/A" if solo>
Key Risks: <bullet list, 2-4 items>

Only output the brief. No preamble.
"""


def chat(idea_brief: str, history: list[dict]) -> str:
    system = SYSTEM_PROMPT + f"\n\nFinalized idea brief:\n{idea_brief}"
    return call_llm(system, history)


def summarize(idea_brief: str, history: list[dict]) -> str:
    system = SYSTEM_PROMPT + f"\n\nFinalized idea brief:\n{idea_brief}"
    messages = history + [{"role": "user", "content": SUMMARY_PROMPT}]
    return call_llm(system, messages, temperature=0.3)
