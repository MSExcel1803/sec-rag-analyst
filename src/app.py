import streamlit as st
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from answer import answer_question

st.set_page_config(
    page_title="SEC 10-K Analytics Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("SEC 10-K Analytics Assistant")
st.caption("Ask questions about 15 large-cap companies across tech, finance, and retail. Answers grounded in actual 10-K filings with citations.")

with st.sidebar:
    st.header("Coverage")
    st.markdown("""
    **Tech:** MSFT, GOOGL, AMZN, META, AAPL  
    **Finance:** JPM, GS, BLK, V, MA  
    **Retail:** WMT, TGT, COST, HD, LOW
    
    3 years of 10-K filings per company (2024-2026).
    """)
    st.markdown("---")
    st.header("Example questions")
    examples = [
        "How does Microsoft describe risks from AI?",
        "What are Amazon's main business segments?",
        "Compare JPMorgan and Goldman Sachs on interest rate risk.",
        "How do retailers describe supply chain risk?",
        "What does Meta say about regulatory risk in the EU?",
    ]
    for ex in examples:
        if st.button(ex, key=ex, use_container_width=True):
            st.session_state["question"] = ex
    
    st.markdown("---")
    top_k = st.slider("Excerpts to retrieve", 3, 15, 8)

# Main area
question = st.text_input(
    "Question",
    value=st.session_state.get("question", ""),
    placeholder="e.g., How does Microsoft describe AI risks?",
)

if st.button("Ask", type="primary") and question:
    with st.spinner("Searching filings and generating answer..."):
        result = answer_question(question, top_k=top_k)
    
    st.markdown("### Answer")
    st.markdown(result["answer"])
    
    if result["tickers_used"]:
        st.caption(f"Filtered to: {', '.join(result['tickers_used'])}")
    else:
        st.caption("No company filter applied (searched all filings)")
    
    st.markdown("### Sources")
    for i, chunk in enumerate(result["chunks"], 1):
        with st.expander(
            f"[{i}] {chunk['ticker']} {chunk['year']} · {chunk['section']} · similarity {chunk['similarity']:.3f}"
        ):
            st.text(chunk["content"])