# Researcher-Supervisor Multi-Agent (LangGraph)

A multi-agent system built with LangGraph where a **Supervisor** LLM orchestrates a **Researcher** (web search) and a **Writer** (draft generation) with a human-in-the-loop breakpoint.

## Architecture

```
START → Supervisor ──► Researcher ──► Supervisor
                  └──► Writer* ───► Supervisor ──► END
                  └──► FINISH ────────────────────► END
```

`*` Writer is paused by `interrupt_before` for human review before running.

## Quick Start

### 1. Clone & install

```bash
git clone <your-repo-url>
cd langgraph_project
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set API keys

```bash
cp .env.example .env
# Edit .env and add your keys
```

Get keys from:
- Groq API key → https://console.groq.com
- Tavily API key → https://app.tavily.com

### 3. Run in VS Code

Open `Researcher_Supervisor__1_.ipynb` in VS Code.  
Install the **Jupyter** extension if prompted.  
Select your virtual environment as the kernel, then run all cells.

## Agent Roles

| Agent | Model | Role |
|-------|-------|------|
| Supervisor | Llama 3.3-70B (Groq) | Routes decisions via structured output |
| Researcher | Tavily Search | Fetches web results |
| Writer | Llama 3.3-70B (Groq) | Generates the final draft |

## Key LangGraph Features Used

- `StateGraph` with `TypedDict` state
- `Annotated[List[str], operator.add]` for append-only state fields
- `add_conditional_edges` for Supervisor routing
- `MemorySaver` checkpointer for thread persistence
- `interrupt_before=["writer"]` for human-in-the-loop breakpoint
- `graph.get_state(config)` to inspect paused state
- `graph.stream(None, config)` to resume after breakpoint

## Project Structure

```
langgraph_project/
├── Researcher_Supervisor__1_.ipynb   # Main notebook
├── requirements.txt                  # Python dependencies
├── .env.example                      # API key template
├── .gitignore                        # Excludes secrets & cache
└── README.md                         # This file
```
