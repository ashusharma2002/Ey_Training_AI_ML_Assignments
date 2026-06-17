import json
import os
from src.pdf_qa import create_pdf_qa

from src.summarization import (
    load_earnings_calls,
    generate_summaries
)

from src.rouge_eval import (
    calculate_rouge,
    save_rouge_results
)

from src.ticket_classifier import (
    load_tickets,
    classify_tickets
)
# --------------------------------------------------
# PATHS
# --------------------------------------------------

EARNINGS_PATH = "data/earnings_calls.json"

TICKETS_PATH = "data/tickets.json"

OUTPUT_DIR = "outputs"

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

# --------------------------------------------------
# TASK 1
# SUMMARIZATION
# --------------------------------------------------

print("\n" + "=" * 60)
print("TASK 1 - SUMMARIZATION")
print("=" * 60)

earnings_data = load_earnings_calls(
    EARNINGS_PATH
)

summary_results = generate_summaries(
    earnings_data
)

with open(
    f"{OUTPUT_DIR}/summaries.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary_results,
        f,
        indent=4,
        ensure_ascii=False
    )

print(
    "Summaries saved successfully."
)

# --------------------------------------------------
# TASK 2
# ROUGE-L
# --------------------------------------------------

print("\n" + "=" * 60)
print("TASK 2 - ROUGE-L EVALUATION")
print("=" * 60)

rouge_results = calculate_rouge(
    summary_results
)

save_rouge_results(
    rouge_results,
    f"{OUTPUT_DIR}/rouge_scores.csv"
)

print("\nROUGE Results")

for row in rouge_results:

    print(
        f"Call {row['call_id']} | "
        f"Zero Shot: {row['zero_shot_rougeL']} | "
        f"Few Shot: {row['few_shot_rougeL']}"
    )

# --------------------------------------------------
# TASK 3
# TICKET CLASSIFIER
# --------------------------------------------------

print("\n" + "=" * 60)
print("TASK 3 - TICKET CLASSIFIER")
print("=" * 60)

ticket_data = load_tickets(
    TICKETS_PATH
)

ticket_predictions = classify_tickets(
    ticket_data
)

with open(
    f"{OUTPUT_DIR}/ticket_predictions.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        ticket_predictions,
        f,
        indent=4,
        ensure_ascii=False
    )

print(
    "Ticket predictions saved successfully."
)

# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

for item in ticket_predictions:

    print("\nTicket:")
    print(item["ticket"])

    print("\nPrediction:")
    print(item["prediction"])


    # ==================================================
# TASK 2 - PDF QUESTION ANSWERING
# ==================================================
print("\n" + "=" * 60)
print("TASK 2 - PDF QUESTION ANSWERING")
print("=" * 60)

pdf_path = "data/policy_document.pdf"

retriever, llm = create_pdf_qa(pdf_path)

questions = [
    "What is this document about?",
    "Summarize the policy.",
    "What are the important rules?"
]

qa_results = []

for question in questions:

    docs = retriever.invoke(question)

    context = "\n".join(
        [doc.page_content for doc in docs]
    )

    prompt = f"""
Answer the question using only the context.

Context:
{context}

Question:
{question}
"""

    answer = llm.invoke(prompt).content

    print("\nQuestion:")
    print(question)

    print("\nAnswer:")
    print(answer)

    qa_results.append(
        {
            "question": question,
            "answer": answer
        }
    )

with open(
    "outputs/qa_results.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        qa_results,
        f,
        indent=4,
        ensure_ascii=False
    )

print("\nQA Results Saved Successfully.")

# --------------------------------------------------
# COMPLETE
# --------------------------------------------------



print("\n" + "=" * 60)
print("PROJECT EXECUTION COMPLETED")
print("=" * 60)

print(
    f"""
Generated Files:

1. {OUTPUT_DIR}/summaries.json

2. {OUTPUT_DIR}/rouge_scores.csv

3. {OUTPUT_DIR}/ticket_predictions.json
"""
)