# CLAUDE.md

This is the AII Platform: agentic AI + algorithmic trading. Read **docs/** in
order (start with docs/00_Start_Here.md) before working. docs/02 is the
architecture; docs/04 is the build order.

## Non-negotiable rules (from docs/01 and docs/02)
- **LLMs reason, software calculates.** Indicators/backtests come from the
  deterministic engine, never from an LLM.
- **Deterministic systems own risk.** No LLM sets size, stops, or limits.
- **Dependencies point down:** the engine never imports agents; agents import the
  engine. The engine must run and be tested with no AI present.
- **The engine core is standard-library-first.** `cd backend && python run_sim.py`
  must run with zero installs.
- **Judge strategies on expectancy (R)/profit factor/drawdown, not win rate.**
- **Validate before trusting:** every strategy (human- or AI-authored) must pass
  the gauntlet in docs/05.

## Build the next phase, not the whole platform
Pick one task from docs/04 (e.g. "implement PolygonFeed"). Stay inside the
architecture. Run: `cd backend && python run_sim.py`, then `uvicorn app.api.main:app`.
