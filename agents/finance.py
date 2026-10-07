"""Finance Agent — turn deals and AI cost into simple investor numbers."""

import json

import streamlit as st

from agents.helper import ask_claude, get_json

# Name used in COST_TRACKER
AGENT_NAME = "Finance Agent"

# We keep 10% of each deal
FEE_RATE = 0.10

SYSTEM_PROMPT = (
    "You are Finance Agent at ZeroDesk, an AI-run company with zero human staff. "
    "You explain numbers simply to investors. Never invent numbers, only use the data given."
)


def report(matches, cost_tracker):
    """Compute fees and profit, then ask Claude for a short investor summary.

    Saves the result in st.session_state["finance"] and returns it.
    """
    deals = _deal_rows(matches)
    n = len(deals)
    total_deal_value = sum(row["deal_value_usd"] for row in deals)
    total_fees = sum(row["fee"] for row in deals)

    ai_cost_per_agent = _agent_costs(cost_tracker)
    total_ai_cost = sum(ai_cost_per_agent.values())

    # Avoid divide by zero when there are no matches
    if n == 0:
        total_deal_value = 0.0
        total_fees = 0.0
        total_ai_cost = 0.0
        profit = 0.0
        ai_cost_per_match = 0.0
        margin_percent = 0.0
        ai_cost_per_agent = {name: 0.0 for name in ai_cost_per_agent}
    else:
        profit = total_fees - total_ai_cost
        ai_cost_per_match = total_ai_cost / n
        margin_percent = (profit / total_fees * 100) if total_fees else 0.0

    numbers = {
        "fee_rate": FEE_RATE,
        "match_count": n,
        "deals": deals,
        "total_deal_value": total_deal_value,
        "total_fees": total_fees,
        "ai_cost_per_agent": ai_cost_per_agent,
        "total_ai_cost": total_ai_cost,
        "profit": profit,
        "ai_cost_per_match": ai_cost_per_match,
        "margin_percent": margin_percent,
    }

    summary, advice = _ask_for_summary(numbers)
    numbers["summary"] = summary
    numbers["advice"] = advice

    st.session_state["finance"] = numbers
    return numbers


def _deal_rows(matches):
    """One row per match: deal value and our 10% fee."""
    rows = []
    if not isinstance(matches, list):
        return rows
    for item in matches:
        if not isinstance(item, dict):
            continue
        value = _as_money(
            item.get("deal_value_usd", item.get("budget_estimate_usd", item.get("budget", 0)))
        )
        rows.append(
            {
                "company": item.get("company", ""),
                "freelancer": item.get("freelancer", ""),
                "deal_value_usd": value,
                "fee": value * FEE_RATE,
            }
        )
    return rows


def _agent_costs(cost_tracker):
    """Map COST_TRACKER rows to {agent_name: cost_usd}."""
    costs = {}
    if not isinstance(cost_tracker, dict):
        return costs
    for name, stats in cost_tracker.items():
        if isinstance(stats, dict):
            # helper.py stores the dollar total as "cost in USD"
            raw = stats.get("cost in USD", stats.get("cost_usd", 0))
        else:
            raw = stats
        costs[str(name)] = _as_money(raw)
    return costs


def _as_money(value):
    """Turn a number or a '$1,234' string into a float."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def _ask_for_summary(numbers):
    """Ask Claude for a 3-sentence summary and 1 sentence of advice."""
    prompt = (
        "Here are ZeroDesk's numbers. Use only these figures. Do not invent any.\n"
        f"{json.dumps(numbers, indent=2, default=str)}\n\n"
        "Return ONLY JSON with:\n"
        '- "summary": exactly 3 sentences for investors\n'
        '- "advice": exactly 1 sentence on what to improve\n'
    )
    reply = ask_claude(
        AGENT_NAME,
        SYSTEM_PROMPT,
        prompt,
        use_web_search=False,
        max_tokens=800,
    )
    data = get_json(reply)
    if isinstance(data, dict):
        summary = str(data.get("summary") or "").strip()
        advice = str(data.get("advice") or "").strip()
        if summary or advice:
            return summary, advice
    # If Claude did not return JSON, keep the raw text as the summary
    return (reply or "").strip(), ""
