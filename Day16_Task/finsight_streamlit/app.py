"""
app.py — FinSight Streamlit Web Application
Run with: streamlit run app.py
"""

import sys
import os
import time
import socket

# ─── Windows DNS fix for Streamlit threading ──────────────────────────────────
_orig_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, family, type, proto)
socket.getaddrinfo = _patched_getaddrinfo

# Force no proxy
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"
os.environ["PYTHONHTTPSVERIFY"] = "0"

import streamlit as st

# ─── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="FinSight — Financial RAG",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-title { font-size: 2rem; font-weight: 600; margin-bottom: 0; }
.sub-title   { font-size: 1rem; color: #666; margin-bottom: 1.5rem; }
.answer-box  { background: #f8f9fa; border-left: 4px solid #1D9E75;
               padding: 1rem 1.25rem; border-radius: 0 8px 8px 0;
               margin: 0.5rem 0 1rem; font-size: 0.95rem; line-height: 1.6; }
.source-tag  { background: #e1f5ee; color: #0f6e56; font-size: 0.75rem;
               padding: 2px 8px; border-radius: 20px; margin-left: 6px; }
.metric-label{ font-size: 0.75rem; color: #888; }
.chunk-box   { background: #fff; border: 1px solid #e5e5e2;
               border-radius: 8px; padding: 0.75rem 1rem;
               margin-bottom: 0.5rem; font-size: 0.8rem; line-height: 1.5; }
.step-done   { color: #1D9E75; font-weight: 500; }
.step-info   { color: #666; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


# ─── Pipeline init (cached so it only runs once) ──────────────────────────────
@st.cache_resource(show_spinner=False)
def init_pipeline():
    """Load and build all pipeline components — cached across sessions."""
    from src.documents import load_documents
    from src.chunker import create_chunks
    from src.embedder import build_embedding_model, build_vectorstore
    from src.retriever import build_retriever
    from src.generator import build_llm, build_rag_chain

    docs      = load_documents()
    chunks    = create_chunks(docs)
    emb_model = build_embedding_model()
    vs        = build_vectorstore(chunks, emb_model)
    retriever = build_retriever(vs)
    llm       = build_llm()
    chain     = build_rag_chain(retriever, llm)

    return {
        "docs":      docs,
        "chunks":    chunks,
        "retriever": retriever,
        "llm":       llm,
        "chain":     chain,
    }


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏦 FinSight")
    st.markdown("**Financial RAG System**")
    st.markdown("---")

    st.markdown("### About")
    st.markdown("""
An end-to-end RAG pipeline that queries
Apple's SEC 10-K annual report filings
using natural language.

**Built with:**
- 🔍 FAISS vector search
- 🤗 HuggingFace embeddings
- 🤖 Azure OpenAI GPT-4o
- 🔗 LangChain
    """)

    st.markdown("---")
    st.markdown("### Documents loaded")
    st.markdown("""
- Apple_10K_2023_Risk
- Apple_10K_2023_Products
- Apple_10K_2023_Liquidity
    """)

    st.markdown("---")
    st.markdown("### Settings")
    show_chunks   = st.toggle("Show retrieved chunks", value=False)
    show_latency  = st.toggle("Show latency", value=True)

    st.markdown("---")
    st.markdown("### Targets")
    st.markdown("""
| Metric | Target |
|--------|--------|
| Faithfulness | ≥ 0.85 |
| Latency | < 3s |
| Cost/query | < $0.002 |
    """)


# ─── Main UI ──────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🏦 FinSight</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">AI Research Analyst · Apple SEC 10-K · Azure OpenAI GPT-4o</p>', unsafe_allow_html=True)

# ─── Pipeline status ──────────────────────────────────────────────────────────
with st.status("Initialising pipeline...", expanded=True) as status:
    try:
        st.write("Loading documents...")
        pipeline = init_pipeline()
        st.write("Building FAISS index...")
        st.write("Connecting to Azure OpenAI...")
        status.update(label="✅ Pipeline ready!", state="complete", expanded=False)
    except Exception as e:
        status.update(label=f"❌ Error: {e}", state="error", expanded=True)
        st.error(f"""
**Setup failed:** {e}

Make sure your `.env` file has:
```
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```
        """)
        st.stop()

# ─── Pipeline stats row ───────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Documents", len(pipeline["docs"]))
with col2:
    st.metric("Chunks", len(pipeline["chunks"]))
with col3:
    st.metric("Vector dims", "384")
with col4:
    st.metric("Model", "GPT-4o")

st.markdown("---")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["💬 Ask a question", "📋 Sample questions", "📊 Pipeline info"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Ask a question
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Ask anything about Apple's 2023 annual report")

    question = st.text_input(
        label="Your question",
        placeholder="e.g. What was Apple's total revenue in fiscal 2023?",
        label_visibility="collapsed",
    )

    ask_col, clear_col = st.columns([1, 5])
    with ask_col:
        ask_btn = st.button("Ask FinSight →", type="primary", use_container_width=True)
    with clear_col:
        if st.button("Clear", use_container_width=False):
            st.session_state.pop("last_result", None)
            st.rerun()

    if ask_btn and question.strip():
        with st.spinner("Searching documents and generating answer..."):
            t0     = time.time()
            answer = pipeline["chain"].invoke(question)
            latency = round(time.time() - t0, 2)

            chunks_used = pipeline["retriever"].invoke(question)

            st.session_state["last_result"] = {
                "question":    question,
                "answer":      answer,
                "latency":     latency,
                "chunks_used": chunks_used,
            }

    if "last_result" in st.session_state:
        r = st.session_state["last_result"]

        st.markdown("#### Answer")
        st.markdown(f'<div class="answer-box">{r["answer"]}</div>', unsafe_allow_html=True)

        if show_latency:
            st.caption(f"⏱ {r['latency']}s · GPT-4o · Azure OpenAI")

        if show_chunks:
            st.markdown("#### Retrieved chunks")
            for i, chunk in enumerate(r["chunks_used"], 1):
                st.markdown(f"""
<div class="chunk-box">
  <span class="source-tag">{chunk.metadata['source']}</span><br/><br/>
  {chunk.page_content[:300]}...
</div>
""", unsafe_allow_html=True)

    elif ask_btn and not question.strip():
        st.warning("Please type a question first.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Sample questions
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Sample questions — click to run")

    SAMPLE_QS = [
        "What was Apple's total revenue in fiscal year 2023?",
        "How much cash did Apple have at the end of fiscal 2023?",
        "What percentage of Apple's revenue came from iPhone in 2023?",
        "How much did Apple return to shareholders in fiscal 2023?",
        "What is Apple's gross margin for fiscal 2023?",
        "What was Apple's net income in 2023?",
        "How many active devices does Apple have?",
        "What was Apple's long-term debt in 2023?",
    ]

    for q in SAMPLE_QS:
        if st.button(q, key=f"sq_{q}", use_container_width=True):
            with st.spinner("Thinking..."):
                t0     = time.time()
                answer = pipeline["chain"].invoke(q)
                latency = round(time.time() - t0, 2)
                chunks_used = pipeline["retriever"].invoke(q)

            st.markdown(f"**Q:** {q}")
            st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)
            if show_latency:
                st.caption(f"⏱ {latency}s")
            st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Pipeline info
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Pipeline architecture")

    st.markdown("""
```
User Question
      ↓
  FAISS MMR Retriever
  (finds top 4 relevant chunks)
      ↓
  Format chunks with source labels
      ↓
  FinSight RAG Prompt
  (context + question → GPT-4o)
      ↓
  Azure OpenAI GPT-4o
  (generates cited answer)
      ↓
  Answer with [Source: ...]
```
    """)

    st.markdown("### Documents in the system")
    for doc in pipeline["docs"]:
        with st.expander(f"📄 {doc.metadata['source']} ({len(doc.page_content)} chars)"):
            st.text(doc.page_content[:500] + "...")

    st.markdown("### All chunks")
    chunk_data = [
        {
            "Chunk #": i + 1,
            "Source": c.metadata["source"],
            "Length": len(c.page_content),
            "Preview": c.page_content[:80] + "...",
        }
        for i, c in enumerate(pipeline["chunks"])
    ]
    st.dataframe(chunk_data, use_container_width=True)

    st.markdown("### RAGAS evaluation results")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Faithfulness", "0.70", delta="-0.15 vs target", delta_color="inverse")
    with col2:
        st.metric("Answer relevancy", "0.78")
    with col3:
        st.metric("Context recall", "0.80")
    with col4:
        st.metric("Context precision", "0.60")

    st.info("💡 Faithfulness improves to ~0.857 with hybrid+rerank retrieval strategy.")

    st.markdown("### Retrieval strategy comparison")
    st.markdown("""
| Strategy | Avg latency | Faithfulness | Notes |
|---|---|---|---|
| Dense (FAISS only) | 1.23s | 0.70 | Baseline |
| Hybrid (FAISS + BM25) | 1.16s | ~0.82 | Keyword + semantic |
| Hybrid + Rerank | 1.80s | ~0.857 ✅ | Best accuracy |
    """)
