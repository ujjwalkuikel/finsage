"""
Your ledger. SQLite via the standard library — zero setup, one file on disk.
Swappable to Postgres later without touching the rest of the app: only the
connection and a few SQL strings change.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent.parent.parent / "trades.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy     TEXT    NOT NULL,
    symbol       TEXT    NOT NULL,
    side         TEXT    NOT NULL,          -- 'long' or 'short'
    qty          REAL    NOT NULL,
    entry_time   TEXT    NOT NULL,
    entry_price  REAL    NOT NULL,
    stop_price   REAL,
    target_price REAL,
    exit_time    TEXT,
    exit_price   REAL,
    pnl          REAL,                       -- realized $ P&L (NULL while open)
    pnl_r        REAL,                       -- P&L in units of initial risk (R)
    status       TEXT    NOT NULL DEFAULT 'open',  -- 'open' or 'closed'
    exit_reason  TEXT                         -- 'target' | 'stop' | 'signal' | 'eod'
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def cursor():
    conn = get_conn()
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()


def insert_open_trade(t: dict) -> int:
    with cursor() as cur:
        cur.execute(
            """INSERT INTO trades
               (strategy, symbol, side, qty, entry_time, entry_price,
                stop_price, target_price, status)
               VALUES (?,?,?,?,?,?,?,?, 'open')""",
            (t["strategy"], t["symbol"], t["side"], t["qty"], t["entry_time"],
             t["entry_price"], t["stop_price"], t["target_price"]),
        )
        return cur.lastrowid


def close_trade(trade_id: int, exit_time: str, exit_price: float,
                pnl: float, pnl_r: float, reason: str):
    with cursor() as cur:
        cur.execute(
            """UPDATE trades
               SET exit_time=?, exit_price=?, pnl=?, pnl_r=?,
                   status='closed', exit_reason=?
               WHERE id=?""",
            (exit_time, exit_price, pnl, pnl_r, reason, trade_id),
        )


def all_trades(limit: int = 500) -> list[dict]:
    with cursor() as cur:
        cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]


def stats() -> dict:
    with cursor() as cur:
        cur.execute("SELECT * FROM trades WHERE status='closed'")
        closed = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT COUNT(*) c FROM trades WHERE status='open'")
        open_count = cur.fetchone()["c"]

    if not closed:
        return {"total_trades": 0, "open_trades": open_count, "wins": 0,
                "losses": 0, "win_rate": 0.0, "total_pnl": 0.0,
                "avg_r": 0.0, "expectancy_r": 0.0, "profit_factor": 0.0}

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
        "expectancy_r": round(avg_r, 3),  # expectancy per trade, in R
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss else float("inf"),
    }


def reset():
    with cursor() as cur:
        cur.execute("DELETE FROM trades")
