# 02 — System Architecture

## 1. The mental model: a small investment firm

The easiest way to understand the system is as a **firm with roles**, not a
program. Every part maps to a job a real firm has:

| Firm role | System part | Job |
|---|---|---|
| Analysts | AI agents | Research, remember, explain — they **reason** |
| Quants | Deterministic engine | Compute indicators, run backtests — they **calculate** |
| Risk officer | Risk module (code only) | Enforce hard limits, can veto anyone |
| Trader | Execution layer | Places orders only after sign-off |
| Filing cabinet | Database + vector memory | Never forgets a decision |
| Front desk | Dashboard + API | Where the human talks to the firm |

The firm's constitution is the philosophy in doc 01: **analysts reason, quants
calculate, the risk officer is never an AI.**

## 2. The layers

A request flows down; an answer flows back up.

```
   ┌──────────────────────────────────────────────────────────┐
 1 │ INTERFACE   Web dashboard (React) · Telegram bot · API    │
   ├──────────────────────────────────────────────────────────┤
 2 │ API         FastAPI — receives requests, routes them       │
   ├──────────────────────────────────────────────────────────┤
 3 │ ORCHESTRATOR  LangGraph — decides which agents run, in     │
   │               what order, and passes state between them    │
   ├──────────────────────────────────────────────────────────┤
 4 │ AGENTS      Technical · Fundamental · News · Macro ·       │
   │             Sentiment · Portfolio · Risk · Memory ·        │
   │             Reflection · Thesis   (LLMs reason)            │
   │                    │ call as deterministic tools ▼          │
   ├──────────────────────────────────────────────────────────┤
 5 │ ENGINE      Strategies · indicators · validation gauntlet ·│
   │             position sizing · execution · ledger           │
   │             (software calculates)   ← WE BUILT THIS         │
   ├──────────────────────────────────────────────────────────┤
 6 │ STORAGE     SQLite/Postgres (facts) · Vector DB (memory/RAG)│
   └──────────────────────────────────────────────────────────┘
```

**The single most important arrow:** layer 4 → layer 5. When an agent needs a
hard number (an indicator, a backtest result), it **calls the deterministic
engine as a tool** and interprets the answer. It never invents the number. That
arrow is where agentic and algorithmic meet — it's the whole project in one line.

## 3. The dependency rule (what keeps it clean)

**Dependencies point one way: down.** The engine never imports the agents; the
agents import the engine. The engine must run, be tested, and be backtested with
no AI present at all. This is the philosophy enforced by structure: it guarantees
the deterministic core stays fast, reproducible, and trustworthy regardless of
what the AI layer does.

## 4. Tech stack (and why each piece)

| Concern | Choice | Why |
|---|---|---|
| Frontend | **React + Vite + Tailwind + shadcn/ui** | Produces the clean, white, minimal SaaS look (see §6); shadcn ships sidebar/card/table components that already match it; Vite is fast to develop |
| Backend | **FastAPI (Python)** | Async-native, WebSocket support, auto API docs; lives in the same language as the engine and the entire LLM ecosystem |
| Engine | **Pure-Python core** (stdlib-first) | Deterministic, testable, dependency-light; runs with zero installs |
| Agents | **LangChain** (tool calling) + **LangGraph** (orchestration) | Standard, well-supported way to wire multi-agent flows and tool use — added *later*, on top of the engine |
| LLM inference | **Groq / Cerebras / Gemini** free tiers | Fast, free, good enough for agent reasoning and classification |
| Facts DB | **SQLite → Postgres** | SQLite now (zero setup), Postgres when it grows; swap touches one module |
| Memory DB | **Chroma or pgvector** | Vector store for RAG / "remember why we did things" — Tier 2 |
| Data + execution | **Polygon + Tradier (+ IBKR later)** | See doc 03 |

**Scaffold the full structure now, fill it in incrementally.** To stay
future-ready, the project ships from day one with the complete layout in place:
the React frontend skeleton and every backend folder (engine, data, agents,
orchestrator, api, core) exist up front, so nothing has to be re-homed later.
The important distinction: *scaffolding the structure* now is good engineering;
*building out all the agents* now is the trap to avoid. So the agent and
orchestrator folders start as marked stubs — real files with clear TODOs — and
get implemented phase by phase (see doc 04). The engine and a runnable backend
work today; the React app and LangGraph agents are wired in as their phases land,
into homes that already exist.

## 5. Repository structure

```
aii-platform/
├── docs/                      # these documents
├── backend/
│   ├── app/
│   │   ├── engine/            # deterministic spine (WORKING)
│   │   │   strategy.py  execution.py  feed.py  engine.py  db.py
│   │   ├── validation/        # stub: permutation + walk-forward gauntlet
│   │   ├── data/              # stub: polygon + tradier adapters
│   │   ├── agents/            # stub: technical, news, macro, memory, risk…
│   │   ├── orchestrator/      # stub: LangGraph graph
│   │   ├── api/               # FastAPI routes (main.py — WORKING)
│   │   └── core/              # stub: config, settings, db wiring
│   ├── static/index.html      # minimal dashboard (until React is built out)
│   ├── run_sim.py
│   └── requirements.txt
└── frontend/                  # React + Vite + Tailwind + shadcn skeleton
    ├── src/ (App.jsx, components, lib)
    ├── package.json  vite.config.js  tailwind.config.js
    └── README.md
```

> Every folder above exists in the repo from day one. The engine and API are
> working code; the `validation`, `data`, `agents`, `orchestrator`, and `core`
> folders contain marked stubs (real files with TODOs) so each phase has a home
> to be implemented into. The frontend is a runnable React skeleton (run
> `npm install && npm run dev` after cloning).

Agent folders sit **beside** the engine, never inside it — preserving the
one-way dependency rule.

## 6. Frontend design direction

The brief is the clean, white, modern SaaS dashboard look seen in Tsenta, Warp,
and similar (the reference screenshots). Follow it precisely:

- **Palette:** white/near-white canvas (#FFFFFF / #F6F7FB), dark ink text
  (#0B1020), a single restrained brand accent (indigo/violet ~#6366F1), and
  semantic green/red (#16A34A / #DC2626) reserved *only* for P&L and gains/losses
  — color carries meaning, it isn't decoration.
- **Type:** a clean sans (Inter or similar) for UI; a **monospace with tabular
  figures** (JetBrains Mono) for all numbers — prices, P&L, R-multiples. Numbers
  in mono is the signature: it reads like a ledger/ticker and keeps columns
  aligned.
- **Layout:** left sidebar nav · top header with one primary action · stat cards
  in a row · a clean data table below. Generous whitespace, hairline dividers,
  ~14px radius cards, no heavy borders or shadows.
- **Components:** lean on shadcn/ui (Card, Table, Badge, Sidebar) so it's
  consistent and accessible by default.
- **Tone of copy:** plain, active, sentence case. Buttons say exactly what
  happens ("Run simulation", not "Submit"). Empty states invite action.

The minimal `static/index.html` already implements this direction (sidebar,
stat cards, monospace numbers) as a reference for the React build.

## 7. How the four headline features map onto the layers

- **Telegram analysis (no execution):** Interface (Telegram) → API → a Research
  Agent → calls Engine for indicators → returns explanation. Never reaches the
  execution layer.
- **Agentic + algo execution:** Agents decide which validated strategy fits →
  Engine executes deterministically → Risk module can veto → Ledger records it.
- **P&L dashboard:** Ledger (storage) → API → dashboard (interface).
- **English → strategy → test:** Agent translates English into a composition of
  vetted engine primitives → Validation gauntlet runs → honest report. Unknown
  concepts are flagged for a human code change, never faked.

Every feature is the same loop: **Interface → Agent reasons → calls Engine →
Ledger/Validation → back to the user.** If a future feature doesn't fit this
loop, that's the signal it needs real design thought.
