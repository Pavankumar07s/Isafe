"""EthicsGuard v0.4 Dashboard — Streamlit entrypoint."""
import streamlit as st

st.set_page_config(
    page_title="EthicsGuard v0.4 Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("EthicsGuard v0.4 — AI Safety Dashboard")
st.markdown("Navigate using the sidebar to access different views.")
st.markdown("""
### Quick Links
- **Scorecard** — Real-time trustworthiness scores
- **Red Team** — Attack simulation and testing
- **Audit Log** — Searchable audit trail
- **Evaluation** — Benchmark results and comparison
- **Compliance** — Regulatory compliance status
""")
