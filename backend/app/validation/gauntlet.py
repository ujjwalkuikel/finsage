"""
The validation gauntlet. (Phase 2) — see docs/05_Strategies_and_Validation.md.

A strategy that looks good on history is usually fooling you. These tests decide
whether an edge is real or mined from noise. Most strategies fail — that's correct.

Pipeline:
  1. in_sample_report()            -> excellence + overfit smell test
  2. monte_carlo_permutation()     -> beat ~99% of randomized runs (p < 0.01)
  3. walk_forward()                -> train/test on rolling unseen windows
  4. walk_forward_permutation()    -> p < 0.05 (1yr) / < 0.01 (multi-yr)
  cross_sectional()                -> same rules across many diverse tickers

Use bar-permutation / block-bootstrap (NOT naive shuffle) to preserve volatility.
"""
from app.engine.strategy import Strategy


def in_sample_report(strategy: Strategy, bars: list) -> dict:
    raise NotImplementedError("Phase 2")


def monte_carlo_permutation(strategy: Strategy, bars: list, n: int = 1000) -> dict:
    raise NotImplementedError("Phase 2")


def walk_forward(strategy: Strategy, bars: list, train: int, test: int) -> dict:
    raise NotImplementedError("Phase 2")


def cross_sectional(strategy: Strategy, bars_by_symbol: dict) -> dict:
    raise NotImplementedError("Phase 2")
