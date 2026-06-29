"""
The loop. This is the spine:

    for each new bar:
        update the open position (stop/target check)
        for each strategy:
            signal = strategy.on_bar(history)
            if signal and no open position: execution.enter(...)

Same loop works for a historical replay (backtest), a Monday forward-sim, or
live trading — only the Feed and Execution objects swap underneath.
"""
from .feed import Feed
from .execution import SimExecution
from .strategy import Strategy


REGISTERED_STRATEGIES: list[Strategy] = []


def register(strategy: Strategy):
    REGISTERED_STRATEGIES.append(strategy)
    return strategy


def run(symbols: list[str], feed: Feed, execution: SimExecution,
        strategies: list[Strategy] | None = None, warmup: int = 200):
    strategies = strategies or REGISTERED_STRATEGIES
    for symbol in symbols:
        history = []
        for bar in feed.bars(symbol):
            history.append(bar)
            # 1) manage any open position first
            execution.mark(symbol, bar)
            # 2) look for new entries (one position per symbol at a time)
            if len(history) < warmup:
                continue
            if execution.has_position(symbol):
                continue
            for strat in strategies:
                sig = strat.on_bar(history)
                if sig:
                    execution.enter(strat.name, symbol, sig, bar)
                    break
        # flatten anything still open at the end of the data
        execution.close_all(symbol, history[-1])
    return execution
