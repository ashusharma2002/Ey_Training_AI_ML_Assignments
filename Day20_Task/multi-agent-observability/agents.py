"""
Observability for a Multi-Agent System
=======================================
Turns a raw progress-listener into correlated, structured, queryable telemetry.

Usage
-----
    python agents.py                        # happy-path run
    python agents.py | python -m json.tool  # pretty-print each event
    python agents.py > trace.jsonl          # persist to JSONL file

To exercise the failure path, change:
    Agent("Writer", 4)  →  Agent("Writer", 4, fail_at_step=2)

Submission note
---------------
Next signal to capture for a real agentic workload: token_count and
estimated_cost_usd per agent_completed — in a real LLM pipeline, runaway
token usage is the most expensive silent failure and "step X/Y" tells you
nothing about it.
In a client environment these events would go to two destinations:
(1) AWS CloudWatch Logs Insights — each JSON event becomes a structured log
    entry queryable across runs (e.g. "all runs where Researcher took > 30 s");
(2) An OpenTelemetry-compatible trace backend such as AWS X-Ray or Honeycomb,
    where trace_id maps to a trace and span_id maps to a span, giving the ops
    team a waterfall diagram of agent handoffs to pinpoint bottlenecks.
"""

import json
import random
import time
import uuid
from datetime import datetime, timezone


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def now_iso() -> str:
    """Return the current UTC time as ISO-8601 with millisecond precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def emit(event: dict) -> None:
    """Write one structured JSON event to stdout (one event per line)."""
    print(json.dumps(event), flush=True)


# ──────────────────────────────────────────────────────────────────────────────
# AGENT  (starter code — interface unchanged)
# ──────────────────────────────────────────────────────────────────────────────

class Agent:
    """A simulated agent that does N steps of work. Pure simulation — no LLM, no network."""

    def __init__(self, name: str, steps: int, fail_at_step: int = None):
        self.name = name
        self.steps = steps
        self.fail_at_step = fail_at_step  # set to an int to force a deterministic failure

    def run(self, listener) -> None:
        for step in range(1, self.steps + 1):
            time.sleep(random.uniform(0.05, 0.2))   # simulate work / latency
            if self.fail_at_step and step == self.fail_at_step:
                raise RuntimeError(f"{self.name} failed at step {step}")
            listener(self.name, step, self.steps)


# ──────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR
# ──────────────────────────────────────────────────────────────────────────────

class Orchestrator:
    """
    Runs a sequential pipeline of agents and emits structured observability events.

    Events (all carry: timestamp, trace_id, span_id, event, agent)
    ---------------------------------------------------------------
    agent_started    — before an agent begins work
    agent_progress   — throttled: fires only when crossing a 25% milestone
    agent_completed  — after an agent finishes successfully; includes duration
    agent_failed     — if an agent raises; pipeline stops cleanly after this
    run_summary      — always last; one per run, regardless of outcome
    """

    def __init__(self, agents: list):
        self.agents = agents

    def run(self) -> None:

        # ── Task 1: one trace_id for the entire run ───────────────────────────
        trace_id: str = str(uuid.uuid4())

        # ── Task 2: pipeline-level state ─────────────────────────────────────
        total_pipeline_steps: int = sum(a.steps for a in self.agents)
        steps_done = [0]            # wrapped in list so nested closure can mutate
        run_start: float = time.monotonic()

        completed_agents: list = []
        failed_agent_info: dict = None

        for agent in self.agents:

            # ── Task 1: one span_id per agent execution ───────────────────────
            span_id: str = str(uuid.uuid4())
            agent_start: float = time.monotonic()

            # ── Task 3: agent_started event ───────────────────────────────────
            emit({
                "timestamp":             now_iso(),
                "trace_id":              trace_id,
                "span_id":               span_id,
                "event":                 "agent_started",
                "agent":                 agent.name,
                "total_steps":           agent.steps,
                "pipeline_pct_complete": round(
                    steps_done[0] / total_pipeline_steps * 100, 1
                ),
            })

            # last_completed_step tracks the last step the listener received.
            # When an agent raises, the failing step is last_completed_step + 1
            # because Agent.run() raises *before* calling listener on that step.
            last_completed_step = [0]

            def _make_listener(trace_id: str, span_id: str):
                """
                Returns a listener closure bound to this agent's trace_id and span_id.
                Using a factory prevents the common Python closure-in-loop bug
                where all closures share the same (final) loop variable values.
                """
                last_emitted_bucket = [-1]  # highest 25%-bucket already emitted

                def listener(name: str, step: int, total_steps: int) -> None:
                    # Advance global pipeline counter and track agent progress
                    steps_done[0]         += 1
                    last_completed_step[0] = step

                    elapsed      = time.monotonic() - run_start
                    throughput   = steps_done[0] / elapsed if elapsed > 0 else 0.0
                    pipeline_pct = steps_done[0] / total_pipeline_steps * 100
                    agent_pct    = step / total_steps * 100

                    # ── Task 3: throttle ─────────────────────────────────────
                    # Map agent_pct to the 25% bucket it falls into.
                    # bucket=0 for 0-24%, 25 for 25-49%, 50 for 50-74%, etc.
                    # Emit only when we cross into a new bucket.
                    bucket = int(agent_pct // 25) * 25
                    if bucket > last_emitted_bucket[0]:
                        last_emitted_bucket[0] = bucket
                        emit({
                            "timestamp":              now_iso(),
                            "trace_id":               trace_id,   # run-level id
                            "span_id":                span_id,    # agent-level id
                            "event":                  "agent_progress",
                            "agent":                  name,
                            "step":                   step,
                            "total_steps":            total_steps,
                            "agent_pct_complete":     round(agent_pct, 1),
                            "pipeline_pct_complete":  round(pipeline_pct, 1),
                            "throughput_steps_per_s": round(throughput, 2),
                        })

                return listener

            listener_fn = _make_listener(trace_id, span_id)

            try:
                agent.run(listener_fn)

                agent_duration = time.monotonic() - agent_start
                completed_agents.append(agent.name)

                # ── Task 3: agent_completed event ─────────────────────────────
                emit({
                    "timestamp":              now_iso(),
                    "trace_id":               trace_id,
                    "span_id":                span_id,
                    "event":                  "agent_completed",
                    "agent":                  agent.name,
                    "duration_s":             round(agent_duration, 3),
                    "pipeline_pct_complete":  round(
                        steps_done[0] / total_pipeline_steps * 100, 1
                    ),
                    "throughput_steps_per_s": round(
                        steps_done[0] / (time.monotonic() - run_start), 2
                    ),
                })

            except RuntimeError as exc:
                # Agent.run() raises BEFORE calling listener on the failing step,
                # so last_completed_step + 1 is the step that actually raised.
                failed_step = last_completed_step[0] + 1

                # ── Task 4: agent_failed event ────────────────────────────────
                failed_agent_info = {
                    "agent": agent.name,
                    "step":  failed_step,
                    "error": str(exc),
                }
                emit({
                    "timestamp":             now_iso(),
                    "trace_id":              trace_id,
                    "span_id":               span_id,
                    "event":                 "agent_failed",
                    "agent":                 agent.name,
                    "failed_at_step":        failed_step,
                    "error":                 str(exc),
                    "pipeline_pct_complete": round(
                        steps_done[0] / total_pipeline_steps * 100, 1
                    ),
                })
                break   # stop pipeline cleanly; remaining agents are not run

        # ── Task 4: run_summary — always the final event ──────────────────────
        total_duration = time.monotonic() - run_start
        emit({
            "timestamp":             now_iso(),
            "trace_id":              trace_id,
            "event":                 "run_summary",
            "status":                "failed" if failed_agent_info else "success",
            "total_duration_s":      round(total_duration, 3),
            "agents_completed":      completed_agents,
            "failed_agent":          failed_agent_info["agent"] if failed_agent_info else None,
            "failed_at_step":        failed_agent_info["step"]  if failed_agent_info else None,
            "failed_error":          failed_agent_info["error"] if failed_agent_info else None,
            "pipeline_pct_complete": round(
                steps_done[0] / total_pipeline_steps * 100, 1
            ),
        })


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    agents = [
        Agent("Planner",    3),
        Agent("Researcher", 6),
        Agent("Writer",     4),
        Agent("Reviewer",   2),
        # To exercise the failure path uncomment the line below and comment Writer above:
        # Agent("Writer", 4, fail_at_step=2),
    ]
    Orchestrator(agents).run()


if __name__ == "__main__":
    main()
