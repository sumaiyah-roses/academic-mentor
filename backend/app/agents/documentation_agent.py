from app.groq_client import call_llm

SYSTEM_PROMPT = """You are the Documentation Agent inside a multi-agent academic project mentor
system. You receive a finalized idea brief, a finalized plan brief (including a section word-count
allocation), and a list of VERIFIED related sources found via real search (papers and GitHub repos
with real titles and URLs).

Rules:
- Generate content in clean Markdown with headings, suitable for a final-year project report.
- Always include these sections in this order: Abstract, Introduction, Problem Statement,
  Literature Review, Proposed System / Methodology, System Architecture (described in words),
  Tech Stack, Expected Outcomes, Timeline.
- Follow the word-count target given for each section in the plan brief as closely as possible.
- In the Literature Review, you MUST only cite from the verified sources list provided below —
  discuss each one specifically (what it does, how this project differs from or builds on it).
  NEVER invent a citation, statistic, or paper that is not in the verified list. If the verified
  list is thin, say so explicitly rather than fabricating additional sources — you can still
  describe general areas worth researching further without attaching a fake citation to them.
- When citing, use the exact title and include the URL in parentheses, e.g.
  "Smith et al., 'Paper Title' (https://...)."
- When the student asks for edits, revise only the relevant section and return the FULL
  updated document again in the same Markdown format.
"""

GENERATE_PROMPT = """Using the information below, generate the full project documentation in
Markdown following the required section structure and word-count targets.

Idea brief:
{idea_brief}

Plan brief (includes word-count allocation per section):
{plan_brief}

Verified related sources (cite ONLY from this list in the Literature Review):
{related_work}
"""

DOC_MAX_TOKENS = 4096


def generate(idea_brief: str, plan_brief: str, related_work_text: str) -> str:
    prompt = GENERATE_PROMPT.format(
        idea_brief=idea_brief, plan_brief=plan_brief, related_work=related_work_text
    )
    return call_llm(
        SYSTEM_PROMPT,
        [{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=DOC_MAX_TOKENS,
    )


def revise(idea_brief: str, plan_brief: str, related_work_text: str, history: list[dict]) -> str:
    system = (
        SYSTEM_PROMPT
        + f"\n\nIdea brief:\n{idea_brief}"
        + f"\n\nPlan brief:\n{plan_brief}"
        + f"\n\nVerified related sources:\n{related_work_text}"
    )
    return call_llm(system, history, temperature=0.4, max_tokens=DOC_MAX_TOKENS)
