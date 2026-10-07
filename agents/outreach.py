"""Outreach Agent — drafts intro emails. Never sends them."""

import json

import streamlit as st

from agents.helper import ask_claude, get_json

# Name used in COST_TRACKER
AGENT_NAME = "Outreach Agent"

# Exact system prompt for Claude
SYSTEM_PROMPT = (
    "You are Outreach Agent, an AI employee at ZeroDesk, an AI-run company "
    "that connects small businesses with freelancers. Write short, honest, "
    "friendly emails. Always say ZeroDesk is AI-run. Never make promises "
    "about price or results. Always include the line: "
    "'Reply STOP if you do not want more messages.'"
)

DRAFT_STATUS = "Draft - needs approval"


def write_messages(matches):
    """Draft company and freelancer emails for each match. Do not send them.

    `matches` is the inner list from st.session_state["matches"]["matches"].
    Saves the JSON list in st.session_state["outreach"] and returns it.
    """
    # Empty or missing list — Matching has not produced pairs yet
    if not isinstance(matches, list) or not matches:
        st.warning("Run Matching first")
        st.session_state["outreach"] = []
        return []

    prompt = (
        "Here is a JSON list of accepted matches. For each match, write two emails.\n"
        "email_to_company: subject + body (under 120 words). Introduce the freelancer "
        "and why they fit.\n"
        "email_to_freelancer: subject + body (under 120 words). Introduce the job "
        "and the company.\n"
        "Always say ZeroDesk is AI-run. Never promise a price or a result. "
        "Always include this exact line in both bodies: "
        "'Reply STOP if you do not want more messages.'\n"
        "Return ONLY a JSON list. Each object must have:\n"
        '- "company"\n'
        '- "freelancer"\n'
        '- "score"\n'
        '- "company_subject"\n'
        '- "company_body"\n'
        '- "freelancer_subject"\n'
        '- "freelancer_body"\n'
        f'- "status": "{DRAFT_STATUS}"\n\n'
        "matches:\n"
        f"{json.dumps(matches, indent=2, default=str)}"
    )

    reply = ask_claude(
        AGENT_NAME,
        SYSTEM_PROMPT,
        prompt,
        use_web_search=False,
        max_tokens=4000,
    )
    data = get_json(reply)
    if not isinstance(data, list):
        data = []

    drafts = [row for row in data if isinstance(row, dict)]
    for row in drafts:
        # These are drafts only — a human must approve before anything is sent
        if not row.get("status"):
            row["status"] = DRAFT_STATUS

    st.session_state["outreach"] = drafts
    return drafts
