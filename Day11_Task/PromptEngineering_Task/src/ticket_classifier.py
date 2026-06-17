import json

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

# --------------------------------------------------
# LLM
# --------------------------------------------------

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# --------------------------------------------------
# TICKET CLASSIFICATION PROMPT
# --------------------------------------------------

classifier_prompt = PromptTemplate(
    input_variables=["ticket"],
    template="""
You are an expert customer support analyst.

Classify the following ticket into ONE category:

Categories:
1. Billing
2. Tech
3. Refund
4. General
5. Escalate

Provide the answer in exactly this format:

Category: <category>

Reason:
<reason>

Ticket:
{ticket}
"""
)

classifier_chain = classifier_prompt | llm

# --------------------------------------------------
# LOAD TICKETS
# --------------------------------------------------

def load_tickets(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --------------------------------------------------
# CLASSIFY TICKETS
# --------------------------------------------------

def classify_tickets(ticket_data):

    predictions = []

    for item in ticket_data:

        ticket_text = item["ticket"]

        response = classifier_chain.invoke(
            {
                "ticket": ticket_text
            }
        )

        predictions.append(
            {
                "ticket": ticket_text,
                "prediction": response.content
            }
        )

    return predictions