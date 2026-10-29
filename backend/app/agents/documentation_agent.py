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
- Follow the word-count target given for each section in the plan brief as closely as possible,
  but the TOTAL document must not exceed roughly 1800-2000 words combined across all sections —
  if the plan brief's targets sum to more than that, scale every section down proportionally
  rather than exceeding the cap. This keeps each request within the API's per-call token limit.
- Use the word-count targets only as an internal guide. NEVER print them in the document: no "(≈ 150 words)", "(~150 words)" or similar annotations under or beside any heading.
- In the Literature Review, you MUST only cite from the verified sources list provided below —
  discuss each one specifically (what it does, how this project differs from or builds on it).
  NEVER invent a citation, statistic, or paper that is not in the verified list. If the verified
  list is thin, say so explicitly rather than fabricating additional sources — you can still
  describe general areas worth researching further without attaching a fake citation to them.
- When citing, use the exact title and include the URL in parentheses, e.g.
  "Smith et al., 'Paper Title' (https://...)."
- When asked to revise, apply ONLY the requested change to the document you are given, and
  return the FULL updated document again in the same Markdown format — do not shrink or drop
  unrelated sections.
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

REVISE_PROMPT = """Here is the current document:

{current_doc}

Requested change: {user_request}

Apply this change and return the FULL updated document in the same Markdown format.
"""

# Keep this comfortably under Groq's free-tier 8000-tokens-per-request cap (prompt + output
# combined). A ~2000-word document is roughly 2700 tokens, leaving headroom for the input side.
DOC_MAX_TOKENS = 3000


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


def revise(idea_brief: str, plan_brief: str, related_work_text: str, current_doc: str, user_request: str) -> str:
    """
    Deliberately does NOT take the full chat history — only the current document and the
    newest edit request. Feeding the whole history (every past full draft) back in on every
    revision was what caused requests to balloon past Groq's per-request token limit.
    """
    system = (
        SYSTEM_PROMPT
        + f"\n\nIdea brief:\n{idea_brief}"
        + f"\n\nPlan brief:\n{plan_brief}"
        + f"\n\nVerified related sources:\n{related_work_text}"
    )
    prompt = REVISE_PROMPT.format(current_doc=current_doc, user_request=user_request)
    return call_llm(
        system, [{"role": "user", "content": prompt}], temperature=0.4, max_tokens=DOC_MAX_TOKENS
    )
