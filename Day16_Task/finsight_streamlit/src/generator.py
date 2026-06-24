"""
generator.py — builds the LangChain RAG chain that generates answers.

Flow:
  user question
    → retriever fetches relevant chunks
    → chunks formatted with source labels
    → injected into FinSight prompt
    → GPT-4o generates a cited answer
    → plain string returned
"""
import httpx
import time
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.vectorstores import VectorStoreRetriever

import src.config as cfg


# ─── Prompt template ──────────────────────────────────────────────────────────
RAG_PROMPT = ChatPromptTemplate.from_template("""
You are FinSight, an AI research analyst for a Tier-1 investment bank.
Answer the analyst's question ONLY using the provided context.
If the context does not contain the answer, say: "Insufficient information in the retrieved context."
Always cite the specific source document at the end of your answer.

CONTEXT:
{context}

ANALYST QUESTION: {question}

ANSWER (cite source):
""")


def format_docs(docs) -> str:
    """Format retrieved chunks into a single context string with source labels."""
    return "\n\n".join(
        f"[Source: {d.metadata['source']}]\n{d.page_content}"
        for d in docs
    )


def build_llm() -> AzureChatOpenAI:
    """Initialise the Azure OpenAI GPT-4o client."""
    import httpx
    import socket

    # Force DNS resolution fix for Windows Streamlit threading issue
    original_getaddrinfo = socket.getaddrinfo
    def patched_getaddrinfo(*args, **kwargs):
        kwargs.pop('flags', None)
        return original_getaddrinfo(*args, **kwargs)

    http_client = httpx.Client(
        verify=True,
        timeout=30.0,
    )

    llm = AzureChatOpenAI(
        azure_endpoint=cfg.AZURE_ENDPOINT,
        azure_deployment=cfg.AZURE_DEPLOYMENT,
        openai_api_version=cfg.AZURE_API_VERSION,
        openai_api_key=cfg.AZURE_API_KEY,
        temperature=cfg.LLM_TEMPERATURE,
        max_tokens=cfg.LLM_MAX_TOKENS,
        timeout=cfg.LLM_TIMEOUT,
        http_client=http_client,
    )
    print(f"✅ Azure OpenAI LLM ready (deployment: {cfg.AZURE_DEPLOYMENT})")
    return llm

def build_rag_chain(retriever: VectorStoreRetriever, llm: AzureChatOpenAI):
    """
    Build the full RAG chain.

    Args:
        retriever: MMR retriever from retriever.py
        llm:       Azure OpenAI LLM from build_llm()

    Returns:
        Runnable chain — call .invoke("question") to get an answer string
    """
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    print("✅ RAG chain built")
    return chain


def run_queries(chain, queries: list[str]) -> list[dict]:
    """
    Run a list of queries through the RAG chain and record answers + latency.

    Args:
        chain:   The RAG chain from build_rag_chain()
        queries: List of question strings

    Returns:
        List of dicts with keys: query, answer, latency_s
    """
    results = []
    print(f"\n🚀 Running {len(queries)} queries...\n")

    for query in queries:
        t0 = time.time()
        answer = chain.invoke(query)
        latency = round(time.time() - t0, 2)

        results.append({
            "query": query,
            "answer": answer,
            "latency_s": latency,
        })

        print(f"❓ {query}")
        print(f"   ⏱️  {latency}s")
        print(f"   💬 {answer[:200]}...")
        print()

    return results
