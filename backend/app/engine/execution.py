"""
Your simulated broker. THIS is the piece that replaces a broker sandbox: it
owns the fill logic and writes every trade to YOUR table. When you go live, you
swap this one class for a LiveExecution that sends orders to Tradier/IBKR and
records the real fill in the SAME table — nothing else in the app changes.

Position sizing follows your worksheet: risk a fixed % of account per trade,
size = risk_dollars / per-share-risk.
"""
from . import db
from .strategy import Signal, Bar


class SimExecution:
    def __init__(self, account_size=1000.0, risk_pct=0.01, slippage_bps=5.0, ledger=None):
        self.account = account_size
        self.risk_pct = risk_pct          # 1% risk per trade by default
        self.slippage_bps = slippage_bps  # assumed slippage, in basis points
        self.open_positions = {}          # symbol -> dict
        self.ledger = ledger or db

    def _slip(self, price, side, entering):
        """Pessimistic slippage: you pay up entering, get less exiting."""
        adj = price * (self.slippage_bps / 10_000.0)
        if (side == "long") == entering:
            return price + adj
        return price - adj

    def has_position(self, symbol):
        return symbol in self.open_positions

    def enter(self, strategy_name, symbol, sig: Signal, bar: Bar):
        if symbol in self.open_positions:
            return
        fill = self._slip(sig.entry, sig.side, entering=True)
        per_share_risk = abs(fill - sig.stop)
        if per_share_risk <= 0:
            return
        risk_dollars = self.account * self.risk_pct
        qty = round(risk_dollars / per_share_risk, 4)
        if qty <= 0:
            return

        trade_id = self.ledger.insert_open_trade({
            "strategy": strategy_name, "symbol": symbol, "side": sig.side,
            "qty": qty, "entry_time": bar.time, "entry_price": round(fill, 4),
            "stop_price": round(sig.stop, 4), "target_price": round(sig.target, 4),
        })
        self.open_positions[symbol] = {
            "id": trade_id, "side": sig.side, "qty": qty, "entry": fill,
            "stop": sig.stop, "target": sig.target, "risk": per_share_risk,
            "strategy": strategy_name,
        }

    def mark(self, symbol, bar: Bar):
        """Check open position against this bar; close on stop/target hit."""
        pos = self.open_positions.get(symbol)
        if not pos:
            return
        reason = None
        if pos["side"] == "long":
            if bar.low <= pos["stop"]:
                exit_px, reason = pos["stop"], "stop"
            elif bar.high >= pos["target"]:
                exit_px, reason = pos["target"], "target"
        if reason:
            self._close(symbol, bar, exit_px, reason)

    def _close(self, symbol, bar, exit_px, reason):
        pos = self.open_positions.pop(symbol)
        fill = self._slip(exit_px, pos["side"], entering=False)
        if pos["side"] == "long":
            pnl = (fill - pos["entry"]) * pos["qty"]
        else:
            pnl = (pos["entry"] - fill) * pos["qty"]
        pnl_r = pnl / (pos["risk"] * pos["qty"]) if pos["risk"] else 0.0
        self.account += pnl
        self.ledger.close_trade(pos["id"], bar.time, round(fill, 4),
                                round(pnl, 2), round(pnl_r, 3), reason)

    def close_all(self, symbol, bar):
        if symbol in self.open_positions:
            self._close(symbol, bar, bar.close, "eod")
