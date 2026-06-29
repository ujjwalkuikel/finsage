# 01 — Project Overview

## 1. What we're building

An **investment copilot** that combines two worlds most projects keep separate:

- **Agentic AI** — LLM agents that research markets, remember past decisions,
  explain their reasoning, and decide *what to do and why*.
- **Algorithmic trading** — a deterministic engine that computes indicators,
  backtests and validates strategies, sizes positions, and executes trades.

Traditional bots only execute fixed rules. Chatbots only answer isolated
questions. This sits between them: the AI reasons and the deterministic engine
calculates and acts, so you get both judgment and rigor.

The end product is not a chatbot and not a bot. It's a **long-term investment
partner** that accumulates knowledge about the market, the portfolio, and the
investor.

## 2. Why it exists (the problems it rejects)

1. **LLMs as crystal balls** — asking an LLM "what should I buy?" and trusting the
   invented answer. We reject this: the LLM never produces numbers, only interprets
   them.
2. **No memory** — chatbots forget yesterday's recommendation. We make memory a
   first-class citizen.
3. **No portfolio awareness** — recommending five chip stocks without noticing the
   concentration. We always reason at the portfolio level.
4. **No explainability** — "BUY, 92% confidence" with no reasoning. Every output
   must be traceable to evidence.
5. **No learning** — never checking whether past calls were right. We store
   outcomes and reflect on them.

## 3. Core philosophy (the rules every decision obeys)

1. **LLMs reason. Software calculates.** Indicators (RSI, MACD, Sharpe,
   correlations) are computed in Python; the LLM only interprets them.
2. **Everything is explainable.** Every recommendation answers: why, what
   evidence, what risks, what assumptions, which agent contributed most.
3. **Memory is first-class.** Portfolio, past analyses, theses, preferences,
   mistakes, and outcomes are all remembered.
4. **Human approval is the default.** The platform assists; it does not replace.
   Autonomous execution exists only behind multiple safety layers.
5. **Every decision becomes knowledge.** Nothing is discarded — analyses,
   theses, and outcomes are versioned and archived.
6. **Deterministic systems own risk.** An LLM never sets trade size, stop loss,
   position limits, or exposure. Code does.

## 4. The features (organized honestly into two tiers)

The full vision is large. To ship something real and avoid building fancy
scaffolding before there's a working core, features are split into two tiers.
**Tier 1 gives you a genuinely useful product on its own. Tier 2 is the
ambitious differentiator layered on top.**

### Tier 1 — Foundation (build first)

| Feature | What it does |
|---|---|
| **Deterministic strategy engine** | Runs rule-based strategies (`on_bar → signal`); the spine everything leans on. ✅ started |
| **Validation framework** | Puts any strategy through a rigorous gauntlet (permutation tests, walk-forward) to separate real edges from noise. See doc 05. |
| **Simulation / paper ledger** | Every (simulated) trade written to *our own* database with full detail. ✅ started |
| **P&L dashboard** | Clean dashboard: equity, win rate, expectancy (R), profit factor, per-strategy comparison, trade table. ✅ minimal version |
| **Live execution (later in Tier 1)** | Swap the simulated executor for a live one (Tradier/IBKR). Same ledger, same dashboard. |
| **Telegram / mobile analysis** | Send tickers, get an AI analysis back. **Analysis only — no execution on this path.** The safest first agent. |
| **Plain-English → strategy → test** | Paste a strategy description (e.g. from Reddit); an agent converts it into deterministic rules *from a vetted library of primitives*, runs the validation gauntlet, and reports honestly. If a concept isn't expressible with existing primitives, it says so and flags the code change needed — it never fakes it. |

### Tier 2 — Institutional knowledge (the differentiator)

| Feature | What it does |
|---|---|
| **Memory / RAG** | Permanent, queryable knowledge: *"Why did we buy Amazon last February?"* Every analysis and decision stored and retrievable. |
| **Thesis tracking** | Records *why* a position was opened, then continuously checks whether that thesis still holds as conditions change. |
| **Portfolio-level reasoning** | Always evaluates at the portfolio level: concentration, sector exposure, diversification, correlation risk. |
| **Self-reflection / learning** | Stores predictions, grades them against outcomes, and reports which agents/strategies are actually accurate over time. |
| **Multi-agent synthesis** | A team of specialist agents (Technical, Fundamental, News, Macro, Sentiment, Risk) whose views are synthesized, not taken in isolation. |
| **Agentic + algorithmic execution** | The agent layer decides *which validated strategy fits today's regime and portfolio*, then the deterministic engine executes it. The combination, done safely. |
| **Personalization** | Recommendations shaped by the user's risk tolerance, philosophy, and history — not generic advice. |
| **Human collaboration** | Beyond approve/reject: modify reasoning, add evidence, correct the AI — and the system learns from it. |

## 5. Non-goals (deliberately out of scope)

- Not high-frequency trading (milliseconds don't matter; reasoning quality does).
- Not a prediction machine (it evaluates probabilities, doesn't predict).
- Not a fully autonomous hedge fund (autonomy is optional, gated, and last).
- Not a general chatbot (it specializes in investment intelligence).

## 6. What success looks like

Judged across four dimensions, not just returns:

- **Engineering:** modular, clear agent boundaries, reliable state, well-tested,
  reproducible, well-logged.
- **AI:** consistent, explainable, good memory retrieval, minimal hallucination,
  structured tool use.
- **User:** less time gathering information, more confidence through transparency.
- **Learning:** hands-on mastery of modern agentic AI engineering (orchestration,
  RAG, memory, tool use, human-in-the-loop, production architecture).

## 7. The honest stance (keep this)

Most day traders lose money. This platform's job is to find the *rare real edge*
cheaply and honestly — not to manufacture confidence. Strategies must survive
rigorous validation before they're trusted; the harness reports weak strategies
as weak on purpose. Rigor is the feature.
