import streamlit as st
from agent_runner import run_agent

st.title("🏥 Healthcare Insights Assistant")

query = st.text_input("Ask about a patient (e.g., 'Summarize patient 1')")

if st.button("Run Agent") and query:
    with st.spinner("Running agent..."):
        response = run_agent(query)
        st.markdown("### 🧠 Agent Response")
        st.write(response)