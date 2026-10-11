"""TollgateRAG demo.  Run:  streamlit run app.py"""

import streamlit as st

from tollgaterag import config
from tollgaterag.pipeline import run_query
from tollgaterag.provenance import load_review_queue

st.set_page_config(page_title="TollgateRAG", page_icon="🚧", layout="wide")
st.title("🚧 TollgateRAG")
st.caption("Per-source risk gating with unauthorized-authority-claim and verified-anchor conflict detection")

with st.sidebar:
    st.header("Policy profile")
    profile = st.selectbox("Gate strictness", list(config.PROFILES), index=1)
    config.REJECT_THRESHOLD = config.PROFILES[profile]["reject"]
    config.WARN_THRESHOLD = config.PROFILES[profile]["warn"]
    st.caption(f"reject ≥ {config.REJECT_THRESHOLD}  |  warn ≥ {config.WARN_THRESHOLD}")
    st.divider()
    st.markdown("**Try these**")
    st.code("What's the real travel policy, is there an unlimited allowance?")
    st.code("Is two-factor authentication required?")
    st.code("Do I need approval for travel to high-risk countries?")
    st.code("What is the daily meal budget for business trips?")
    st.caption("The last one hits a known limitation (an evasive document with no cue words).")
    st.divider()
    st.write("**LLM:** " + ("✅ connected" if config.LLM_BASE_URL else "⚠️ offline extractive mode"))

query = st.text_input("Ask about the sample company policy documents:")
if st.button("Run", type="primary") and query:
    with st.spinner("Retrieving, scoring, gating..."):
        res = run_query(query)

    tab1, tab2, tab3 = st.tabs(["Answer & gate decisions", "Review queue", "Raw provenance"])
    with tab1:
        st.subheader("Answer")
        st.write(res["answer"])
        st.caption(f"Latency {res['latency_ms']:.0f} ms")
        st.subheader("Gate decisions")
        for r in res["reports"]:
            icon = {"accept": "🟢", "warn": "🟡", "reject": "🔴"}[r.decision]
            with st.expander(f"{icon} {r.decision.upper()}  risk={r.overall_risk:.2f} — {r.title}"):
                st.bar_chart(r.sub_scores)
                for reason in r.reasons:
                    st.write(f"- {reason}")
    with tab2:
        st.write("Rejected / warned documents waiting for a human decision (logs/review_queue.jsonl).")
        q = load_review_queue()
        st.dataframe([{k: x[k] for k in ("title", "decision", "overall_risk", "status", "query")}
                      for x in q[-50:]] or [])
    with tab3:
        st.json(res["provenance_record"])
