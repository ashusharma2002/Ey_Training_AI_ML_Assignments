"""
app.py
Streamlit chat UI for the RAG PDF Chat project.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
from pipeline import build_index, get_answer

st.set_page_config(page_title="Chat with your PDFs", page_icon="📄")
st.title("📄 Chat with your PDFs")

with st.sidebar:
    st.header("Setup")
    st.write("Put your PDFs in `data/pdfs/` before building the index.")
    if st.button("Build / Rebuild Index"):
        with st.spinner("Reading PDFs, chunking, embedding, and storing..."):
            build_index()
        st.success("Index built successfully!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if question := st.chat_input("Ask something about your documents..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, sources = get_answer(question)
            st.write(answer)
            if sources:
                with st.expander("Sources"):
                    for s in sources:
                        st.caption(s)

    st.session_state.messages.append({"role": "assistant", "content": answer})
