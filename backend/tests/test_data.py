import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.data.provider import DataProvider
from app.data.polygon_feed import PolygonFeed


class MockDataProvider(DataProvider):
    def __init__(self):
        self.call_count = 0

    def fetch_bars(self, symbol: str, multiplier: int, timespan: str,
                   from_date: str, to_date: str) -> list[dict]:
        self.call_count += 1
        return [
            {"time": "2024-01-01", "open": 10.0, "high": 12.0, "low": 9.5, "close": 11.0, "volume": 1000.0},
            {"time": "2024-01-02", "open": 11.0, "high": 13.0, "low": 10.5, "close": 12.0, "volume": 1500.0},
        ]


def test_polygon_feed_caching(tmp_path):
    provider = MockDataProvider()
    # Create feed pointing to a temp cache directory
    feed = PolygonFeed(
        api_key="MOCK_KEY",
        timespan="day",
        from_date="2024-01-01",
        to_date="2024-01-02",
        provider=provider
    )
    feed.cache_dir = tmp_path

    # First run: should hit provider (cache miss)
    bars_first = list(feed.bars("MOCK_STOCK"))
    assert len(bars_first) == 2
    assert provider.call_count == 1
    assert bars_first[0].close == 11.0

    # Verify cache file was created
    cache_file = feed._get_cache_path("MOCK_STOCK")
    assert cache_file.exists()

    # Second run: should load from disk (cache hit) without calling provider
    bars_second = list(feed.bars("MOCK_STOCK"))
    assert len(bars_second) == 2
    assert provider.call_count == 1  # Should still be 1 (no new provider calls)
    assert bars_second[1].high == 13.0
