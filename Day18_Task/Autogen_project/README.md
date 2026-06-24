# AutoGen Multi-Agent System with Groq LLMs

> A multi-agent AI pipeline built with Microsoft AutoGen, powered by Groq's ultra-fast LPU inference, running on Google Colab with a live UI via Ngrok.

---

## Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Task Flow](#task-flow)
4. [Architecture](#architecture)
5. [Agent Overview](#agent-overview)
6. [Technology Stack](#technology-stack)
7. [Project Structure](#project-structure)
8. [Setup & How to Run](#setup--how-to-run)
9. [What Each Cell Does](#what-each-cell-does)

---

## Overview

This project demonstrates how to build a **multi-agent AI system** where multiple AI agents collaborate on a task — each with a specific role, powered by different LLM models, and optionally guided by a human in real time.

It is built on top of **Microsoft AutoGen** (a framework for orchestrating multiple AI agents) and uses **Groq** as the inference provider for extremely fast responses.

---

## Problem Statement

A single LLM call is not enough for complex real-world tasks. The challenges are:

- **No role separation** — one model tries to do everything
- **No tool access** — the model cannot fetch live data (e.g. stock prices)
- **No human control** — once you send a prompt, the model runs without any way to guide it
- **Slow inference** — multi-turn agent loops feel painful with slow models

**This project solves all four** by building a pipeline where agents have defined roles, can call real tools, pause for human input, and run on Groq's high-speed hardware.

---

## Task Flow

### Core Task (Cell 4) — 2-Agent Research Pipeline

```
┌─────────────────────────────────────────────────────┐
│                   User gives a Task                  │
│  "Explain why Groq LPUs give higher throughput       │
│   for LLMs than standard GPUs"                       │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │     Researcher Agent   │
          │  Model: LLaMA 3.1 8B   │
          │  → Writes detailed     │
          │    research in         │
          │    Markdown format     │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │      Editor Agent      │
          │  Model: LLaMA 3.3 70B  │
          │  → Critiques and       │
          │    refines the output  │
          └────────────┬───────────┘
                       │
              Repeats up to
              4 messages total
                       │
                       ▼
               ✅ Final Output
```

---

### Extension Task (Cell 5) — 3-Agent Pipeline with Tool + Human

```
┌─────────────────────────────────────────────────────┐
│                   User gives a Task                  │
│  "Find current stock price of Apple (AAPL) and       │
│   provide analysis for investors"                    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │     Researcher Agent   │
          │  Model: LLaMA 3.1 8B   │
          │                        │
          │  1. Calls Tool:        │
          │     get_stock_price()  │──► Yahoo Finance API
          │     ← gets live price  │       (no key needed)
          │  2. Writes analysis    │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │      Editor Agent      │
          │  Model: LLaMA 3.3 70B  │
          │  → Reviews & refines   │
          │  → Asks for approval   │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │    UserProxy Agent     │
          │       (YOU)            │
          │  → Type feedback       │
          │    to continue         │
          │  → Type TERMINATE      │
          │    to stop             │
          └────────────┬───────────┘
                       │
              Repeats up to
              6 messages OR
              until TERMINATE
                       │
                       ▼
               ✅ Final Output
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Google Colab                          │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               AutoGen Orchestration Layer            │   │
│   │                                                      │   │
│   │   ┌─────────────┐        ┌─────────────────────┐    │   │
│   │   │  Researcher  │        │       Editor         │    │   │
│   │   │  Assistant   │        │     Assistant        │    │   │
│   │   │    Agent     │        │       Agent          │    │   │
│   │   └──────┬───────┘        └──────────┬──────────┘    │   │
│   │          │                           │               │   │
│   │          ▼                           ▼               │   │
│   │   ┌─────────────┐        ┌─────────────────────┐    │   │
│   │   │  LLaMA 3.1  │        │     LLaMA 3.3 70B   │    │   │
│   │   │   8B Instant│        │      Versatile       │    │   │
│   │   │  (via Groq) │        │     (via Groq)       │    │   │
│   │   └──────┬───────┘        └─────────────────────┘    │   │
│   │          │                                           │   │
│   │          ▼                                           │   │
│   │   ┌─────────────┐        ┌─────────────────────┐    │   │
│   │   │  Tool Call   │        │    UserProxy Agent   │    │   │
│   │   │get_stock_    │        │    (Human Input)     │    │   │
│   │   │price(ticker) │        │                      │    │   │
│   │   └──────┬───────┘        └─────────────────────┘    │   │
│   │          │                                           │   │
│   │          ▼                                           │   │
│   │   Yahoo Finance                                      │   │
│   │   Public API                                         │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │         AutoGen Studio UI (port 8081)                │   │
│   │         Exposed publicly via Ngrok tunnel            │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Overview

| Agent | Type | Model | Role | Tools |
|---|---|---|---|---|
| **Researcher** | `AssistantAgent` | LLaMA 3.1 8B Instant | Gathers information, writes detailed research in Markdown | `get_stock_price()` (Cell 5 only) |
| **Editor** | `AssistantAgent` | LLaMA 3.3 70B Versatile | Critiques the Researcher's output and refines it for professional delivery | None |
| **UserProxy** | `UserProxyAgent` | — (no LLM) | Pauses the pipeline and waits for your typed input — feedback or TERMINATE | None |

### Agent Behaviour

**Researcher**
- Receives the task first in every round
- In Cell 5: must call `get_stock_price()` tool before writing analysis
- Responds in structured Markdown

**Editor**
- Reviews what Researcher produced
- Points out gaps, improves clarity and structure
- In Cell 5: asks UserProxy for approval before concluding

**UserProxy** *(Cell 5 only)*
- Not an LLM — it calls Python's `input()` function
- Every time it's its turn, the entire pipeline freezes until you type
- Type any feedback to continue, type `TERMINATE` to stop the session

---

## Technology Stack

| Technology | Version / Details | Purpose |
|---|---|---|
| **Microsoft AutoGen** | `autogen-agentchat` | Multi-agent orchestration framework |
| **AutoGen Studio** | `autogenstudio` | Visual drag-and-drop UI for agent workflows |
| **Groq API** | `api.groq.com` | High-speed LPU inference provider |
| **LLaMA 3.1 8B Instant** | Meta via Groq | Fast, lightweight model for Researcher agent |
| **LLaMA 3.3 70B Versatile** | Meta via Groq | Powerful model for Editor agent |
| **OpenAIChatCompletionClient** | `autogen_ext` | Connects AutoGen to any OpenAI-compatible endpoint (used for Groq) |
| **RoundRobinGroupChat** | `autogen_agentchat` | Team strategy — agents take turns in fixed order |
| **MaxMessageTermination** | `autogen_agentchat` | Stops the loop after N messages |
| **pyngrok** | Python Ngrok wrapper | Exposes AutoGen Studio UI from Colab to a public URL |
| **Yahoo Finance API** | Public endpoint | Live stock price data — no API key required |
| **Google Colab** | Cloud notebook | Runtime environment — supports `await` natively |

### Why Groq?
Groq uses **LPU (Language Processing Unit)** chips — hardware purpose-built for LLM inference. In a multi-agent loop where agents exchange multiple messages, Groq's speed (often 5–10× faster than GPU-based providers) makes the pipeline feel responsive instead of sluggish.

### Why Two Different Models?
Using a smaller fast model (8B) for initial research and a larger capable model (70B) for editorial critique is a common production pattern — it balances speed and quality while keeping inference cost lower than using the large model for everything.

---

## Project Structure

```
autogen-groq/
│
├── Autogen_groq_.ipynb       ← Main notebook (all 5 cells)
│
└── README.md                 ← This file
```

### Inside the Notebook

```
Autogen_groq_.ipynb
│
├── Cell 1 — Installation
│   └── pip install autogenstudio pyngrok
│
├── Cell 2 — API Key Setup
│   ├── GROQ_API_KEY      (via getpass — never hardcoded)
│   └── NGROK_AUTH_TOKEN  (via getpass — never hardcoded)
│
├── Cell 3 — AutoGen Studio UI
│   ├── Starts studio on port 8081
│   └── Opens Ngrok tunnel → prints public URL
│
├── Cell 4 — Core Task (2-Agent Pipeline)
│   ├── Researcher Agent  (LLaMA 3.1 8B)
│   ├── Editor Agent      (LLaMA 3.3 70B)
│   ├── RoundRobinGroupChat
│   └── MaxMessageTermination (max 4 messages)
│
└── Cell 5 — Extension Task (3-Agent + Tool + Human)
    ├── get_stock_price() tool  (Yahoo Finance)
    ├── Researcher Agent        (LLaMA 3.1 8B + tool)
    ├── Editor Agent            (LLaMA 3.3 70B)
    ├── UserProxy Agent         (human input)
    ├── RoundRobinGroupChat
    └── MaxMessageTermination   (max 6 messages)
```

---

## Setup & How to Run

### Step 1 — Prerequisites

| Requirement | Where to get it |
|---|---|
| Google account | [colab.google](https://colab.google) |
| Groq API Key | [console.groq.com](https://console.groq.com) — free tier |
| Ngrok Auth Token | [dashboard.ngrok.com](https://dashboard.ngrok.com) — free account |

---

### Step 2 — Open the Notebook in Colab

1. Go to [colab.google](https://colab.google)
2. Click **File → Upload Notebook**
3. Upload `Autogen_groq_.ipynb`

---

### Step 3 — Run the Cells in Order

**Cell 1 — Install packages**
```python
!pip install -q autogenstudio pyngrok
```

**Cell 2 — Enter your API keys when prompted**
```
Enter your Groq API Key:   [paste key here, press Enter]
Enter your Ngrok Token:    [paste token here, press Enter]
```

**Cell 3 — Launch AutoGen Studio (optional)**
```
Output will print a public URL like:
NgrokTunnel: "https://xxxx.ngrok.io" -> "http://localhost:8081"
Click that link to open the visual Studio UI
```

**Cell 4 — Run the core 2-agent task**
```
Agents will start exchanging messages automatically.
Watch Researcher and Editor discuss:
"Explain why Groq LPUs provide higher throughput for LLMs than standard GPUs"
```

**Cell 5 — Run the extension task with human control**
```
When you see [UserProxy]: waiting for input...

→ Type your feedback and press Enter   (pipeline continues)
→ Type TERMINATE and press Enter       (pipeline stops cleanly)
```

---

## What Each Cell Does

| Cell | Name | What it does |
|---|---|---|
| **Cell 1** | Installation | Installs `autogenstudio` and `pyngrok` libraries |
| **Cell 2** | API Key Setup | Securely reads Groq API key and Ngrok token using `getpass` — keys go into environment variables, never into code |
| **Cell 3** | AutoGen Studio UI | Launches the AutoGen Studio visual interface on port 8081 and exposes it to the public internet via an Ngrok tunnel |
| **Cell 4** | Core Multi-Agent Task | Creates Researcher + Editor agents backed by two Groq/LLaMA models, runs them in a RoundRobin loop on a research question |
| **Cell 5** | Extension Task | Adds a real stock price tool to Researcher, adds a UserProxy so you control the conversation, runs a 3-agent loop on a live financial analysis task |

---

## Push to GitHub

```bash
git init
git add Autogen_groq_.ipynb README.md
git commit -m "Add AutoGen multi-agent system with Groq LLMs"
git remote add origin https://github.com/YOUR_USERNAME/autogen-groq.git
git push -u origin main
```
