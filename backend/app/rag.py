"""
Lightweight RAG layer: searches real external sources for work related to a
student's idea. We query live APIs at request time rather than maintaining
our own embeddings index — retrieval without a local vector DB.

- Semantic Scholar: free API, no key required for light usage.
- GitHub: free API, unauthenticated search is rate-limited (~10 req/min).
  Set GITHUB_TOKEN in .env to raise that limit if you hit it during testing.
"""

import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # optional


def search_papers(query: str, limit: int = 3) -> list[dict]:
    try:
        resp = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={"query": query, "limit": limit, "fields": "title,abstract,url,year"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("data", []) or []
    except requests.RequestException:
        # Search is best-effort — if the API is down or rate-limited,
        # the pipeline should degrade gracefully, not crash the request.
        return []


def search_repos(query: str, limit: int = 3) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "per_page": limit},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("items", []) or []
    except requests.RequestException:
        return []


def gather_related_work(query: str, limit: int = 3) -> dict:
    return {
        "papers": search_papers(query, limit=limit),
        "repos": search_repos(query, limit=limit),
    }


def format_related_work(related: dict) -> str:
    """Renders search results as Markdown — shown to the student and fed
    as grounding context into the Feasibility and Documentation agents."""
    papers = related.get("papers", [])
    repos = related.get("repos", [])

    lines = ["**Related Academic Papers:**"]
    if papers:
        for p in papers:
            title = p.get("title", "Untitled")
            year = p.get("year", "n.d.")
            url = p.get("url", "")
            lines.append(f"- [{title}]({url}) ({year})")
    else:
        lines.append("- No closely related papers found via search.")

    lines.append("")
    lines.append("**Related GitHub Repositories:**")
    if repos:
        for r in repos:
            name = r.get("full_name", "unknown/repo")
            url = r.get("html_url", "")
            stars = r.get("stargazers_count", 0)
            desc = r.get("description") or "No description."
            lines.append(f"- [{name}]({url}) (\u2605 {stars}) \u2014 {desc}")
    else:
        lines.append("- No closely related repositories found via search.")

    return "\n".join(lines)


def extract_search_query(idea_brief: str) -> str:
    """Pulls a search-friendly query out of the structured idea brief.
    Falls back to the first chunk of text if no 'Title:' line is found."""
    for line in idea_brief.splitlines():
        if line.strip().lower().startswith("title:"):
            return line.split(":", 1)[1].strip()
    return idea_brief.strip()[:150]
