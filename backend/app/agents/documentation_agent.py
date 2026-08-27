from app.groq_client import call_llm

SYSTEM_PROMPT = """You are the Documentation Agent inside a multi-agent academic project mentor system.
You receive a finalized idea brief and a finalized plan brief, and produce academic documentation.

Rules:
- Generate content in clean Markdown with headings, suitable for a final-year project report.
- Always include these sections in this order: Abstract, Introduction, Problem Statement,
  Literature Review (skeleton with 3-4 bullet points of areas to research, not fake citations),
  Proposed System / Methodology, System Architecture (described in words), Tech Stack,
  Expected Outcomes, Timeline.
- Never invent fake citations, fake statistics, or fake prior work with specific numbers.
  For the literature review, describe the AREAS to review, not fabricated papers.
- When the student asks for edits, revise only the relevant section and return the FULL
  updated document again in the same Markdown format.
"""

GENERATE_PROMPT = """Using the idea brief and plan brief below, generate the full project
documentation in Markdown following the required section structure.

Idea brief:
{idea_brief}

Plan brief:
{plan_brief}
"""


DOC_MAX_TOKENS = 4096


def generate(idea_brief: str, plan_brief: str) -> str:
    prompt = GENERATE_PROMPT.format(idea_brief=idea_brief, plan_brief=plan_brief)
    return call_llm(
        SYSTEM_PROMPT,
        [{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=DOC_MAX_TOKENS,
    )


def revise(idea_brief: str, plan_brief: str, history: list[dict]) -> str:
    system = SYSTEM_PROMPT + f"\n\nIdea brief:\n{idea_brief}\n\nPlan brief:\n{plan_brief}"
    return call_llm(system, history, temperature=0.4, max_tokens=DOC_MAX_TOKENS)
