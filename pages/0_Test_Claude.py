# This file is a Streamlit *page*. Put it in the pages/ folder and Streamlit
# adds it to the sidebar automatically. The "0_" prefix puts it near the top.

import streamlit as st
import anthropic

from agents.helper import COST_TRACKER, ask_claude
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
