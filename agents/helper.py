"""Helpers for calling Claude and tracking how much each agent costs."""

import json
import re

import anthropic
import streamlit as st

# Which Claude model every agent uses
MODEL = "claude-sonnet-5-5"

# Dollars per 1 million tokens. check anthropic.com/pricing and update
PRICE_INPUT_PER_MILLION = 3.0
PRICE_OUTPUT_PER_MILLION = 15.0

# Running totals for each agent name:
#   input tokens, output tokens, number of calls, cost in USD
COST_TRACKER = {}


def ask_claude(agent_name, system, prompt, use_web_search=False, max_tokens=2000):
    """Send one prompt to Claude and return the text reply.

    agent_name: label for the cost tracker, for example "Tester"
    system: instructions that tell Claude how to behave
    prompt: the user message
    use_web_search: if True, Claude may search the web (up to 3 searches)
    max_tokens: longest reply we will accept
    """
    # Read the key from Streamlit secrets — never put a key in this file
    api_key = st.secrets["ANTHROPIC_API_KEY"]
    client = anthropic.Anthropic(api_key=api_key)

    request = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }

    # Optional web search tool (Claude can search up to 3 times)
    if use_web_search:
        request["tools"] = [
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3,
            }
        ]

    message = client.messages.create(**request)

    # Claude can return several blocks; keep only the text ones and glue them
    parts = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    reply = "".join(parts)

    # Add this call's tokens and dollar cost to COST_TRACKER
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    cost = (
        input_tokens / 1_000_000 * PRICE_INPUT_PER_MILLION
        + output_tokens / 1_000_000 * PRICE_OUTPUT_PER_MILLION
    )

    if agent_name not in COST_TRACKER:
        COST_TRACKER[agent_name] = {
            "input tokens": 0,
            "output tokens": 0,
            "number of calls": 0,
            "cost in USD": 0.0,
        }

    COST_TRACKER[agent_name]["input tokens"] += input_tokens
    COST_TRACKER[agent_name]["output tokens"] += output_tokens
    COST_TRACKER[agent_name]["number of calls"] += 1
    COST_TRACKER[agent_name]["cost in USD"] += cost

    return reply


def get_json(text):
    """Find a JSON list or object in Claude's reply.

    Works if the JSON sits inside ```json fences, or is mixed with other words.
    Returns Python data (a list or a dict), or None if no JSON is found.
    """
    if not text:
        return None

    # Try the fenced block first, then the whole reply
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    pieces = []
    if fenced:
        pieces.append(fenced.group(1).strip())
    pieces.append(text)

    decoder = json.JSONDecoder()
    for piece in pieces:
        # JSON we want starts with { (object) or [ (list)
        start_obj = piece.find("{")
        start_list = piece.find("[")
        starts = [i for i in (start_obj, start_list) if i != -1]
        if not starts:
            continue
        start = min(starts)
        try:
            # raw_decode reads JSON even if extra text comes after it
            data, _ = decoder.raw_decode(piece[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(data, (list, dict)):
            return data

    return None


def reset_costs():
    """Clear COST_TRACKER so a new run starts at zero."""
    COST_TRACKER.clear()
