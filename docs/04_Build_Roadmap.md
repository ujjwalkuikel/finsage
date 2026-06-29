# 04 — Build Roadmap

The guiding rule: **build the foundation up, never the fancy parts first.** The
classic failure of an ambitious AI project is building the agent scaffolding
before there's a working engine for the agents to reason about. Each phase below
is usable on its own, and each one only *adds* a layer — nothing gets rewritten.

```
Phase 1  Deterministic spine        ← you are here
Phase 2  Validation gauntlet
Phase 3  Real data + dashboard
Phase 4  First agent (analysis only)
Phase 5  Memory + more agents + orchestrator
Phase 6  Agentic + algo execution
Phase 7  Human approval + live trading
```

---

## Phase 1 — Deterministic spine (✅ started)
Strategy interface, simulated execution, ledger, the loop, a minimal dashboard.
**Done when:** a strategy runs end-to-end and a trade appears in the ledger and
dashboard. *(Already working in `backend/`.)*

## Phase 2 — Validation gauntlet
The rigorous testing from doc 05: in-sample check → Monte Carlo permutation test
→ walk-forward → walk-forward permutation. Plus cross-sectional (multi-ticker)
testing. **Done when:** you can put any strategy through the gauntlet and get an
honest verdict (p-values, walk-forward P&L). Build the six strategies here too,
so the gauntlet has real targets.

## Phase 3 — Real data + dashboard
Write `PolygonFeed` (historical/backtest) and `TradierFeed`/`AlpacaFeed` (live
stream) behind the existing feed interface. Build out the React + shadcn
dashboard. **Done when:** strategies run on real market data and results show in
the clean dashboard. This alone is a genuinely useful backtesting product.

## Phase 4 — First agent (analysis only)
One agent — the **Technical/Research Agent** — reachable from the web app and/or
**Telegram**. It calls the engine as a tool, gets real indicators, and writes an
English explanation. **No execution.** **Done when:** you send a ticker and get
back an evidence-backed analysis. *This is the moment agentic + algo are married
in the codebase* — the smallest proof of the whole pattern.

## Phase 5 — Memory + more agents + orchestrator
Add the vector DB (memory/RAG), the Portfolio / News / Macro / Risk / Thesis /
Reflection agents, and LangGraph to coordinate them. **Done when:** the system
can answer knowledge questions ("why did we buy X?", "are we over-concentrated?")
and synthesize multiple agents' views with explainability.

## Phase 6 — Agentic + algo execution
The agent layer selects/weights *validated* strategies based on regime and
portfolio; the deterministic engine executes; the risk module can veto. Still
simulated. **Done when:** the AI decides which validated strategy to deploy and
the engine trades it in simulation, with full reasoning logged.

## Phase 7 — Human approval + live trading
Add the human-approval gate and swap `SimExecution` for `LiveExecution`
(Tradier/IBKR). Same ledger, same dashboard. **Done when:** a real trade is
placed only after sign-off, recorded in the same ledger as the sims.

---

## Feature → phase map

| Feature (from doc 01) | Phase |
|---|---|
| Strategy engine, ledger | 1 |
| Validation framework | 2 |
| The six strategies | 2 |
| Real data feeds | 3 |
| P&L dashboard (polished) | 3 |
| Telegram analysis (no execution) | 4 |
| Plain-English → strategy → test | 4–5 (needs engine + validation + an agent) |
| Memory / RAG, thesis, reflection, portfolio reasoning, multi-agent | 5 |
| Agentic + algorithmic execution | 6 |
| Live execution + human approval | 7 |

## How to work with an AI coding agent on this

Hand the agent the repo and point it at **one phase task at a time**, e.g.
"implement `PolygonFeed` per docs 02 §5 and 03." The docs + `CLAUDE.md`/
`AGENTS.md` give it the guardrails; a scoped task keeps it from wandering.
Never ask it to "build the platform" — ask it to build the next phase.
