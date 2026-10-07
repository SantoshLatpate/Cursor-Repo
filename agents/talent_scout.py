"""Talent Scout — finds real freelancers from public GitHub profiles."""

import json

import requests
import streamlit as st

from agents.helper import ask_claude, get_json

# Name used in COST_TRACKER
AGENT_NAME = "Talent Scout"

# Exact system prompt for Claude
SYSTEM_PROMPT = (
    "You are Talent Scout, an AI employee at ZeroDesk. "
    "You pick freelancers from public profiles only. "
    "Never use LinkedIn. Never invent people."
)


def find_freelancers(skill, location, count=5):
    """Find `count` real people in `location` who look like a fit for `skill`.

    1. Look up public GitHub users in that location.
    2. Ask Claude to pick the best matches from that list only.
    Saves the JSON list in st.session_state["freelancers"] and returns it.
    """
    profiles = _github_profiles(location)

    prompt = (
        f"Pick the best {count} people for this skill: {skill}.\n"
        "Use only the GitHub profiles below. Never invent people. Never use LinkedIn.\n"
        "Return ONLY a JSON list. Each object must have these keys:\n"
        '- "name": their name (or GitHub login if they have no name)\n'
        '- "profile_url": their GitHub html_url\n'
        '- "skills": short list or string of skills\n'
        '- "location": where they are\n'
        '- "experience_summary": one or two sentences from their public profile\n'
        '- "estimated_rate_usd_per_hour": a number in US dollars per hour\n'
        '- "source": "GitHub"\n\n'
        "GitHub profiles:\n"
        f"{json.dumps(profiles, indent=2)}"
    )

    reply = ask_claude(
        AGENT_NAME,
        SYSTEM_PROMPT,
        prompt,
        use_web_search=False,
        max_tokens=3000,
    )
    data = get_json(reply)
    if not isinstance(data, list):
        data = []

    # Keep only dict rows, and no more than `count` of them
    freelancers = [row for row in data if isinstance(row, dict)][:count]
    for row in freelancers:
        # Claude should set this; fill it in if a row is missing it
        if not row.get("source"):
            row["source"] = "GitHub"

    st.session_state["freelancers"] = freelancers
    return freelancers


def _optional_github_token():
    """Use a GitHub token from secrets if one is already there. Do not require it."""
    for name in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_API_KEY"):
        try:
            value = st.secrets[name]
        except Exception:
            continue
        if value:
            return str(value).strip()
    return None


def _github_profiles(location):
    """Search GitHub users, then load details for the first 10.

    If GitHub fails, warn in the app and return an empty list so Claude can still run.
    """
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ZeroDesk-TalentScout",
        }
        token = _optional_github_token()
        if token:
            headers["Authorization"] = "Bearer " + token

        # location:"San Francisco" repos:>5  — people in that city with more than 5 repos
        search = requests.get(
            "https://api.github.com/search/users",
            params={
                "q": f'location:"{location}" repos:>5',
                "per_page": 10,
            },
            headers=headers,
            timeout=20,
        )
        search.raise_for_status()
        items = (search.json() or {}).get("items") or []

        profiles = []
        for item in items[:10]:
            login = item.get("login")
            if not login:
                continue
            detail = requests.get(
                f"https://api.github.com/users/{login}",
                headers=headers,
                timeout=20,
            )
            if detail.status_code != 200:
                continue
            data = detail.json() or {}
            profiles.append(
                {
                    "name": data.get("name"),
                    "login": data.get("login"),
                    "bio": data.get("bio"),
                    "blog": data.get("blog"),
                    "html_url": data.get("html_url"),
                    "public_repos": data.get("public_repos"),
                    "hireable": data.get("hireable"),
                    "location": data.get("location"),
                }
            )
        return profiles
    except Exception as e:
        st.warning(f"GitHub search failed ({e}). Continuing with an empty list.")
        return []
