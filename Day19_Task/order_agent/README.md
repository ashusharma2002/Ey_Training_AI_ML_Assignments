# Claude Order Agent
Day 18 · Colab 1 · Agentic Systems Bootcamp

---

## What this builds

A tool-using AI agent that looks up orders, remembers user preferences,
and holds multi-turn conversations — driven by Claude's `stop_reason` loop.

```
User message
     │
     ▼
 Agent  ──loads history──▶  Redis
     │
     ▼
 Claude (stop_reason loop)
     │
     ├── tool_use  ──▶  run tool  ──▶  FastAPI / Redis
     │                   loop back with result
     │
     └── end_turn  ──▶  save reply  ──▶  return text
```

---

## File structure

```
order_agent/
├── .env             API keys — git-ignored
├── .env.example     Template — safe to commit
├── .gitignore
├── requirements.txt
│
├── api.py           FastAPI backend  (/orders  /customers)
├── memory.py        Redis memory  +  compaction  +  TTL
├── tools.py         Tool schemas  +  dispatch  +  PII guard
├── agent.py         Agent loop  +  token tracking
├── main.py          Run demos or interactive chat
└── test_agent.py    Full test suite
```

---

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Edit `.env` and paste your Anthropic API key.

---

## Run

```bash
python main.py              # base demo
python main.py --ext 1      # rolling compaction
python main.py --ext 2      # TTL + forget_fact
python main.py --ext 3      # parallel tool calls
python main.py --ext 4      # PII guard
python main.py --ext 5      # token accounting
python main.py --ext 6      # real Redis
python main.py --chat       # interactive REPL
pytest test_agent.py -v     # all tests
```

No API key → leave `.env` blank → runs in offline mock mode.

---

## Extensions

| # | What | File |
|---|---|---|
| 1 | History > 20 turns → Haiku summarises oldest half | `memory.py` |
| 2 | Facts auto-expire (TTL) or delete on demand | `memory.py` + `tools.py` |
| 3 | Two tools called in one Claude turn (parallel) | `api.py` + `tools.py` |
| 4 | PII guard blocks card / email / phone storage | `tools.py` |
| 5 | Token usage printed after every turn | `agent.py` |
| 6 | Real Redis via `REDIS_URL` in `.env` | `memory.py` |

---

## Git

```bash
git init
git add .
git commit -m "Day 18 Claude agent"
git remote add origin https://github.com/YOUR_USERNAME/REPO.git
git push -u origin main
```

`.env` is in `.gitignore` — your key is never committed.
Teammates copy `.env.example` → `.env` and fill in their own key.
