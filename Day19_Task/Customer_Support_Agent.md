# Day 18 Capstone — Multi-Memory Support Agent

**Agentic Systems Bootcamp · Take-Home Project**

---

## What is this project?

This project is a **customer support AI agent** built for an electronics store.

The idea is simple — a customer sends a message like *"I want to order a keyboard"* and the agent figures out on its own what to do: check if it's in stock, place the order, get approval if it's expensive, verify everything is correct, and send a confirmation email. No hard-coded logic. The AI decides the steps.

This is different from a normal chatbot. A normal chatbot just replies with text. This agent actually **does things** — it reads from a database, writes orders, queues emails, and remembers your conversation. It behaves like a real support agent sitting behind a computer.

---

## What problem does it solve?

Imagine a customer support team that has to:
- Answer the same policy questions over and over (return policy, shipping times)
- Check stock before taking an order
- Get manager approval for expensive purchases
- Send confirmation emails after every order
- Handle email failures gracefully

This agent automates all of that. It handles the full flow from question to confirmation, escalates when needed, and never loses track of what it was doing.

---

## How does it work?

The core idea is **tool use**. We give the AI a set of tools — Python functions — and tell it what each one does. The AI then decides which tool to call, looks at the result, and decides what to do next. It keeps going until the job is done.

Here is what one full conversation turn looks like:

```
Customer says:  "Order 1 ergonomic chair, email me at john@email.com"

Agent thinks:   I should check inventory first
Agent calls:    check_inventory("CHAIR")
Result:         in stock, price $699

Agent thinks:   I'll place the order
Agent calls:    create_order("CHAIR", qty=1)
Result:         order created but needs approval — total $699 is over $300 limit

Agent thinks:   I need to get approval before continuing
Agent calls:    approve_order(order_id)
Result:         approved

Agent thinks:   Let me verify the order is correct
Agent calls:    verify_order(order_id)
Result:         verified — status is created, total matches

Agent thinks:   Now I can send the confirmation email
Agent calls:    send_confirmation("john@email.com", order_id)
Result:         email job queued, job_id returned instantly

Agent thinks:   Let me check the email was delivered
Agent calls:    check_job(job_id)
Result:         sent

Agent replies:  "Your order #5 has been placed for $699.
                 It has been approved and your confirmation
                 email has been sent to john@email.com"
```

The AI made every one of those decisions itself. We just gave it the tools and described the rules.

---

## What are the tools?

| Tool | What it does |
|---|---|
| `lookup_faq` | Searches the knowledge base for answers to policy and product questions |
| `check_inventory` | Checks how many units are in stock and the price |
| `create_order` | Places an order in the database |
| `approve_order` | Approves a high-value order — the agent cannot skip this |
| `verify_order` | Re-reads the order to confirm everything is correct before confirming |
| `send_confirmation` | Queues a confirmation email — returns instantly without waiting |
| `check_job` | Checks whether the queued email was actually delivered |

---

## What technologies did we use?

### Anthropic API — `claude-sonnet-4-6`
This is the brain of the agent. We send it the customer's message along with a list of available tools. It responds by saying which tool to call and with what arguments. We run the tool, send back the result, and Claude decides what to do next. This loop continues until Claude has enough information to give a final answer.

### SQLite
A lightweight database built into Python. We use it to store three things:
- **Inventory** — which products exist, how many are in stock, and the price
- **Orders** — every order the agent places, including its status
- **Documents** — the FAQ articles stored as vectors for search

No setup needed. The database lives in memory while the notebook runs.

### Redis (via fakeredis)
Redis is a fast in-memory data store. We use it for three different things:

**Short-term memory** — Every conversation has a session ID. Redis stores the last 6 messages of that session so the agent remembers what was said earlier. Each session automatically expires after 1 hour.

**Email job queue** — When the agent calls `send_confirmation`, instead of sending the email directly (which is slow and can fail), it drops a job into a Redis Stream. A separate worker picks it up and processes it. This keeps the agent fast.

**Dead-letter queue** — If an email fails 3 times in a row (for example, because the address is invalid), the job is moved to a separate stream called `emails:dlq`. Nothing is lost — you can inspect it and decide what to do.

We use `fakeredis` which is a Python library that simulates Redis in memory. The code is identical to real Redis so you can swap it out with a real Redis server by changing one line.

### NumPy
Used for the vector search inside long-term memory. When a customer asks a question, we convert it to a list of numbers (a vector) and compare it against all the FAQ articles using cosine similarity. The most similar article gets returned. NumPy makes these vector calculations fast.

### Python threading
The email worker runs in a background thread. This means it processes the email queue independently while the agent continues handling the conversation. The agent never has to wait for emails to be sent.

---

## Key concepts and patterns

### Short-term memory
The agent remembers the last 6 messages of your conversation. This means if you said *"I want the keyboard"* in a previous message, you don't have to repeat yourself. Redis stores this automatically and it expires after 1 hour.

### Long-term memory (vector store)
FAQ articles are stored as mathematical vectors in SQLite. When you ask a question, the agent searches for the most similar article using cosine similarity. This is the same idea behind how search engines work — finding meaning, not just matching keywords.

### Async email queue
Sending email is slow and unreliable. Instead of doing it inline, the agent drops a job into a Redis Stream and moves on immediately. A background worker processes it separately. This pattern is called the **producer-consumer pattern** and it is used everywhere in real systems.

### Human-approval gate
Orders above $300 are automatically blocked. The agent creates the order with a `needs_approval` status and cannot proceed until `approve_order` is called. Stock is not decremented until approval happens. This is called a **human-in-the-loop** pattern.

### Evaluator step
After placing or approving an order, the agent calls `verify_order` to independently re-read the order from the database and confirm the total and status are correct before sending a confirmation. If something is wrong it stops and reports an error. This is the **evaluator-optimiser pattern**.

### Tracing
Every tool call is wrapped with a `@traced` decorator that records the tool name, arguments, how long it took in milliseconds, and whether it passed or failed. After every turn, a trace table is printed so you can see exactly what the agent did and how long each step took.

### Retries with backoff
Every tool call is wrapped in a retry loop. If a tool fails due to a transient error, it waits 0.1 seconds and tries again, then 0.2 seconds, then 0.4 seconds. After 3 failures it gives up and reports the error to the agent. This makes the system resilient to temporary database or network issues.

### Prompt caching
The system prompt and tool definitions are sent to Claude on every message. We mark them with `cache_control: ephemeral` which tells Anthropic's infrastructure to cache them. On the second and third turns in a conversation, Claude reads from cache instead of re-processing everything. This cuts the input token cost by around 90% on repeated turns.

---

## Project structure

```
.
├── Day18_Capstone_Support_Agent.ipynb   ← everything is in here
├── README.md                            ← this file
├── .env                                 ← your API key (never commit this)
└── .gitignore                           ← excludes .env
```

The entire project lives in one notebook. Each cell covers one concept so you can run it step by step and see what each part does.

---

## Setup

**1. Get an API key**

Go to [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key

**2. Create a `.env` file** in the same folder as the notebook

```
ANTHROPIC_API_KEY=sk-ant-...
```

**3. Install dependencies**

```bash
pip install anthropic fakeredis numpy
```

**4. Open the notebook** in VS Code and run cells from top to bottom

> No API key? The notebook has an **offline mock mode** — just don't create a `.env` file and it will simulate the full agent chain without calling the API.

---

## What you will see when you run it

**Turn 1 — FAQ question**
The agent routes to `lookup_faq` and answers without touching the order system.

**Turn 2 — Low-value order ($258)**
Full chain runs: check inventory → place order → verify → queue email → confirm delivery.
No approval needed because $258 is under the $300 threshold.

**Turn 3 — High-value order ($699)**
Same chain but the approval gate fires. The agent calls `approve_order` automatically before continuing. You can see this in the trace table.

After each turn a **trace table** is printed:

```
  Tool                   Args                               ms     OK
  ─────────────────────────────────────────────────────────────────────
  lookup_faq             {'query': 'high value order...'}   0.8    OK
  check_inventory        {'sku': 'CHAIR'}                   0.1    OK
  create_order           {'sku': 'CHAIR', 'qty': 1}         0.2    OK
  approve_order          {'order_id': 3}                    0.1    OK
  verify_order           {'order_id': 3, ...}               0.0    OK
  send_confirmation      {'to': 'demo@example.com', ...}    0.5    OK
  check_job              {'job_id': 'c68f7c00'}             0.1    OK
```

---

## Why this matters

The patterns in this project are not just for a demo. They are the same patterns used in real production AI systems:

- **Tool use** is how GitHub Copilot, Cursor, and every modern AI assistant works
- **Redis Streams** are used by companies like Uber and Netflix for async job processing
- **Human-in-the-loop gates** are required by law in many industries for high-value decisions
- **Vector search** powers the knowledge bases behind every enterprise AI product
- **Prompt caching** is how companies keep API costs manageable at scale

Learning these patterns on a small project like this gives you the foundation to build real agentic systems.
