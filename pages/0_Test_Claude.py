# This file is a Streamlit *page*. Put it in the pages/ folder and Streamlit
# adds it to the sidebar automatically. The "0_" prefix puts it near the top.

import streamlit as st
import anthropic

from agents.helper import COST_TRACKER, ask_claude
from agents.mailer import send_email
from agents.matching import match
from agents.outreach import write_messages
from agents.talent_scout import find_freelancers

st.title("Test Claude")

# A button the user clicks to send a short prompt to Claude
if st.button("Test Claude"):
    try:
        # Read the API key from Streamlit secrets — never hard-code a key here.
        # Locally it comes from .streamlit/secrets.toml; on Streamlit Cloud,
        # add ANTHROPIC_API_KEY under App settings → Secrets.
        api_key = st.secrets["ANTHROPIC_API_KEY"]

        # The Anthropic client is how Python talks to Claude's API
        client = anthropic.Anthropic(api_key=api_key)

        # messages.create sends the prompt and waits for Claude's reply
        message = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say hello in one sentence"}
            ],
        )

        # Claude's text is in the first content block
        st.write(message.content[0].text)

        # usage tells you how many tokens went in and came out (affects cost)
        st.write(f"Input tokens: {message.usage.input_tokens}")
        st.write(f"Output tokens: {message.usage.output_tokens}")
    except Exception as e:
        # Show any problem (missing key, network error, bad model name, etc.)
        st.error(str(e))

# Same hello prompt, but through the shared helper (tracks cost per agent)
if st.button("Test Helper"):
    try:
        reply = ask_claude(
            "Tester",
            "You are friendly.",
            "Say hello in one sentence",
        )
        st.write(reply)

        # Show one row per agent with tokens, calls, and dollars
        rows = []
        for agent_name, stats in COST_TRACKER.items():
            rows.append({"agent": agent_name, **stats})
        st.table(rows)
    except Exception as e:
        st.error(str(e))

st.divider()
st.header("Test Talent Scout")

# Defaults so Santosh can click the button without typing first
skill = st.text_input("Skill", value="web developer")
location = st.text_input("Location", value="San Francisco")

if st.button("Find Freelancers"):
    try:
        with st.spinner("Finding freelancers..."):
            find_freelancers(skill, location)
    except Exception as e:
        st.error(str(e))

people = st.session_state.get("freelancers")
if people is not None:
    if people:
        # LinkColumn makes profile_url clickable (a plain table cannot)
        st.dataframe(
            people,
            column_config={
                "profile_url": st.column_config.LinkColumn("profile_url"),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No freelancers found.")

    # Cost of the Talent Scout Claude call (and any earlier helper calls)
    cost_rows = []
    for agent_name, stats in COST_TRACKER.items():
        cost_rows.append({"agent": agent_name, **stats})
    if cost_rows:
        st.table(cost_rows)

st.divider()
st.header("Test Matching")

if st.button("Match Now"):
    try:
        with st.spinner("Matching companies and freelancers..."):
            match(
                st.session_state.get("companies"),
                st.session_state.get("freelancers"),
            )
    except Exception as e:
        st.error(str(e))

result = st.session_state.get("matches")
if result is not None:
    matches = result.get("matches") or []
    rejected = result.get("rejected") or []

    if matches:
        # ProgressColumn draws score as a 0-100 bar
        match_rows = []
        for row in matches:
            item = dict(row)
            try:
                item["score"] = int(item.get("score") or 0)
            except (TypeError, ValueError):
                item["score"] = 0
            if isinstance(item.get("reasons"), list):
                item["reasons"] = "; ".join(str(r) for r in item["reasons"])
            match_rows.append(item)
        st.dataframe(
            match_rows,
            column_config={
                "score": st.column_config.ProgressColumn(
                    "score",
                    min_value=0,
                    max_value=100,
                    format="%d",
                ),
                "profile_url": st.column_config.LinkColumn("profile_url"),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No matches.")

    st.subheader("Rejected pairs")
    if rejected:
        st.table(rejected)
    else:
        st.info("No rejected pairs.")

    cost_rows = []
    for agent_name, stats in COST_TRACKER.items():
        cost_rows.append({"agent": agent_name, **stats})
    if cost_rows:
        st.table(cost_rows)

st.divider()
st.header("Test Outreach")

if st.button("Write Messages"):
    try:
        with st.spinner("Writing draft emails..."):
            # Matching saves {"matches": [...], "rejected": [...]}; we want the inner list
            match_result = st.session_state.get("matches")
            inner = None
            if isinstance(match_result, dict):
                inner = match_result.get("matches")
            write_messages(inner)
    except Exception as e:
        st.error(str(e))

drafts = st.session_state.get("outreach")
if drafts is not None:
    if not drafts:
        st.info("No drafts.")
    for i, draft in enumerate(drafts):
        company = draft.get("company", "company")
        freelancer = draft.get("freelancer", "freelancer")
        score = draft.get("score", "")
        title = f"{company} ↔ {freelancer} ({score})"
        with st.expander(title):
            st.markdown("**To the company**")
            st.write(draft.get("company_subject", ""))
            st.write(draft.get("company_body", ""))
            st.markdown("**To the freelancer**")
            st.write(draft.get("freelancer_subject", ""))
            st.write(draft.get("freelancer_body", ""))

            col_ok, col_no = st.columns(2)
            if col_ok.button("Approve", key=f"outreach_approve_{i}"):
                st.session_state["outreach"][i]["status"] = "Approved"
            if col_no.button("Reject", key=f"outreach_reject_{i}"):
                st.session_state["outreach"][i]["status"] = "Rejected"

            # Colored label: green / red / blue for draft
            status = st.session_state["outreach"][i].get("status", "")
            if status == "Approved":
                st.success(status)
            elif status == "Sent (test)":
                st.success(status)
            elif status == "Rejected":
                st.error(status)
            else:
                st.info(status)

            # Only Approved drafts can be sent, and only when Santosh clicks
            if status == "Approved":
                if st.button("Send (test)", key=f"outreach_send_{i}"):
                    try:
                        to_company = send_email(
                            draft.get("company_subject", ""),
                            draft.get("company_body", ""),
                            intended_for=draft.get("company", "company"),
                        )
                        to_freelancer = send_email(
                            draft.get("freelancer_subject", ""),
                            draft.get("freelancer_body", ""),
                            intended_for=draft.get("freelancer", "freelancer"),
                        )
                    except Exception as e:
                        st.error(str(e))
                    else:
                        if to_company is True and to_freelancer is True:
                            st.session_state["outreach"][i]["status"] = "Sent (test)"
                            st.success("Sent (test)")
                        else:
                            # Show each unique error once (both sends often fail the same way)
                            problems = []
                            for result in (to_company, to_freelancer):
                                if result is not True and str(result) not in problems:
                                    problems.append(str(result))
                            for problem in problems:
                                st.error(problem)

    cost_rows = []
    for agent_name, stats in COST_TRACKER.items():
        cost_rows.append({"agent": agent_name, **stats})
    if cost_rows:
        st.table(cost_rows)
