# This file is a Streamlit *page*. Put it in the pages/ folder and Streamlit
# adds it to the sidebar automatically. The "0_" prefix puts it near the top.

import streamlit as st
import anthropic

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
