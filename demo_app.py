"""Zero Human Match — Streamlit hackathon demo.

Most pages use sample data. Company Scout can run a real search.
"""

import time
import streamlit as st

from agents.company_scout import find_companies

st.set_page_config(page_title="Zero Human Match", page_icon="⚡", layout="wide")

# --- Sample data (all fictional) ---
JOBS = [
    {
        "company": "Bright Smile Dental Clinic",
        "need": "New website",
        "budget": "$2,500",
        "source": "Outdated website",
    },
    {
        "company": "Mission Street Coffee",
        "need": "Logo and menu design",
        "budget": "$800",
        "source": "Job post",
    },
    {
        "company": "Sunset Yoga Studio",
        "need": "Social media content",
        "budget": "$600 per month",
        "source": "Funding news",
    },
]

FREELANCERS = [
    {
        "name": "Maya Chen",
        "skill": "Web developer",
        "rate": "$45/hr",
        "experience": "Built 2 clinic websites",
        "source": "GitHub",
    },
    {
        "name": "Leo Martins",
        "skill": "Graphic designer",
        "rate": "$40/hr",
        "experience": "Logos and branding",
        "source": "Portfolio site",
    },
    {
        "name": "Priya Shah",
        "skill": "Social media manager",
        "rate": "$35/hr",
        "experience": "Wellness brands",
        "source": "Sign-up form",
    },
    {
        "name": "Sam Okafor",
        "skill": "Full-stack developer",
        "rate": "$120/hr",
        "experience": "Senior full-stack (too expensive)",
        "source": "GitHub",
    },
    {
        "name": "Ana Lopez",
        "skill": "Illustrator",
        "rate": "—",
        "experience": "Children's books only",
        "source": "Portfolio site",
    },
]

ACCEPTED = [
    "91% match - Maya Chen -> Bright Smile Dental Clinic - built 2 clinic websites, within budget",
    "87% match - Leo Martins -> Mission Street Coffee - logo and branding expert, within budget",
    "84% match - Priya Shah -> Sunset Yoga Studio - wellness brand experience",
]

REJECTED = [
    "Rejected: Sam Okafor -> Bright Smile Dental - rate $120/hr is over budget",
    "Rejected: Ana Lopez -> Mission Street Coffee - children's illustration only, no logo work",
]

# Deal values and the company's 10% fee
DEALS = [
    {"deal": "Maya Chen × Bright Smile Dental Clinic", "value": 2500, "fee": 250},
    {"deal": "Leo Martins × Mission Street Coffee", "value": 800, "fee": 80},
    {"deal": "Priya Shah × Sunset Yoga Studio", "value": 600, "fee": 60},
]

# Fake AI run costs (no real models)
AI_COSTS = [
    {"agent": "Company Scout", "cost": 0.08},
    {"agent": "Talent Scout", "cost": 0.05},
    {"agent": "Matching", "cost": 0.15},
    {"agent": "Outreach", "cost": 0.10},
    {"agent": "Finance & Analyst", "cost": 0.02},
]

TOTAL_FEES = sum(d["fee"] for d in DEALS)
TOTAL_AI = round(sum(a["cost"] for a in AI_COSTS), 2)
PROFIT = round(TOTAL_FEES - TOTAL_AI, 2)

AGENTS = [
    {
        "emoji": "🔭",
        "name": "Company Scout",
        "job": "Finds businesses that need work",
    },
    {
        "emoji": "🧑‍💻",
        "name": "Talent Scout",
        "job": "Finds freelancers for the jobs",
    },
    {
        "emoji": "🔗",
        "name": "Matching",
        "job": "Pairs jobs with talent",
    },
    {
        "emoji": "✉️",
        "name": "Outreach",
        "job": "Drafts intros to both sides",
    },
    {
        "emoji": "💹",
        "name": "Finance & Analyst",
        "job": "Tracks fees, cost, and profit",
    },
]

# One-by-one run log (shown live on Overview)
RUN_STEPS = [
    ("Company Scout", "Company Scout found 3 jobs -> handing off to Matching"),
    ("Talent Scout", "Talent Scout found 5 freelancers -> handing off to Matching"),
    ("Matching", "Matching made 3 matches (2 rejected) -> handing off to Outreach"),
    ("Outreach", "Outreach drafted 6 messages -> handing off to Finance"),
    ("Finance & Analyst", "Finance logged 3 deals and $389.60 profit -> done"),
]

OUTREACH = [
    {
        "title": "Maya Chen ↔ Bright Smile Dental Clinic",
        "business": (
            "Hi Bright Smile team — I'm an AI at Zero Human Match (no human staff). "
            "Your site looks dated, so we found Maya Chen, a web developer who has "
            "already built 2 clinic websites and can work within your $2,500 budget. "
            "Want an intro? Reply STOP and we will not contact you again."
        ),
        "freelancer": (
            "Hi Maya — I'm an AI at Zero Human Match. Bright Smile Dental Clinic needs "
            "a new website ($2,500 budget). Your two clinic sites look like a strong fit. "
            "Interested in an intro? Reply STOP and we will not contact you again."
        ),
    },
    {
        "title": "Leo Martins ↔ Mission Street Coffee",
        "business": (
            "Hi Mission Street Coffee — I'm an AI at Zero Human Match (no human staff). "
            "We saw your job post for a logo and menu design and found Leo Martins, "
            "a branding designer who can stay within $800. Want us to connect you? "
            "Reply STOP and we will not contact you again."
        ),
        "freelancer": (
            "Hi Leo — I'm an AI at Zero Human Match. Mission Street Coffee needs a logo "
            "and menu design ($800 budget). Your branding work looks like a great match. "
            "Shall we intro you? Reply STOP and we will not contact you again."
        ),
    },
    {
        "title": "Priya Shah ↔ Sunset Yoga Studio",
        "business": (
            "Hi Sunset Yoga — I'm an AI at Zero Human Match (no human staff). "
            "We noticed your funding news and thought you might want social content. "
            "Priya Shah manages wellness brands at $35/hr, within $600/month. "
            "Open to a chat? Reply STOP and we will not contact you again."
        ),
        "freelancer": (
            "Hi Priya — I'm an AI at Zero Human Match. Sunset Yoga Studio needs ongoing "
            "social content ($600/month). Your wellness-brand experience is the reason "
            "we reached out. Want an intro? Reply STOP and we will not contact you again."
        ),
    },
]


def init_state():
    if "ran" not in st.session_state:
        st.session_state.ran = False
        st.session_state.logs = []
        st.session_state.statuses = {a["name"]: "Idle" for a in AGENTS}
    # None means we have not run a real search yet (show demo rows)
    if "company_scout_results" not in st.session_state:
        st.session_state.company_scout_results = None


def banner():
    st.markdown(
        """
        <div style="background:#FFE566;border:1px solid #E0C200;padding:10px 16px;
                    border-radius:8px;text-align:center;font-weight:700;color:#5C4D00;
                    margin-bottom:8px;">
            DEMO MODE - sample data
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str):
    if status == "Done":
        st.success(status)
    elif status == "Working":
        st.warning(status)
    else:
        st.info(status)


def draw_agent_cards(holders):
    for i, agent in enumerate(AGENTS):
        status = st.session_state.statuses[agent["name"]]
        with holders[i].container(border=True):
            st.markdown(f"{agent['emoji']} **{agent['name']}**")
            st.caption(agent["job"])
            status_badge(status)


def money(n: float) -> str:
    n = round(float(n), 2)
    if n == int(n):
        return f"${int(n):,}"
    return f"${n:,.2f}"


def page_overview():
    st.title("Zero Human Match")
    st.write(
        "AI agents doing business with AI agents. A company with zero human staff "
        "that connects work and workers in minutes."
    )
    st.caption("Five AI employees")

    cols = st.columns(5)
    holders = [c.empty() for c in cols]
    draw_agent_cards(holders)

    st.markdown("**Flow:** Company Scout + Talent Scout → Matching → Outreach → Finance")

    m1, m2, m3, m4 = st.columns(4)
    if st.session_state.ran:
        m1.metric("Jobs found", 3)
        m2.metric("Freelancers found", 5)
        m3.metric("Matches made", 3)
        m4.metric("Profit", money(PROFIT))
    else:
        m1.metric("Jobs found", 0)
        m2.metric("Freelancers found", 0)
        m3.metric("Matches made", 0)
        m4.metric("Profit", "$0")

    st.divider()
    run = st.button("Run all 5 agents", type="primary", use_container_width=True)

    progress_slot = st.empty()
    if st.session_state.ran:
        progress_slot.progress(1.0)

    log_box = st.container(border=True)
    log_box.markdown("**Live log**")
    log_slot = log_box.empty()
    if st.session_state.logs:
        log_slot.markdown("\n".join(f"- {line}" for line in st.session_state.logs))
    else:
        log_slot.caption("Click the button to run the five AI employees.")

    if run:
        st.session_state.logs = []
        st.session_state.statuses = {a["name"]: "Idle" for a in AGENTS}
        st.session_state.ran = False
        draw_agent_cards(holders)
        progress = progress_slot.progress(0)

        for i, (name, msg) in enumerate(RUN_STEPS):
            st.session_state.statuses[name] = "Working"
            draw_agent_cards(holders)
            time.sleep(1)
            st.session_state.statuses[name] = "Done"
            st.session_state.logs.append(msg)
            log_slot.markdown("\n".join(f"- {line}" for line in st.session_state.logs))
            progress.progress((i + 1) / len(RUN_STEPS))
            draw_agent_cards(holders)

        st.session_state.ran = True
        st.rerun()


def page_company_scout():
    st.title("Company Scout")
    st.write("Finds small businesses that need freelance work.")

    # Short inputs: where to look, what they need, how many to return
    col_loc, col_need, col_count = st.columns(3)
    with col_loc:
        location = st.text_input("Location", placeholder="San Francisco")
    with col_need:
        need = st.text_input("Need", placeholder="new website")
    with col_count:
        count = st.number_input("Count", min_value=1, max_value=20, value=5, step=1)

    if st.button("Find companies", type="primary"):
        if not str(location).strip() or not str(need).strip():
            st.error("Please type a location and a need first.")
        else:
            try:
                # Calls Querit first, then Claude web search if Querit fails
                with st.spinner("Searching for real businesses..."):
                    results = find_companies(
                        str(location).strip(),
                        str(need).strip(),
                        int(count),
                    )
                st.session_state.company_scout_results = results
            except Exception as e:
                # Missing API key, network error, bad reply, etc.
                st.error(str(e))

    results = st.session_state.company_scout_results
    if results is None:
        # No real search yet — keep the old sample table, labeled as demo
        st.caption("Sample rows below are demo-only. Click Find companies for a real search.")
        st.table(JOBS)
        return

    if not results:
        st.info("No businesses found. Try another location or need.")
        return

    # Table includes the Source field on every row
    st.table(results)

    # Cards make the URL and Source easy to read
    for biz in results:
        with st.container(border=True):
            st.markdown(f"**{biz.get('company', 'Unknown company')}**")
            st.write(f"Need: {biz.get('need', '')}")
            st.write(f"Budget: {biz.get('budget', '')}")
            url = biz.get("url") or ""
            if url:
                st.write(url)
            why = biz.get("why") or ""
            if why:
                st.caption(why)
            st.info(biz.get("source", ""))


def page_talent_scout():
    st.title("Talent Scout")
    st.write("Finds freelancers who can do the work.")
    st.table(FREELANCERS)


def page_matching():
    st.title("Matching")
    st.write("Pairs each job with the best freelancer. Two candidates are rejected.")
    for line in ACCEPTED:
        st.success(line)
    for line in REJECTED:
        st.error(line)


def page_outreach():
    st.title("Outreach")
    st.info("Draft only - a human approves before sending")
    for i, draft in enumerate(OUTREACH):
        with st.container(border=True):
            st.subheader(draft["title"])
            left, right = st.columns(2)
            with left:
                st.markdown("**To the business**")
                st.write(draft["business"])
            with right:
                st.markdown("**To the freelancer**")
                st.write(draft["freelancer"])
            st.button("Send", disabled=True, key=f"send_{i}")


def page_finance():
    st.title("Finance & Analyst")
    st.write("The company earns a 10% fee per deal. AI costs are fake demo numbers.")

    deal_rows = [
        {
            "deal": d["deal"],
            "deal value": money(d["value"]),
            "10% fee earned": money(d["fee"]),
        }
        for d in DEALS
    ]
    cost_rows = [
        {"agent": a["agent"], "AI cost": f"${a['cost']:.2f}"} for a in AI_COSTS
    ]

    st.subheader("Deals")
    st.table(deal_rows)

    st.subheader("AI cost per agent")
    st.table(cost_rows)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total fees", money(TOTAL_FEES))
    c2.metric("Total AI cost", f"${TOTAL_AI:.2f}")
    c3.metric("Profit", money(PROFIT))

    st.subheader("Analyst report")
    st.markdown(
        "- Clinic websites have the highest fee\n"
        "- Matching agent costs the most, try a smaller model\n"
        "- Next: get more freelancers from the sign-up form"
    )


init_state()
banner()

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Company Scout",
        "Talent Scout",
        "Matching",
        "Outreach",
        "Finance & Analyst",
    ],
)

if page == "Overview":
    page_overview()
elif page == "Company Scout":
    page_company_scout()
elif page == "Talent Scout":
    page_talent_scout()
elif page == "Matching":
    page_matching()
elif page == "Outreach":
    page_outreach()
else:
    page_finance()
