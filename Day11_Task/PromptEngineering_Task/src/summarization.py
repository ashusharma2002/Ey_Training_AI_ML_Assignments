import json
import os

from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

load_dotenv()

# --------------------------------------------------
# LLM
# --------------------------------------------------

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# --------------------------------------------------
# ZERO SHOT PROMPT
# --------------------------------------------------

zero_shot_prompt = PromptTemplate(
    input_variables=["transcript"],
    template="""
You are a financial analyst.

Summarize the following earnings call transcript
in 2-3 concise bullet points.

Transcript:
{transcript}
"""
)

zero_shot_chain = zero_shot_prompt | llm

# --------------------------------------------------
# FEW SHOT PROMPT
# --------------------------------------------------

few_shot_prompt = PromptTemplate(
    input_variables=["transcript"],
    template="""
Example

Transcript:
Revenue increased 10 percent.
Operating margin improved.

Summary:
- Revenue increased.
- Operating performance improved.

Now summarize the following transcript:

{transcript}

Provide 2-3 concise bullet points.
"""
)

few_shot_chain = few_shot_prompt | llm

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_earnings_calls(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --------------------------------------------------
# GENERATE SUMMARIES
# --------------------------------------------------

def generate_summaries(data):

    results = []

    for item in data:

        transcript = item["transcript"]

        zero_summary = zero_shot_chain.invoke(
            {"transcript": transcript}
        ).content

        few_summary = few_shot_chain.invoke(
            {"transcript": transcript}
        ).content

        results.append(
            {
                "id": item["id"],
                "transcript": transcript,
                "reference_summary": item["reference_summary"],
                "zero_shot_summary": zero_summary,
                "few_shot_summary": few_summary
            }
        )

    return results