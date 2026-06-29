# 03 — Data Sources & Decisions

This captures every data and broker decision so they don't get re-litigated.
The short version: **Polygon for data + Tradier for execution, $0 to start,
~$29/mo at most for a long while.** The detail follows.

## 1. The core insight

No single API does everything, because **data providers and brokers are
different businesses.** Execution legally requires a broker; brokers have weak
historical depth. So a complete setup is always **one data provider + one
broker**. The jobs split like this:

| Job | What it needs | Tool |
|---|---|---|
| Backtest / validation history | deep, clean, delisted-inclusive bars | Polygon |
| Live data feed | real-time stream on a watchlist | Tradier (or Alpaca free) |
| Execution | place orders | Tradier (long) / IBKR (short) |
| Catalyst / news + float | news text, float numbers | Finnhub free + LLM |
| Screener (which symbols) | filter a universe | our own code over a feed |

## 2. Providers (what each is for, cost, limits)

### Polygon.io — the data spine
- **Free "Stocks Basic" ($0):** 100% market coverage, minute aggregates,
  corporate actions, reference data, **includes delisted tickers** (this fixes
  survivorship bias — see §4). Limits: ~5 API calls/min, ~2 years history,
  end-of-day / delayed.
- **Starter ($29/mo):** unlimited calls, 15-min delayed, 5+ years history,
  websocket (delayed), second aggregates. The upgrade when free gets tight.
- **Developer ($79) / Advanced ($199):** real-time, tick data. Only needed for
  true real-time intraday execution (deferred).
- **Role:** all historical/backtest/validation data. The free tier covers the
  entire build-and-validate phase.

### Tradier — the execution + live-data home
- Real-time **consolidated** data (full market volume, not partial) is **free
  for brokerage account holders** — no separate data fee.
- WebSocket streaming, add/remove symbols live, Level 1, US equities/options.
- Individual API tokens never expire (no OAuth dance for personal use).
- Cost: $0 data; $0.35/equity trade on Standard, or $10/mo Pro for commission-free.
- **Role:** live data feed + order execution for the long side.

### IBKR — the long-term real-money home (shorting)
- Free API; consolidated real-time data ~$1.50–4.50/mo (waived if you trade
  enough); needs ~$500 in the account to enable data.
- The one broker with real short-selling + share locates on small caps.
- **Role:** live execution when shorting is needed. Deferred.

### Alpaca — instant free start for the build
- Free real-time **IEX** data (partial volume on thin names) + free paper API.
- **Role:** the fastest $0 way to wire up a live feed while building. Swap to
  Tradier (consolidated) for better data later.

### Finnhub — float + news (free)
- Free tier (~60 calls/min) with fundamentals (float), structured news,
  earnings calendar. **Role:** the catalyst + float layer.

### Free historical extras
- **Daily bars:** decades of free EOD history from Stooq, yfinance, Tiingo,
  Alpha Vantage. Important: this makes the *full validation gauntlet free on
  daily-timeframe strategies* (see doc 05).
- **Databento:** pay-as-you-go with ~$125 starter credits — best for clean,
  one-time intraday history pulls without a subscription.

### Schwab — viable free alternative
- Free Trader API (data + execution) and the best free *manual* real-time
  scanner (thinkorswim). Catch: OAuth + app-approval friction, and the scanner
  has no API for its results. A fine alternative to Tradier, not better enough
  to switch to now.

## 3. The screener problem (important)

A broker feed streams the symbols *you ask for*; it cannot scan the whole market
for you. And **no free, real-time, full-market, automatable scanner exists** —
that's the $100+ paid product (Trade Ideas, Day Trade Dash). thinkorswim's free
scanner is real-time but manual-only.

So the screener is **our own code over a data feed**, and it runs in one of three
modes:
1. **Fixed watchlist (start here):** 20–50 liquid, diverse names, hardcoded.
   Zero infrastructure, clean data, enough to prove every strategy.
2. **Daily pre-computed universe:** once a day, a cheap EOD query builds today's
   candidate list (e.g. avg volume > 1M, price $5–500); feed those to the stream.
3. **Real-time scanner:** only needed for intraday-discovery strategies (Ross
   style). Most of our chosen strategies don't need it.

## 4. Constraints & gotchas (read before building)

- **Survivorship bias:** historical sources that drop delisted/failed tickers
  make backtests look better than reality. Polygon free keeps them — use it.
- **Free IEX feeds (Alpaca, Tiingo) under-report volume on thin small-caps** —
  fine for liquid names and plumbing; not trustworthy for small-cap VWAP /
  relative-volume signals. Tradier's consolidated feed fixes this.
- **Tradier paper environment can't stream.** Use the live data stream for the
  feed, but route orders to our own simulated executor + ledger. (We own the
  ledger anyway, so this is a non-issue.)
- **Tradier streaming session IDs are short-lived** — fetch a fresh one at
  startup and on reconnect.
- **Broker feeds stream a watchlist, not the whole market** (IBKR ~100 data
  lines). They feed deep data on candidates; they are not the screener.
- **Validation is data-hungry.** Walk-forward + 1,000 permutations needs lots of
  clean history — free deep *daily* data covers this; deep *minute* data is where
  Polygon Starter ($29) eventually earns its place.
- **One request vs many:** 2yr of *daily* bars for a symbol = 1 API call; 2yr of
  *minute* bars ≈ 4–5 paginated calls. Cache pulls to CSV; never re-pull.

## 5. The cheapest "everything" — final answer

| Phase | Data | Execution | Cost |
|---|---|---|---|
| Build + validate | Polygon free (history) + Stooq/yfinance (deep daily) | simulated (our code) | **$0** |
| Live, long side | Tradier (consolidated stream) | Tradier | **$0** data |
| Heavy validation / intraday | Polygon Starter | Tradier | **$29/mo** |
| Live, short side | IBKR data (~$0–4/mo) | IBKR | ~$0–4/mo + ~$500 parked |

**Start at $0. Maximum spend for a long time: $29/mo.** There is no cheaper
combination that covers everything; this is the answer.
