"""Streamlit chat page.  Run:  streamlit run ui.py --server.port 8503"""
import requests
import streamlit as st

import config

st.set_page_config(page_title="Harbor Trust Bank Assistant", page_icon="🏦")
st.title("🏦 Harbor Trust Bank – Support Assistant")
st.caption("Local RAG lab: llama3.1 + pgvector. Guardrails OFF leaks data on purpose.")

with st.sidebar:
    user_id = st.selectbox("Logged in as (user_id)", ["cust_001", "cust_002", "guest"])
    guardrails_on = st.toggle("Guardrails", value=config.GUARDRAILS_DEFAULT)
    st.write(f"API: `{config.API_URL}`")
    if st.button("Clear chat"):
        st.session_state.history = []

if "history" not in st.session_state:
    st.session_state.history = []

for turn in st.session_state.history:
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        st.write(turn["answer"])
        st.caption(turn["meta"])

question = st.chat_input("Ask a banking question...")
if question:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            resp = requests.post(
                f"{config.API_URL}/chat",
                json={"user_id": user_id, "message": question},
                headers={"X-Guardrails": "on" if guardrails_on else "off"},
                timeout=300,
            )
            data = resp.json()
        sources = ", ".join(s["source"] for s in data["sources"]) or "(none)"
        meta = f"user: {user_id} · guardrails: {data['guardrails']} · sources: {sources}"
        if data.get("blocked"):
            meta += " · BLOCKED by input filter"
        st.write(data["answer"])
        st.caption(meta)
    st.session_state.history.append({"question": question, "answer": data["answer"], "meta": meta})
