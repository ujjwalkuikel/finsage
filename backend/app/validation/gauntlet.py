"""
The validation gauntlet. (Phase 2) — see docs/05_Strategies_and_Validation.md.

A strategy that looks good on history is usually fooling you. These tests decide
whether an edge is real or mined from noise. Most strategies fail — that's correct.
"""
from app.engine.strategy import Strategy, Bar
from app.engine.feed import Feed
from app.engine.execution import SimExecution
from app.engine import engine

class MemoryLedger:
    """
    An in-memory ledger mimicking the SQLite db.py connection interface.
    Prevents database pollution and optimizes performance for Monte Carlo simulation tests.
    """
    def __init__(self):
        self.trades = {}
        self.next_id = 1

    def init_db(self):
        pass

    def reset(self):
        self.trades.clear()
        self.next_id = 1

    def insert_open_trade(self, t: dict) -> int:
        trade_id = self.next_id
        self.next_id += 1
        self.trades[trade_id] = {
            "id": trade_id,
            "strategy": t["strategy"],
            "symbol": t["symbol"],
            "side": t["side"],
            "qty": t["qty"],
            "entry_time": t["entry_time"],
            "entry_price": t["entry_price"],
            "stop_price": t["stop_price"],
            "target_price": t["target_price"],
            "status": "open",
            "exit_time": None,
            "exit_price": None,
            "pnl": None,
            "pnl_r": None,
            "exit_reason": None,
        }
        return trade_id

    def close_trade(self, trade_id: int, exit_time: str, exit_price: float,
                    pnl: float, pnl_r: float, reason: str):
        if trade_id in self.trades:
            self.trades[trade_id].update({
                "exit_time": exit_time,
                "exit_price": exit_price,
                "pnl": pnl,
                "pnl_r": pnl_r,
                "status": "closed",
                "exit_reason": reason,
            })

    def all_trades(self, limit: int = 500) -> list[dict]:
        closed = sorted(self.trades.values(), key=lambda x: x["id"], reverse=True)
        return closed[:limit]

    def stats(self) -> dict:
        closed = [t for t in self.trades.values() if t["status"] == "closed"]
        open_count = sum(1 for t in self.trades.values() if t["status"] == "open")

        if not closed:
            return {
                "total_trades": 0,
                "open_trades": open_count,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_r": 0.0,
                "expectancy_r": 0.0,
                "profit_factor": 0.0,
            }

        wins = [t for t in closed if (t["pnl"] or 0) > 0]
        losses = [t for t in closed if (t["pnl"] or 0) <= 0]
        gross_win = sum(t["pnl"] for t in wins) or 0.0
        gross_loss = abs(sum(t["pnl"] for t in losses)) or 0.0
        total_pnl = sum(t["pnl"] for t in closed)
        avg_r = sum(t["pnl_r"] for t in closed) / len(closed)

        return {
            "total_trades": len(closed),
            "open_trades": open_count,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(100 * len(wins) / len(closed), 1),
            "total_pnl": round(total_pnl, 2),
            "avg_r": round(avg_r, 3),
            "expectancy_r": round(avg_r, 3),
            "profit_factor": round(gross_win / gross_loss, 2) if gross_loss else float("inf"),
        }


class ListFeed(Feed):
    """
    A custom feed that streams pre-loaded bars from a list.
    """
    def __init__(self, bars_dict: dict[str, list[Bar]]):
        self.bars_dict = bars_dict

    def bars(self, symbol: str):
        for bar in self.bars_dict.get(symbol, []):
            yield bar


def backtest(strategy: Strategy, bars: list[Bar], initial_account: float = 1000.0, risk_pct: float = 0.01) -> dict:
    """
    Runs a strategy over a bar list entirely in-memory.
    Returns trades and stats including max drawdown.
    """
    ledger = MemoryLedger()
    feed = ListFeed({"TEST": bars})
    execution = SimExecution(account_size=initial_account, risk_pct=risk_pct, ledger=ledger)

    engine.run(["TEST"], feed, execution, strategies=[strategy])

    # Retrieve trades and calculate drawdown metrics
    closed_trades = [t for t in ledger.trades.values() if t["status"] == "closed"]
    closed_trades.sort(key=lambda t: t["exit_time"] or "")

    peak = initial_account
    current = initial_account
    max_dd = 0.0

    for t in closed_trades:
        current += t["pnl"]
        peak = max(peak, current)
        dd = (peak - current) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    stats = ledger.stats()
    stats["max_dd"] = round(max_dd, 4)

    return {
        "trades": sorted(ledger.trades.values(), key=lambda x: x["id"], reverse=True),
        "stats": stats,
    }


def count_parameters(strategy: Strategy) -> int:
    """
    Count the number of user-configurable parameters of a strategy.
    Exclude private attributes.
    """
    return sum(1 for attr, val in strategy.__dict__.items()
               if not attr.startswith('_') and not callable(val))


def in_sample_report(strategy: Strategy, bars: list[Bar]) -> dict:
    """
    Runs in-sample backtest and checks for overfitting indicators:
    - Suspiciously high win rate (> 80% for >= 5 trades)
    - Suspiciously high profit factor (> 4.0 for >= 5 trades)
    - Too many parameters (> 5)
    - Low sample size (< 15 trades)
    """
    res = backtest(strategy, bars)
    stats = res["stats"]

    n_params = count_parameters(strategy)
    warnings = []

    total_trades = stats["total_trades"]
    win_rate = stats["win_rate"]
    profit_factor = stats["profit_factor"]

    if total_trades >= 5:
        if win_rate > 80.0:
            warnings.append(f"Suspiciously high win rate ({win_rate}%): Potential data leakage or overfitting.")
        if profit_factor > 4.0:
            warnings.append(f"Suspiciously high profit factor ({profit_factor}): Potential overfitting.")

    if total_trades < 15:
        warnings.append(f"Low sample size ({total_trades} trades): Statistical metrics may not be reliable.")

    if n_params > 5:
        warnings.append(f"Too many parameters ({n_params} variables): High risk of overfitting (curve fitting).")

    stats["num_parameters"] = n_params
    stats["warnings"] = warnings
    stats["overfit_risk"] = "high" if len(warnings) >= 2 else "medium" if len(warnings) == 1 else "low"

    return {
        "trades": res["trades"],
        "stats": stats,
    }


def permute_bars(bars: list[Bar], block_size: int = 10, seed: int | None = None) -> list[Bar]:
    """
    Shuffles the return series using a block bootstrap method to destroy patterns
    while preserving return volatility structure.
    Reconstructs continuous prices without artificial price gaps.
    """
    import random
    if len(bars) <= 2:
        return [b for b in bars]

    # Calculate returns and keep matching original bar ratios/volume
    returns_info = []
    for i in range(1, len(bars)):
        prev_close = bars[i-1].close
        curr_close = bars[i].close
        ret = (curr_close - prev_close) / prev_close if prev_close > 0 else 0.0

        returns_info.append({
            "ret": ret,
            "ratio_open": bars[i].open / curr_close if curr_close > 0 else 1.0,
            "ratio_high": bars[i].high / curr_close if curr_close > 0 else 1.0,
            "ratio_low": bars[i].low / curr_close if curr_close > 0 else 1.0,
            "volume": bars[i].volume,
        })

    # Divide returns_info into blocks
    blocks = []
    for i in range(0, len(returns_info), block_size):
        blocks.append(returns_info[i:i+block_size])

    # Shuffle the blocks
    rng = random.Random(seed)
    rng.shuffle(blocks)

    # Concatenate the shuffled blocks
    shuffled_returns = []
    for block in blocks:
        shuffled_returns.extend(block)

    # Reconstruct bars
    new_bars = [Bar(
        time=bars[0].time,
        open=bars[0].open,
        high=bars[0].high,
        low=bars[0].low,
        close=bars[0].close,
        volume=bars[0].volume,
    )]

    for i, info in enumerate(shuffled_returns):
        prev_close = new_bars[-1].close
        new_close = prev_close * (1.0 + info["ret"])
        new_open = new_close * info["ratio_open"]
        new_high = new_close * info["ratio_high"]
        new_low = new_close * info["ratio_low"]

        # Candle sanity checks (high >= open/close and low <= open/close)
        new_high = max(new_high, new_open, new_close)
        new_low = min(new_low, new_open, new_close)

        time_str = bars[i+1].time

        new_bars.append(Bar(
            time=time_str,
            open=round(new_open, 3),
            high=round(new_high, 3),
            low=round(new_low, 3),
            close=round(new_close, 3),
            volume=info["volume"],
        ))

    return new_bars


def monte_carlo_permutation(strategy: Strategy, bars: list[Bar], n: int = 100) -> dict:
    """
    Runs the strategy N times on permuted market data and computes
    the p-value: the probability that a random sequence matches or beats
    the strategy's real performance.
    """
    real_res = backtest(strategy, bars)
    real_expectancy = real_res["stats"]["expectancy_r"]

    if real_res["stats"]["total_trades"] == 0:
        return {
            "real_expectancy": real_expectancy,
            "p_value": 1.0,
            "n_simulations": n,
            "mean_sim_expectancy": 0.0,
            "max_sim_expectancy": 0.0,
            "message": "Strategy did not place any trades on real data.",
        }

    better_runs = 0
    sim_expectancies = []

    for i in range(n):
        permuted = permute_bars(bars, block_size=10, seed=i)
        perm_res = backtest(strategy, permuted)
        perm_expectancy = perm_res["stats"]["expectancy_r"]
        sim_expectancies.append(perm_expectancy)

        if perm_expectancy >= real_expectancy:
            better_runs += 1

    p_value = better_runs / n
    mean_sim = sum(sim_expectancies) / n
    max_sim = max(sim_expectancies) if sim_expectancies else 0.0

    return {
        "real_expectancy": round(real_expectancy, 3),
        "p_value": round(p_value, 4),
        "n_simulations": n,
        "mean_sim_expectancy": round(mean_sim, 3),
        "max_sim_expectancy": round(max_sim, 3),
        "verdict": "pass" if p_value < 0.01 else "fail",
    }


def compute_stats_from_trades(trades: list[dict], initial_account: float = 1000.0) -> dict:
    """
    Computes summary metrics (expectancy_r, profit_factor, max_dd, etc.)
    from a list of trade dictionaries.
    """
    closed = [t for t in trades if t["status"] == "closed"]
    closed.sort(key=lambda t: t["exit_time"] or "")

    if not closed:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_r": 0.0,
            "expectancy_r": 0.0,
            "profit_factor": 0.0,
            "max_dd": 0.0,
            "final_account": initial_account,
        }

    wins = [t for t in closed if (t["pnl"] or 0) > 0]
    losses = [t for t in closed if (t["pnl"] or 0) <= 0]
    gross_win = sum(t["pnl"] for t in wins) or 0.0
    gross_loss = abs(sum(t["pnl"] for t in losses)) or 0.0
    total_pnl = sum(t["pnl"] for t in closed)
    avg_r = sum(t["pnl_r"] for t in closed) / len(closed)

    # Compute max drawdown
    peak = initial_account
    current = initial_account
    max_dd = 0.0
    for t in closed:
        current += t["pnl"]
        peak = max(peak, current)
        dd = (peak - current) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    return {
        "total_trades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(100 * len(wins) / len(closed), 1),
        "total_pnl": round(total_pnl, 2),
        "avg_r": round(avg_r, 3),
        "expectancy_r": round(avg_r, 3),
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss else float("inf"),
        "max_dd": round(max_dd, 4),
        "final_account": round(current, 2),
    }


def walk_forward(strategy_class: type[Strategy], bars: list[Bar], train_size: int, test_size: int,
                 param_grid: dict[str, list] | None = None) -> dict:
    """
    Runs a rolling walk-forward optimization on the bar list.
    1. Grid searches strategy parameters on the train window.
    2. Runs the best parameter set on the unseen test window (using combined history for indicator warmup).
    3. Accumulates out-of-sample trades and computes overall stats.
    """
    import itertools

    if param_grid is None:
        # Default parameter grid for RaynerTeoPullback if matching
        if strategy_class.__name__ == "RaynerTeoPullback":
            param_grid = {
                "fast": [10, 20, 30],
                "rr": [1.5, 2.0, 2.5],
            }
        else:
            param_grid = {}

    # Generate all parameter combinations
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combinations = []
    if keys:
        for comb in itertools.product(*values):
            combinations.append(dict(zip(keys, comb)))
    else:
        combinations = [{}]  # Just run with default strategy params

    oos_trades = []
    start_idx = 0
    T = len(bars)
    initial_account = 1000.0
    current_account = initial_account

    while start_idx + train_size + test_size <= T:
        train_bars = bars[start_idx : start_idx + train_size]
        test_bars = bars[start_idx + train_size : start_idx + train_size + test_size]
        combined_bars = bars[start_idx : start_idx + train_size + test_size]

        test_start_time = test_bars[0].time
        test_end_time = test_bars[-1].time

        # 1) Parameter Optimization on Train Window
        best_params = combinations[0]
        best_metric = -999999.0
        best_trades_count = 0

        for comb in combinations:
            strat = strategy_class(**comb)
            res = backtest(strat, train_bars, initial_account=current_account)
            metric = res["stats"]["expectancy_r"]
            trades_count = res["stats"]["total_trades"]

            # Maximize expectancy, breaking ties with higher trade count
            if (metric > best_metric) or (metric == best_metric and trades_count > best_trades_count):
                best_metric = metric
                best_trades_count = trades_count
                best_params = comb

        # 2) Run Best Parameter Set on Out-Of-Sample Combined window
        strat = strategy_class(**best_params)
        combined_res = backtest(strat, combined_bars, initial_account=current_account)

        # 3) Filter trades that entered within the test window
        window_trades = [
            t for t in combined_res["trades"]
            if test_start_time <= t["entry_time"] <= test_end_time
        ]

        oos_trades.extend(window_trades)

        # Update account balance for the next window
        window_pnl = sum(t["pnl"] for t in window_trades if t["status"] == "closed")
        current_account += window_pnl

        # Roll forward
        start_idx += test_size

    # Sort accumulated OOS trades by ID/time to reconstruct stats
    # We assign clean unique IDs to OOS trades
    for idx, t in enumerate(sorted(oos_trades, key=lambda x: x["entry_time"])):
        t["id"] = idx + 1

    stats = compute_stats_from_trades(oos_trades, initial_account=initial_account)

    return {
        "trades": sorted(oos_trades, key=lambda x: x["id"], reverse=True),
        "stats": stats,
    }


def walk_forward_permutation(strategy_class: type[Strategy], bars: list[Bar], train_size: int, test_size: int,
                             param_grid: dict[str, list] | None = None, n: int = 20) -> dict:
    """
    Runs rolling walk-forward optimization N times on permuted market data and computes
    the p-value: the probability that a random sequence matches or beats
    the walk-forward strategy's out-of-sample performance.
    """
    real_wf = walk_forward(strategy_class, bars, train_size, test_size, param_grid)
    real_expectancy = real_wf["stats"]["expectancy_r"]

    if real_wf["stats"]["total_trades"] == 0:
        return {
            "real_expectancy": real_expectancy,
            "p_value": 1.0,
            "n_simulations": n,
            "mean_sim_expectancy": 0.0,
            "max_sim_expectancy": 0.0,
            "message": "Strategy did not place any OOS trades on real data.",
        }

    better_runs = 0
    sim_expectancies = []

    for i in range(n):
        permuted = permute_bars(bars, block_size=10, seed=i)
        perm_wf = walk_forward(strategy_class, permuted, train_size, test_size, param_grid)
        perm_expectancy = perm_wf["stats"]["expectancy_r"]
        sim_expectancies.append(perm_expectancy)

        if perm_expectancy >= real_expectancy:
            better_runs += 1

    p_value = better_runs / n
    mean_sim = sum(sim_expectancies) / n
    max_sim = max(sim_expectancies) if sim_expectancies else 0.0

    return {
        "real_expectancy": round(real_expectancy, 3),
        "p_value": round(p_value, 4),
        "n_simulations": n,
        "mean_sim_expectancy": round(mean_sim, 3),
        "max_sim_expectancy": round(max_sim, 3),
        "verdict": "pass" if p_value < 0.05 else "fail",
    }


def cross_sectional(strategy: Strategy, bars_by_symbol: dict[str, list[Bar]]) -> dict:
    """
    Evaluates the strategy across multiple tickers, printing and returning the performance distribution.
    """
    results = {}

    # Header of the printed table
    print("\n" + "="*85)
    print(f" CROSS-SECTIONAL PERFORMANCE: {strategy.name.upper()} ")
    print("="*85)
    print(f"{'Symbol':<10} {'Trades':>8} {'Win Rate':>10} {'Expectancy':>12} {'Profit Factor':>15} {'Max DD':>10} {'Total P&L':>12}")
    print("-"*85)

    for symbol, bars in bars_by_symbol.items():
        res = backtest(strategy, bars)
        stats = res["stats"]
        results[symbol] = stats

        win_rate_str = f"{stats['win_rate']}%"
        expectancy_str = f"{stats['expectancy_r']} R"
        pf_str = f"{stats['profit_factor']}"
        max_dd_str = f"{round(stats['max_dd'] * 100, 1)}%"
        pnl_str = f"${stats['total_pnl']}"

        print(f"{symbol:<10} {stats['total_trades']:>8} {win_rate_str:>10} {expectancy_str:>12} {pf_str:>15} {max_dd_str:>10} {pnl_str:>12}")

    print("="*85 + "\n")
    return results


def validate(strategy_class: type[Strategy], bars: list[Bar], train_size: int, test_size: int,
             param_grid: dict[str, list] | None = None, n_sims: int = 100) -> dict:
    """
    Chains all four steps of the validation gauntlet:
    1. In-sample report & overfit smell test.
    2. Monte Carlo permutation test (p-value < 0.01).
    3. Rolling Walk-forward out-of-sample optimization.
    4. Walk-forward Monte Carlo permutation test (p-value < 0.05).
    Produces a unified PASS/FAIL verdict.
    """
    # Instantiate default strategy for in-sample runs
    default_strategy = strategy_class()

    # Step 1: In-sample report
    is_report = in_sample_report(default_strategy, bars)

    # Step 2: Monte Carlo permutation test
    mc_report = monte_carlo_permutation(default_strategy, bars, n=n_sims)

    # Step 3: Rolling walk-forward OOS test
    wf_report = walk_forward(strategy_class, bars, train_size, test_size, param_grid)

    # Step 4: Walk-forward permutation test
    wf_perm_report = walk_forward_permutation(strategy_class, bars, train_size, test_size, param_grid, n=n_sims)

    # Evaluate verdict
    is_pnl = is_report["stats"]["total_pnl"]
    mc_p = mc_report["p_value"]
    wf_expectancy = wf_report["stats"]["expectancy_r"]
    wf_p = wf_perm_report["p_value"]
    overfit_risk = is_report["stats"]["overfit_risk"]

    failures = []
    if is_pnl <= 0:
        failures.append("In-sample P&L is negative or zero.")
    if mc_p >= 0.01:
        failures.append(f"In-sample Monte Carlo p-value ({mc_p}) >= 0.01 (not statistically significant).")
    if wf_expectancy <= 0:
        failures.append(f"Out-of-sample Walk-forward expectancy ({wf_expectancy} R) is negative or zero.")
    if wf_p >= 0.05:
        failures.append(f"Walk-forward out-of-sample p-value ({wf_p}) >= 0.05.")
    if overfit_risk == "high":
        failures.append("Strategy flagged with high overfitting risk.")

    verdict = "FAIL" if failures else "PASS"

    return {
        "strategy": default_strategy.name,
        "verdict": verdict,
        "failures": failures,
        "in_sample": is_report["stats"],
        "monte_carlo": mc_report,
        "walk_forward": wf_report["stats"],
        "walk_forward_permutation": wf_perm_report,
    }
