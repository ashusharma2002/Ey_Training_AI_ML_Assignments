# Researcher-Supervisor Multi-Agent: Deep Analysis & Full Guide

## Architecture Overview

This notebook implements a **Supervisor-Worker multi-agent pattern** using LangGraph. A central
Supervisor LLM orchestrates two specialist workers — a Researcher and a Writer — deciding at each
step which worker to invoke next. A human-in-the-loop breakpoint pauses execution before the Writer
runs, allowing a human to review research before any draft is written.

---

## Step 1 — State and Schema Design

```python
import operator
from typing import Annotated, List, TypedDict, Literal
from pydantic import BaseModel, Field

# ── The State object that travels through every node ─────────────────────────
class AgentState(TypedDict):
    task: str                                        # The user's original research question
    research_notes: Annotated[List[str], operator.add]  # APPENDS across nodes (not overwrites)
    draft: str                                       # Final written output
    next_node: str                                   # Routing signal set by the Supervisor
    retry_count: int                                 # Guard against infinite loops
    revision_feedback: str                           # Instructions Supervisor passes to the next worker

# ── Structured output schema the Supervisor must follow ──────────────────────
class Router(BaseModel):
    """Forces the Supervisor LLM to produce parseable routing decisions."""
    next_worker: Literal["researcher", "writer", "FINISH"] = Field(
        description="The next node to act"
    )
    instructions: str = Field(
        description="Specific instructions for the worker"
    )
    is_critical: bool = Field(
        description="If True, system will pause for human review"
    )
```

### Why `Annotated[List[str], operator.add]`?
LangGraph merges state updates from all nodes. Without the `operator.add` annotation,
each node's return value would *overwrite* `research_notes` instead of *appending* to it.
This is the correct pattern for accumulating results across multiple Researcher calls.

---

## Step 2 — LLM, Tool, and Agent Definitions

```python
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults

# ── Model and tool setup ──────────────────────────────────────────────────────
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
# temperature=0 → deterministic routing decisions, no creative randomness in the supervisor

search_tool = TavilySearchResults(k=2)  # Returns top-2 web search results per query


# ── Researcher: pure tool-calling, no LLM generation ─────────────────────────
def researcher(state: AgentState):
    """
    Calls Tavily search with the task as the query.
    Returns a new list item that gets APPENDED to state['research_notes']
    via the operator.add annotation.
    """
    print("🔍 Researcher is digging...")
    query = state['task']
    results = search_tool.invoke(query)
    print(results)
    return {
        "research_notes": [str(results)],  # Wrapped in list → appended, not overwritten
        "retry_count": 0
    }


# ── Writer: generates the final draft using accumulated research ──────────────
def writer(state: AgentState):
    """
    Joins all research_notes and passes them to the LLM to produce a draft.
    Only runs after a human has reviewed the research (due to the breakpoint).
    """
    print("✍️ Writer is composing...")
    context = "\n".join(state['research_notes'])
    res = llm.invoke(f"Write a report on {state['task']} using: {context}")
    return {"draft": res.content}


# ── Supervisor: the central orchestrator ─────────────────────────────────────
def supervisor(state: AgentState):
    """
    Uses structured output (Router schema) to make routing decisions.
    Reads the current state to decide whether to research more, write, or finish.
    """
    print("🧠 Supervisor is reviewing state...")

    # .with_structured_output() forces the LLM to return a valid Router object
    structured_llm = llm.with_structured_output(Router)

    prompt = f"""
    Task: {state['task']}
    Notes collected: {len(state['research_notes'])}
    Current Draft: {state['draft'][:100]}...
    If you have something in research_notes, select writer
    """

    print(f"Supervisor sees {len(state['research_notes'])} notes and draft length {len(state['draft'])}")

    decision = structured_llm.invoke(prompt)
    return {
        "next_node": decision.next_worker,      # Used by conditional_edges to route
        "revision_feedback": decision.instructions  # Passes context to the next worker
    }
```

### Key design insight: Supervisor prompt engineering
The Supervisor's decision quality is entirely determined by its prompt. The current prompt is
intentionally simple. For production use, you'd add:
- Summary of what's already in `research_notes`
- Explicit criteria for when enough research has been done
- A `retry_count` check to force FINISH after N rounds

---

## Step 3 — Graph Construction with Breakpoints

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

builder = StateGraph(AgentState)

# ── Register all nodes ────────────────────────────────────────────────────────
builder.add_node("supervisor", supervisor)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)

# ── Entry point ───────────────────────────────────────────────────────────────
builder.set_entry_point("supervisor")
# The Supervisor always runs first so it can assess the initial empty state
# and decide whether to research or (theoretically) jump straight to writing

# ── Conditional routing from Supervisor ──────────────────────────────────────
builder.add_conditional_edges(
    "supervisor",
    lambda x: x["next_node"],       # Read the routing signal set by supervisor()
    {
        "researcher": "researcher", # → runs researcher()
        "writer": "writer",         # → runs writer()  (PAUSED by breakpoint)
        "FINISH": END               # → graph terminates
    }
)

# ── Worker → Supervisor back-edges (the feedback loop) ───────────────────────
builder.add_edge("researcher", "supervisor")  # After researching, always re-evaluate
builder.add_edge("writer", "supervisor")       # After writing, supervisor can review/finish

# ── Compile with persistence and human-in-the-loop ───────────────────────────
memory = MemorySaver()  # In-memory checkpointer (use SqliteSaver for production)

graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["writer"]  # PAUSE execution just before writer() runs
    # At this point, graph.stream() halts and returns control to the caller
    # A human can inspect state, modify it, then call graph.stream(None, config) to resume
)
```

### Why `interrupt_before=["writer"]` is placed here
The breakpoint fires *after* the Supervisor has decided to call the Writer, but *before*
the Writer actually generates the draft. This is the ideal review point: the human can
see the research notes collected so far and decide whether to proceed.

---

## Step 4 — Execution: Two-Phase Streaming

```python
config = {"configurable": {"thread_id": "workshop_user_1"}}
# thread_id scopes the MemorySaver checkpoint — different users get separate state histories

initial_input = {
    "task": "Impact of LPU architecture on AI inference speeds",
    "research_notes": [],
    "retry_count": 0,
    "draft": ""
}

# ── Phase 1: Run until the breakpoint fires ───────────────────────────────────
print("--- STARTING GRAPH ---")
for event in graph.stream(initial_input, config, stream_mode="values"):
    if "next_node" in event:
        print(f"Moving to: {event['next_node']}")
# Graph will halt automatically when it reaches the writer node

# ── Inspect the paused state ──────────────────────────────────────────────────
snapshot = graph.get_state(config)
if snapshot.next:
    print(f"\n⏸️ SYSTEM PAUSED. Next step is: {snapshot.next}")
    print(f"Feedback from Supervisor: {snapshot.values['revision_feedback']}")
    # Here a human can:
    #   - Read snapshot.values['research_notes'] to review gathered data
    #   - Call graph.update_state(config, {"research_notes": [...]}) to inject edits
    #   - Or simply proceed

# ── Phase 2: Resume after human approval ─────────────────────────────────────
print("\n--- RESUMING GRAPH ---")
for event in graph.stream(None, config, stream_mode="values"):
    # Passing None as input resumes from the checkpointed state
    if "next_node" in event:
        print(f"Moving to: {event['next_node']}")
    elif "draft" in event:
        print(f"\n--- FINAL DRAFT ---:\n{event['draft']}")
```

---

## Execution Flow (step-by-step trace)

```
1. graph.stream(initial_input)  →  supervisor()
   state: notes=0, draft=""
   decision: next_node="researcher"

2. supervisor → researcher()
   Tavily searches "Impact of LPU architecture on AI inference speeds"
   research_notes grows: ["[result1, result2]"]
   returns to supervisor

3. researcher → supervisor()
   state: notes=1, draft=""
   decision: next_node="writer"

4. ⏸  BREAKPOINT fires (interrupt_before=["writer"])
   graph.stream() halts
   human inspects snapshot.values['research_notes']

5. graph.stream(None, config)   →  writer()
   joins research_notes, generates draft via LLM

6. writer → supervisor()
   state: notes=1, draft="[non-empty]"
   decision: next_node="FINISH"

7. supervisor → END
   final state returned
```

---

## Extension Tasks

### Extension 1 — Add a Critic agent for quality review

```python
def critic(state: AgentState) -> dict:
    """Reviews the draft for accuracy and completeness."""
    res = llm.invoke(
        f"Review this draft about '{state['task']}'. "
        f"List specific issues or confirm it is satisfactory.\n\n{state['draft']}"
    )
    return {"revision_feedback": res.content}

# Update Router to include critic
class Router(BaseModel):
    next_worker: Literal["researcher", "writer", "critic", "FINISH"]
    instructions: str
    is_critical: bool

# Add to builder
builder.add_node("critic", critic)
builder.add_edge("critic", "supervisor")  # Back to supervisor after critique
# Supervisor can then route to writer again for revision
```

### Extension 2 — Multi-query Researcher (parallel search)

```python
from langchain_core.runnables import RunnableParallel

def researcher_multi(state: AgentState) -> dict:
    """Runs 3 search queries in parallel for richer context."""
    queries = [
        state['task'],
        f"{state['task']} benchmarks",
        f"{state['task']} limitations"
    ]
    results = []
    for q in queries:
        results.append(str(search_tool.invoke(q)))
    return {"research_notes": results}  # All 3 appended in one return
```

### Extension 3 — Persistent checkpointing with SQLite

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Replace MemorySaver (lost on restart) with SQLite (survives restarts)
with SqliteSaver.from_conn_string("checkpoints.db") as memory:
    graph = builder.compile(checkpointer=memory, interrupt_before=["writer"])
    # Now any interrupted thread can be resumed even after server restart
```

### Extension 4 — Retry guard against infinite loops

```python
def supervisor(state: AgentState):
    structured_llm = llm.with_structured_output(Router)

    # Force termination after 3 research cycles
    if state.get("retry_count", 0) >= 3:
        return {"next_node": "FINISH", "revision_feedback": "Max retries reached"}

    decision = structured_llm.invoke(f"""
        Task: {state['task']}
        Notes collected: {len(state['research_notes'])}
        Draft: {state['draft'][:200]}
        Retry count: {state['retry_count']}
        Route to researcher if notes < 2, else writer, else FINISH.
    """)
    return {
        "next_node": decision.next_worker,
        "revision_feedback": decision.instructions,
        "retry_count": state.get("retry_count", 0) + 1
    }
```

### Extension 5 — Human state injection (edit research before writing)

```python
# After the breakpoint, inject a corrected or enriched research note
graph.update_state(
    config,
    {
        "research_notes": ["Custom human-verified fact: LPUs deliver 10x lower latency than GPUs for autoregressive inference due to SRAM-only design."]
    },
    as_node="researcher"   # Attributes the edit to the researcher node in the trace
)

# Then resume normally
for event in graph.stream(None, config, stream_mode="values"):
    ...
```

---

## Dependency Installation

```bash
pip install langgraph langchain langchain_groq langchain_community tavily-python pydantic

# Set environment variables
export GROQ_API_KEY="your_groq_key"
export TAVILY_API_KEY="your_tavily_key"
```

---

## Quick Reference: Key LangGraph APIs Used

| API | Purpose |
|-----|---------|
| `StateGraph(AgentState)` | Creates the graph with typed state |
| `Annotated[List[str], operator.add]` | Append-mode state field |
| `builder.add_conditional_edges(...)` | Routes based on state value |
| `builder.compile(interrupt_before=[...])` | Sets human-review breakpoints |
| `MemorySaver` | In-memory thread state (swap for SqliteSaver in prod) |
| `graph.stream(None, config)` | Resumes a paused thread |
| `graph.get_state(config)` | Reads current snapshot |
| `graph.update_state(config, {...})` | Human injects state edits |
| `llm.with_structured_output(Router)` | Forces Router-schema output |
