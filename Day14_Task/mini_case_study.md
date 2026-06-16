# AI Customer Support System – Mini Case Study

## Problem Statement
A logistics company receives around 10,000 customer support emails every day. They want an AI system that can:
- Automatically classify incoming emails
- Retrieve relevant policy documents
- Generate draft replies
- Escalate complex cases to human agents using a ticketing API

---

## Solution Overview
We build an AI-powered customer support system using **LangChain + LlamaIndex**.

- **LlamaIndex** → Used for storing and retrieving company policy documents (RAG system)
- **LangChain** → Used for workflow orchestration, tool usage, and API integration

---

## System Workflow

### Step 1: Email Classification
- Incoming emails are analyzed using an LLM
- Each email is categorized (e.g., delivery issue, refund request, complaint)

---

### Step 2: Document Retrieval (RAG)
- Relevant policy documents are retrieved using LlamaIndex
- Example: refund policy, delivery guidelines, damage claims policy

---

### Step 3: Response Generation
- LLM generates a draft reply using:
  - Customer email content
  - Retrieved policy information

---

### Step 4: Escalation to Human Agent
- If the issue is complex or unclear:
  - LangChain triggers a ticketing API
  - The case is forwarded to a human support agent

---

## Architecture Flow

Customer Email  
→ Email Classification (LLM)  
→ Policy Retrieval (LlamaIndex)  
→ Draft Response Generation (LLM)  
→ Decision Making (LangChain)  
   → Simple case → Auto reply  
   → Complex case → Escalate to human agent via API  

---

## Why LangChain + LlamaIndex?

- **LlamaIndex**: Efficient document indexing and retrieval for large policy databases
- **LangChain**: Handles agent logic, tool calling, API integration, and workflow orchestration

---

## Final Outcome
An intelligent customer support assistant that:
- Reduces manual workload
- Speeds up response time
- Improves accuracy using company policies
- Automatically escalates complex issues