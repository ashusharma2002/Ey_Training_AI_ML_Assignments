"""
generator.py
Takes retrieved chunks + user question, builds a grounded prompt,
and calls Gemini to generate the final answer.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-flash-latest")


def build_prompt(question: str, chunks: list) -> str:
    context_blocks = []
    for c in chunks:
        context_blocks.append(f"[Source: {c['source']}, Page {c['page']}]\n{c['text']}")

    context = "\n\n---\n\n".join(context_blocks)

    prompt = f"""You are a helpful assistant answering questions based ONLY on the provided document excerpts.
If the answer is not contained in the excerpts, say "I couldn't find that in the provided documents."
Do not make up information.

Document excerpts:
{context}

Question: {question}

Answer:"""
    return prompt


def generate_answer(question: str, chunks: list) -> str:
    prompt = build_prompt(question, chunks)
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    from retriever import retrieve_chunks

    q = "What is this document about?"
    chunks = retrieve_chunks(q)
    answer = generate_answer(q, chunks)
    print("\nAnswer:", answer)
