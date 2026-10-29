from app.groq_client import call_llm

SYSTEM_PROMPT = """You are the Feasibility Agent inside a multi-agent academic project mentor
system. You receive a student's finalized project idea brief AND a list of related academic
papers and GitHub repositories found via a real search (provided below, in Markdown).

Your job:
1. Compare the idea against each listed paper/repo. Be specific — name the actual title when
   something overlaps.
2. If the idea is essentially a duplicate of something already listed (not meaningfully novel),
   explain why in 2-4 sentences and propose 1-2 concrete differentiating twists the student could
   adopt. Do NOT include the token [APPROVED] anywhere in this response.
3. If the idea already has enough novelty relative to what's listed — OR once the student adopts
   a twist that meaningfully differentiates it — confirm this in 2-4 sentences and end your
   response with the exact token [APPROVED] on its own line.
4. Keep the tone collaborative, not just a gatekeeper — you're helping them find a unique angle,
   not just rejecting ideas.
5. Re-evaluate fresh each time the student proposes a change; don't assume approval carries over
   unless the current idea actually clears the bar.
"""


# The default of 1024 cut long table-style replies off mid-sentence. Input here is small
# (brief + search results + short chat), so 2048 output stays well under the 8000 limit.
FEASIBILITY_MAX_TOKENS = 2048


def _context(idea_brief: str, related_work_text: str) -> str:
    return (
        SYSTEM_PROMPT
        + f"\n\nFinalized idea brief:\n{idea_brief}"
        + f"\n\nRelated work found via search:\n{related_work_text}"
    )


def initial_verdict(idea_brief: str, related_work_text: str) -> str:
    """First automatic message once an idea is finalized — runs the comparison immediately."""
    system = _context(idea_brief, related_work_text)
    messages = [
        {
            "role": "user",
            "content": "Please assess the feasibility and novelty of my idea against the related work listed above.",
        }
    ]
    return call_llm(system, messages, temperature=0.4, max_tokens=FEASIBILITY_MAX_TOKENS)


def chat(idea_brief: str, related_work_text: str, history: list[dict]) -> str:
    system = _context(idea_brief, related_work_text)
    return call_llm(system, history, temperature=0.4, max_tokens=FEASIBILITY_MAX_TOKENS)
