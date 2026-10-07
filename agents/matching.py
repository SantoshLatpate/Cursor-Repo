"""Matching Agent — pairs businesses with freelancers and rejects bad fits."""

import json

import streamlit as st

from agents.helper import ask_claude, get_json

# Name used in COST_TRACKER
AGENT_NAME = "Matching Agent"

# Exact system prompt for Claude
SYSTEM_PROMPT = (
    "You are Matching Agent, an AI employee at ZeroDesk. "
    "You match small businesses with freelancers. Be honest. "
    "Reject bad matches and explain why."
)

def match(companies, freelancers):
    """Pick the best freelancer for each company. Return matches and rejections.

    Saves the JSON in st.session_state["matches"] and returns it.
    If either list is empty, warn and return empty matches/rejected.
    """
    if not companies or not freelancers:
        st.warning("Run Company Scout and Talent Scout first")
        result = {"matches": [], "rejected": []}
        st.session_state["matches"] = result
        return result

    prompt = (
        "Here are two JSON lists: companies and freelancers.\n"
        "For each company, pick the best freelancer from the list.\n"
        "Give a score from 0 to 100 using: skills fit 40%, past work 30%, "
        "budget fit 20%, location 10%.\n"
        "Give 2-3 short reasons for each match.\n"
        "Also list rejected pairs with a reason (at least 1 rejection).\n"
        "deal_value_usd must be that company's budget_estimate_usd "
        "(use budget_estimate_usd or budget from the company).\n"
        "Return ONLY JSON in this shape:\n"
        '{"matches": [{"company", "freelancer", "profile_url", "score", '
        '"reasons", "deal_value_usd"}],\n'
        ' "rejected": [{"company", "freelancer", "reason"}]}\n\n'
        "companies:\n"
        f"{json.dumps(companies, indent=2, default=str)}\n\n"
        "freelancers:\n"
        f"{json.dumps(freelancers, indent=2, default=str)}"
    )

    reply = ask_claude(
        AGENT_NAME,
        SYSTEM_PROMPT,
        prompt,
        use_web_search=False,
        max_tokens=4000,
    )
    data = get_json(reply)
    result = _normalize_result(data)
    st.session_state["matches"] = result
    return result


def _normalize_result(data):
    """Turn Claude's JSON into {matches: [...], rejected: [...]}."""
    if not isinstance(data, dict):
        return {"matches": [], "rejected": []}

    matches = data.get("matches")
    rejected = data.get("rejected")
    if not isinstance(matches, list):
        matches = []
    if not isinstance(rejected, list):
        rejected = []

    return {
        "matches": [row for row in matches if isinstance(row, dict)],
        "rejected": [row for row in rejected if isinstance(row, dict)],
    }
