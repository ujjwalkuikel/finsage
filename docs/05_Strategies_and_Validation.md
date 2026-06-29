# 05 — Strategies & Validation

Two parts: the strategies we plan to test, and the methodology that decides
which ones are actually real. The methodology matters more than any single
strategy.

## 1. The strategy library (initial set)

All are deterministic (`on_bar(bars) → Signal`) and built from price, volume,
and time — so they run on free/cheap data. Each is a separate module that
competes on the same dashboard.

| Strategy | Type | Idea | Encodes | Data note |
|---|---|---|---|---|
| **ORB** (Opening Range Breakout) | momentum | break of the first 5–15 min range sets the day's direction | trivially (price+time) | best evidence of the set; liquid names |
| **RSI(2) Connors** | mean reversion | in an uptrend, buy short-term oversold dips, exit fast | beautifully (a formula) | daily-friendly |
| **Donchian / Turtle** | trend | break N-bar high → long; exit on M-bar low; ATR sizing | designed to be mechanical | low win rate, big winners |
| **PDH/PDL** | levels | trade breaks (or failed breaks) of prior-day high/low | yes (yesterday's extremes) | simple |
| **VWAP** | trend/reversion | bias off VWAP / fade extreme deviations | yes, **but needs accurate volume** | consolidated data only |
| **Gap fade** | mean reversion | gaps tend to fill — fade toward prior close | easily, **but needs a catalyst filter** | gaps on real news *run*, don't fill |
| **Rayner-Teo pullback** | trend | trade with higher-timeframe trend, buy the pullback | yes | ✅ already implemented |

**ICT / Smart-Money (FVG, liquidity sweeps, displacement, order blocks):**
extremely *popular*, not rigorously *proven*. Much of its apparent success is
hindsight pattern-matching on loosely-defined concepts. It *is* encodable (FVG =
a 3-candle gap; sweep = failed break; displacement = range > k×ATR), but it has
many tunable knobs → high overfitting risk. Treat it as a candidate to put
through the gauntlet, not an article of faith.

**Build order (easy → hard):** ORB → PDH/PDL → Donchian → RSI(2) → VWAP →
gap-fade. Build and validate **one at a time**; a bake-off of half-tested
strategies tells you nothing.

## 2. Picking which symbols (universe)

The strategy is the hunter; the **universe** is the pool it hunts in. Don't scan
10,000 stocks live — pre-filter to a universe (see doc 03 §3):
- Start with a **fixed, diverse watchlist** (20–50 names across sectors/caps).
- Later, a **daily EOD screen** builds today's candidate list.

## 3. The validation gauntlet (the important part)

A strategy that looks good on history is usually fooling you. The gauntlet exists
to answer one question: **is this a real edge, or a pattern mined from noise?**
Four progressively meaner tests. Most strategies fail — that's the point.

### Step 1 — In-sample excellence + smell test
Optimize on in-sample data. Ask "is it excellent?" *and* "is it obviously
overfit?" A 100% win rate or 50 parameters = a red flag (overfit or data leak).
Fewer knobs = more trustworthy. (Our six have 2–3 knobs each; ICT is where this bites.)

### Step 2 — In-sample Monte Carlo permutation test
Shuffle the price data to destroy real patterns while keeping its statistical
fingerprint (use bar-permutation / block-bootstrap — **not** naive shuffling,
which destroys volatility structure). Re-optimize on the random data ~1,000
times. Real-data profit should beat ~99% of random runs (**p < 1%**). Catches
**data-mining bias** — the fact that enough parameter tries will "find" profit in
noise.

### Step 3 — Walk-forward test
Train on a window, test on the *next unseen* window, roll forward, repeat. Results
come only from data never used for tuning. This is the gold standard; never skip
it. Then judge subjectively: "is this actually worth trading?"

### Step 4 — Walk-forward Monte Carlo permutation test
Permute the *out-of-sample* data and run the walk-forward strategy on it to see
what a worthless strategy earns by luck. Your real result must sit in the lucky
tail: **p < 5%** for one year of test data, **p < 1%** for multiple years.

**If a strategy fails the gauntlet, throw it out.** That is the system working.

## 4. Cross-sectional (multi-ticker) validation

Breadth partly substitutes for depth: a real edge should work across **many
diverse, uncorrelated tickers**, not one. Done right:
- Test across **20–30 names spread over sectors and caps** (not 30 chip stocks —
  that's one test in 30 costumes).
- Use **one global parameter set**, not per-ticker tuning (per-ticker tuning =
  overfitting).
- Run the **gauntlet per ticker**; judge the **distribution** (mildly positive on
  most names ≫ hugely positive on two).
- Caveat: a single 2-year window is one *regime* for all tickers — breadth gives
  cross-sectional robustness, not *temporal* robustness. Pair it with deep daily
  history (free) to cover different eras.

## 5. Why this is free (mostly)

- The tests are just code (numpy/pandas, or VectorBT) — no paid platform.
- **Daily-timeframe** strategies can run the *entire* gauntlet on decades of free
  daily data (Stooq/yfinance/Tiingo). Most of our six have clean daily versions.
- Only **intraday/minute** strategies eventually need paid history (Polygon
  Starter $29 / Databento credits) for multi-year walk-forward.
- So: validate on free daily data first; spend on intraday data only for a
  strategy that already survived on daily.

## 6. The metric rule (don't forget)

Judge strategies on **expectancy (R), profit factor, max drawdown, and sample
size** — never win rate alone. A 70%-win strategy can lose money; a 35%-win one
can be excellent at 2:1 R. The dashboard surfaces these so the comparison is honest.

## 7. Where AI fits (later, safely)

AI never pulls the trigger. It belongs in: catalyst classification (fuzzy news →
tag), regime labeling (which strategy suits today), **strategy generation**
(propose rules from vetted primitives → the gauntlet judges them), trade
post-mortems, and natural-language control. Every AI-proposed strategy must
survive the same gauntlet before it counts — which is exactly what makes the
agentic layer safe.
