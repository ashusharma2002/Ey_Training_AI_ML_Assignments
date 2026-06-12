!pip install -q \
langchain-community \
langchain-core \
langchain-huggingface \
langchain-groq \
sentence-transformers \
faiss-cpu

print("Dependencies installed successfully")

import os

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_groq import ChatGroq

print("Imports successful")

GROQ_API_KEY = "enter your api key"

os.environ["GROQ_API_KEY"] = GROQ_API_KEY

MODEL_NAME = "llama-3.1-8b-instant"

print("Configuration loaded")

faq_data = [

{
    "question":"What is RAG?",
    "answer":"Retrieval Augmented Generation combines document retrieval with LLM generation to produce grounded answers."
},

{
    "question":"What is FAISS?",
    "answer":"FAISS is Meta's vector similarity search library used for semantic retrieval."
},

{
    "question":"What is an embedding?",
    "answer":"An embedding is a numerical vector representation of text."
},

{
    "question":"What is a vector database?",
    "answer":"A vector database stores embeddings for semantic search."
},

{
    "question":"What is cosine similarity?",
    "answer":"Cosine similarity measures how similar two vectors are."
},

{
    "question":"What is LangChain?",
    "answer":"LangChain is a framework for building applications powered by large language models."
},

{
    "question":"What is Groq?",
    "answer":"Groq provides ultra-fast inference for large language models."
},

{
    "question":"What is chunking?",
    "answer":"Chunking splits large documents into smaller pieces for retrieval."
},

{
    "question":"What is hybrid search?",
    "answer":"Hybrid search combines keyword search and vector search."
},

{
    "question":"What is an LLM?",
    "answer":"A Large Language Model is trained on massive text corpora to understand and generate text."
}

]

print(f"Loaded {len(faq_data)} FAQs")

documents = []

for faq in faq_data:

    content = f"""
Question: {faq['question']}
Answer: {faq['answer']}
"""

    documents.append(
        Document(
            page_content=content,
            metadata={"source": faq["question"]}
        )
    )

print(f"Created {len(documents)} documents")

embedder = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded")

vector_store = FAISS.from_documents(
    documents,
    embedder
)

print("FAISS index created")

llm = ChatGroq(
    model=MODEL_NAME,
    temperature=0
)

print("Groq model ready")

def retrieve_faqs(query, top_k=2):

    return vector_store.similarity_search_with_score(
        query,
        k=top_k
    )


def generate_answer(query, retrieved_docs):

    context = "\n\n".join(
        [doc.page_content for doc, score in retrieved_docs]
    )

    prompt = f"""
You are a FAQ assistant.

Use ONLY the information below.

{context}

Question:
{query}

Answer in 2-3 sentences.
"""

    response = llm.invoke(prompt)

    return response.content

def ask_bot(query):

    retrieved_docs = retrieve_faqs(query)

    answer = generate_answer(
        query,
        retrieved_docs
    )

    print("\n====================")
    print("ANSWER")
    print("====================")
    print(answer)

    print("\n====================")
    print("TOP-2 MATCHES")
    print("====================")

    for idx, (doc, score) in enumerate(retrieved_docs, start=1):

        print(f"\nMatch #{idx}")

        print(
            f"Source FAQ : {doc.metadata['source']}"
        )

        print(
            f"Similarity Score : {score:.4f}"
        )

print("=" * 50)
print("SMART FAQ BOT")
print("=" * 50)
print("Type 'exit' to quit")

while True:

    user_query = input("\nYou : ")

    if user_query.lower() == "exit":

        print("Goodbye!")
        break

    ask_bot(user_query)

