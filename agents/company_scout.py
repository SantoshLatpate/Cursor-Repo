"""Company Scout — finds real small businesses that need freelance work."""

from agents.helper import ask_claude, get_json
import streamlit as st

# Name used in COST_TRACKER
AGENT_NAME = "Company Scout"

# Labels stamped onto each result so the table shows where it came from
SOURCE_QUERIT = "Source: Querit"
SOURCE_CLAUDE_WEB = "Source: Claude web search"

# JSON keys we always ask Claude to return (same list for both search paths)
BUSINESS_JSON_KEYS = (
    "company",  # business name
    "need",  # what they need help with
    "budget",  # budget if known, otherwise "unknown"
    "url",  # page we found them on
    "why",  # short reason they look like a real lead
)


def find_companies(location, need, count=5):
    """Find `count` real businesses in `location` that look like they need `need`.

    Tries Querit search first. If the Querit key is missing or Querit fails,
    falls back to Claude's built-in web search.
    Returns a list of dicts (company, need, budget, url, why, source).
    """
    try:
        hits = _search_querit(location, need)
        if not hits:
            raise RuntimeError("Querit returned no results")
        businesses = _pick_with_claude(location, need, count, hits, use_web_search=False)
        if not businesses:
            raise RuntimeError("Claude returned no businesses from Querit hits")
        return _add_source(businesses, SOURCE_QUERIT)
    except Exception:
        # Missing key, missing package, network error, empty results, etc.
        businesses = _pick_with_claude(location, need, count, hits=None, use_web_search=True)
        return _add_source(businesses, SOURCE_CLAUDE_WEB)


def _search_querit(location, need):
    """Run 3 Querit searches and collect title, url, snippet from each."""
    from querit import QueritClient
    from querit.models.request import SearchRequest

    # Read the key from Streamlit secrets — never put a key in this file
    client = QueritClient(api_key="Bearer " + st.secrets["QUERIT_API_KEY"])

    queries = [
        f"{location} small business hiring {need}",
        f"{location} new business needs {need}",
        f"{location} {need} job post",
    ]

    hits = []
    seen_urls = set()
    for query in queries:
        request = SearchRequest(query=query, count=10)
        response = client.search(request)
        for item in response.results:
            title = getattr(item, "title", None) or ""
            url = getattr(item, "url", None) or ""
            snippet = getattr(item, "snippet", None) or ""
            if not title and not url:
                continue
            # Skip duplicate URLs so Claude does not see the same page 3 times
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            hits.append({"title": title, "url": url, "snippet": snippet})
    return hits


def _pick_with_claude(location, need, count, hits, use_web_search):
    """Ask Claude to pick the best `count` real businesses as a JSON list."""
    system = (
        "You find real small businesses that need freelance work. "
        "Only use real companies. Never invent names or URLs. "
        "Reply with JSON only."
    )
    prompt = _build_prompt(location, need, count, hits, use_web_search)
    reply = ask_claude(
        AGENT_NAME,
        system,
        prompt,
        use_web_search=use_web_search,
        max_tokens=3000,
    )
    data = get_json(reply)
    if not isinstance(data, list):
        return []
    # Keep only dict rows, and no more than `count` of them
    businesses = [row for row in data if isinstance(row, dict)]
    return businesses[:count]


def _build_prompt(location, need, count, hits, use_web_search):
    """Build the Claude prompt. Same JSON shape for Querit and web-search paths."""
    json_rules = (
        f"Pick the best {count} real businesses in {location} that need help with: {need}.\n"
        "Return ONLY a JSON list. Each object must have these keys:\n"
        '- "company": business name\n'
        '- "need": what they need help with\n'
        '- "budget": budget if known, otherwise "unknown"\n'
        '- "url": the page URL\n'
        '- "why": one short reason they look like a real lead\n'
        "Skip directories, ads, and anything that is not a real business."
    )

    if use_web_search:
        return (
            "Search the web for small businesses that are hiring, newly opened, "
            f"or posting a job for {need} in {location}.\n\n"
            + json_rules
        )

    # Querit already searched; we only ask Claude to rank those hits
    lines = []
    for i, hit in enumerate(hits, start=1):
        lines.append(
            f"{i}. Title: {hit.get('title', '')}\n"
            f"   URL: {hit.get('url', '')}\n"
            f"   Snippet: {hit.get('snippet', '')}"
        )
    results_text = "\n".join(lines) if lines else "(no search results)"
    return (
        "Here are web search results. Use only these pages — do not invent businesses.\n\n"
        f"{results_text}\n\n"
        + json_rules
    )


def _add_source(businesses, source_label):
    """Copy the list and set source on every row (Querit or Claude web search)."""
    labeled = []
    for row in businesses:
        item = dict(row)
        item["source"] = source_label
        labeled.append(item)
    return labeled
