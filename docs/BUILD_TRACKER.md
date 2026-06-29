# BUILD_TRACKER.md — AII Platform

A granular, commit-sized task list so every change is small enough to review and
you always know what's going on. This is the single place to track progress.

---

## How to use this

- **One task = one commit = one review.** Don't let an agent batch many tasks
  into one giant change — that's the thing that makes a project hard to follow.
- Each task has an **ID** (e.g. `T2.3`). To delegate, say: *"Do T2.3 only. Stop
  and show me the diff."*
- A task is **done** only when its "Done when" is true *and* `cd backend &&
  python run_sim.py` still runs (nothing is broken).
- Work **top to bottom**. Later tasks assume earlier ones are done.
- Update the checkbox (`[ ]` → `[x]`) yourself after you've reviewed and
  committed — that keeps you, not the AI, in control of what's "real."

**Status legend:** `[ ]` todo · `[x]` done · `[~]` in progress · `[!]` blocked

---

## Phase 0 — Repo hygiene (do first, ~half a day)

- [x] **T0.1** — `git init`, add a `.gitignore` (ignore `trades.db`, `__pycache__`,
  `node_modules`, `.env`). *Done when:* `git status` is clean except source files.
- [x] **T0.2** — Add `.env.example` listing every key from `core/config.py`
  (POLYGON_API_KEY, TRADIER_TOKEN, …) with blank values. *Done when:* a newcomer
  knows exactly which secrets to set.
- [x] **T0.3** — Set up `pytest` + a trivial `tests/test_smoke.py` that imports
  the engine and asserts a sim produces ≥1 trade. *Done when:* `pytest` passes.
- [x] **T0.4** — Add a `Makefile` (or `justfile`) with `sim`, `serve`, `test`,
  `web` targets. *Done when:* `make sim` runs the simulation.
- [x] **T0.5** — First commit: the scaffold as-is. *Done when:* clean history starts.

---

## Phase 1 — Deterministic spine ✅ (already built)

- [x] **T1.1** — `Bar` / `Signal` / `Strategy` interfaces (`engine/strategy.py`)
- [x] **T1.2** — SQLite ledger + stats (`engine/db.py`)
- [x] **T1.3** — `SimExecution` with % risk sizing + slippage (`engine/execution.py`)
- [x] **T1.4** — `MockFeed` synthetic bars (`engine/feed.py`)
- [x] **T1.5** — The loop (`engine/engine.py`) + `run_sim.py`
- [x] **T1.6** — FastAPI API + minimal dashboard (`api/main.py`, `static/index.html`)
- [x] **T1.7** — One reference strategy: Rayner-Teo pullback

---

## Phase 2 — Validation gauntlet + strategies

### Validation (`app/validation/`)
- [x] **T2.1** — Backtest result object: a function that runs a strategy over a
  bar list and returns trades + metrics (expectancy R, profit factor, max DD,
  win rate, # trades). *Done when:* metrics match the dashboard's numbers.
- [x] **T2.2** — In-sample report + overfit smell-test helper. *Done when:* it
  flags a strategy with suspiciously high win rate / too many params.
- [x] **T2.3** — Bar-permutation utility (block bootstrap, preserves volatility).
  *Done when:* a unit test shows permuted series keep similar volatility.
- [x] **T2.4** — Monte Carlo permutation test (re-run on N permutations, return
  p-value). *Done when:* returns a p-value for a given strategy + data.
- [x] **T2.5** — Walk-forward runner (train window → test window, roll forward).
  *Done when:* returns out-of-sample equity for a strategy.
- [x] **T2.6** — Walk-forward permutation test (p-value on OOS data). *Done when:*
  returns a p-value for the walk-forward result.
- [x] **T2.7** — Cross-sectional runner (same strategy across many CSVs, report
  the per-ticker distribution). *Done when:* prints a distribution table.
- [x] **T2.8** — `validate(strategy, data)` that chains all four steps + a verdict
  (pass/fail). *Done when:* one call gives a full report.

### Strategies (`app/engine/strategies/` — one file each)
- [x] **T2.9** — ORB (opening range breakout). *Done when:* it backtests and the
  trade logic matches the spec in docs/05.
- [ ] **T2.10** — PDH/PDL breakout + failed-break reversal.
- [ ] **T2.11** — Donchian / Turtle breakout (ATR sizing).
- [ ] **T2.12** — RSI(2) Connors mean reversion.
- [ ] **T2.13** — VWAP (needs session-start handling — see T3.x). *Note:* defer
  until the feed provides intraday session boundaries.
- [ ] **T2.14** — Gap-fade (with a placeholder catalyst filter flag).
- [ ] **T2.15** — Register all strategies; dashboard shows per-strategy stats.
  *Done when:* multiple strategies appear side by side in the table.

---

## Phase 3 — Real data + React dashboard

### Data adapters (`app/data/`)
- [ ] **T3.1** — `PolygonFeed`: fetch daily bars for one symbol (1 call).
  *Done when:* real NVDA daily bars flow into the engine.
- [ ] **T3.2** — CSV cache layer (save/load pulled bars). *Done when:* a second
  run reads from disk, no re-fetch.
- [ ] **T3.3** — `PolygonFeed` minute bars with `next_url` pagination + rate-limit
  sleep. *Done when:* 2yr of minute bars for one symbol pulls cleanly.
- [ ] **T3.4** — Session-boundary support in the feed (so ORB/VWAP know the open).
  *Done when:* VWAP (T2.13) can be enabled.
- [ ] **T3.5** — `AlpacaFeed` (free live stream) OR `TradierFeed` (consolidated).
  *Done when:* live bars stream into the engine for a watchlist.
- [ ] **T3.6** — Universe module: a fixed diverse watchlist + a stub
  `build_daily_universe()`. *Done when:* the engine loops over the watchlist.

### Frontend (`frontend/`)
- [ ] **T3.7** — `npm install`, confirm the skeleton runs against the live backend.
  *Done when:* the React dashboard shows real sim data at localhost:5173.
- [ ] **T3.8** — Add an equity-curve chart (per strategy). *Done when:* curve renders.
- [ ] **T3.9** — Strategy comparison view (a row per strategy with its metrics).
  *Done when:* you can compare strategies at a glance.
- [ ] **T3.10** — Validation results panel (show p-values / walk-forward verdict).
  *Done when:* a strategy's gauntlet result is visible in the UI.

---

## Phase 4 — First agent (analysis only, no execution)

- [ ] **T4.1** — LLM client wrapper (Groq/Cerebras) reading key from config.
  *Done when:* a test prompt returns a completion.
- [ ] **T4.2** — Engine-as-tools: expose "get indicators for symbol" and "run
  backtest" as callable tools. *Done when:* a function returns real numbers.
- [ ] **T4.3** — `TechnicalAgent.run()`: call tools → LLM interprets → structured
  result (conclusion + evidence + inputs used). *Done when:* a ticker returns an
  evidence-backed analysis. **No execution.**
- [ ] **T4.4** — API endpoint `POST /api/analyze {ticker}`. *Done when:* curl
  returns the analysis JSON.
- [ ] **T4.5** — Telegram bot: receive a ticker, call `/api/analyze`, reply.
  *Done when:* you DM a ticker and get the analysis back.
- [ ] **T4.6** — Explainability check: every analysis lists which indicators/data
  it used. *Done when:* no "black box" outputs.

---

## Phase 5 — Memory + more agents + orchestrator

- [ ] **T5.1** — Vector DB setup (Chroma/pgvector) + an `add`/`query` wrapper.
- [ ] **T5.2** — Store every analysis + decision as a memory record (with metadata).
- [ ] **T5.3** — RAG retrieval: "why did we look at X before?" returns past records.
- [ ] **T5.4** — `PortfolioAgent`: reads holdings, reports concentration/sector exposure.
- [ ] **T5.5** — `NewsAgent`: Finnhub news → LLM catalyst classification → tag.
- [ ] **T5.6** — `MacroAgent`: pulls a few macro signals, labels the regime.
- [ ] **T5.7** — `RiskAgent` (reads deterministic limits, can flag/veto — never sets them).
- [ ] **T5.8** — `ThesisAgent`: store the "why" of a position; later check if it holds.
- [ ] **T5.9** — `ReflectionAgent`: grade past predictions against outcomes.
- [ ] **T5.10** — LangGraph orchestrator: wire agents into a graph + a synthesis node.
- [ ] **T5.11** — Synthesis output is explainable (which agent contributed what).
- [ ] **T5.12** — Knowledge endpoints: ask the system about its own past.

---

## Phase 6 — Agentic + algorithmic execution (still simulated)

- [ ] **T6.1** — Regime → strategy mapping (deterministic baseline first).
- [ ] **T6.2** — Agent selects/weights *validated* strategies for the day.
- [ ] **T6.3** — Selected strategies run through the engine into the sim ledger.
- [ ] **T6.4** — Risk module can veto an agent-selected trade. *Done when:* a
  limit breach blocks the trade and logs why.
- [ ] **T6.5** — Every agentic decision is logged with full reasoning.
- [ ] **T6.6** — Prove it beats the naive "run all strategies flat" baseline OOS
  before trusting the router. *Done when:* a comparison report exists.

---

## Phase 7 — Live trading + human approval

- [ ] **T7.1** — `LiveExecution` mirroring `SimExecution`'s interface (broker order
  in, real fill recorded in the SAME ledger).
- [ ] **T7.2** — Human-approval gate: nothing executes live without explicit sign-off.
- [ ] **T7.3** — Tradier order placement (long side). *Done when:* a paper/live
  order goes through and the fill lands in the ledger.
- [ ] **T7.4** — IBKR adapter for shorting + locates (when needed).
- [ ] **T7.5** — Daily max-loss / 3-strike kill switch enforced in code.
- [ ] **T7.6** — Live/sim toggle in config + clear UI indicator of which mode.

---

## Running rules (pin these)

1. The engine core stays **standard-library-only**; deps live in api/agents.
2. **Agents call the engine as tools** — they never compute indicators or set risk.
3. Judge strategies on **expectancy/profit factor/drawdown**, not win rate.
4. **Validate before trusting** — every strategy passes the gauntlet (Phase 2).
5. After every task: run `python run_sim.py`; if it breaks, the task isn't done.
