import datetime as dt
import csv
from pathlib import Path
from app.engine.feed import Feed
from app.engine.strategy import Bar
from app.data.provider import DataProvider, PolygonProvider


class PolygonFeed(Feed):
    """
    PolygonFeed handles historical bar loading from a DataProvider (defaulting to PolygonProvider)
    and implements a local CSV cache layer to prevent redundant API queries.
    """
    def __init__(self, api_key: str, timespan: str = "day", multiplier: int = 1,
                 from_date: str = "2024-01-01", to_date: str = None, provider: DataProvider = None):
        self.api_key = api_key
        self.timespan = timespan
        self.multiplier = multiplier
        self.from_date = from_date
        self.to_date = to_date or dt.date.today().isoformat()
        
        # Swappable data provider
        self.provider = provider or PolygonProvider(api_key)
        
        # Local CSV cache directory inside backend/
        self.cache_dir = Path(__file__).resolve().parent.parent.parent / "data_cache"

    def _get_cache_path(self, symbol: str) -> Path:
        filename = f"{symbol}_{self.multiplier}{self.timespan}_{self.from_date}_{self.to_date}.csv"
        return self.cache_dir / filename

    def bars(self, symbol: str):
        """
        Streams bars for a given symbol, checking local cache first.
        """
        cache_file = self._get_cache_path(symbol)

        # 1) If cache exists, load from disk
        if cache_file.exists():
            print(f"Cache hit for {symbol} ({self.timespan}). Loading from: {cache_file.name}")
            with open(cache_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield Bar(
                        time=row["time"],
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                    )
            return

        # 2) Cache miss: fetch from data provider
        print(f"Cache miss for {symbol} ({self.timespan}). Fetching from provider...")
        bars_data = self.provider.fetch_bars(
            symbol=symbol,
            multiplier=self.multiplier,
            timespan=self.timespan,
            from_date=self.from_date,
            to_date=self.to_date,
        )

        # Save to cache folder
        self.cache_dir.mkdir(exist_ok=True)
        with open(cache_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["time", "open", "high", "low", "close", "volume"])
            writer.writeheader()
            writer.writerows(bars_data)

        # Yield items
        for r in bars_data:
            yield Bar(
                time=r["time"],
                open=r["open"],
                high=r["high"],
                low=r["low"],
                close=r["close"],
                volume=r["volume"],
            )
