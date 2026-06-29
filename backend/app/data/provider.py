import datetime as dt
import urllib.request
import urllib.error
import json
import time
from zoneinfo import ZoneInfo


class DataProvider:
    """
    Abstract Base Class for financial market data providers.
    """
    def fetch_bars(self, symbol: str, multiplier: int, timespan: str,
                   from_date: str, to_date: str) -> list[dict]:
        raise NotImplementedError


class PolygonProvider(DataProvider):
    """
    Polygon/Massive.com Data Provider.
    Fetches historical bars using standard library urllib.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.eastern_tz = ZoneInfo("America/New_York")

    def _http_get(self, url: str) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": "AII-Platform"})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            # Handle rate limiting (Free tier limit is 5 requests/minute)
            if e.code == 429:
                print("Rate limit (429) hit. Sleeping for 15 seconds...")
                time.sleep(15.0)
                return self._http_get(url)
            raise e

    def fetch_bars(self, symbol: str, multiplier: int, timespan: str,
                   from_date: str, to_date: str) -> list[dict]:
        """
        Fetches bars for a given symbol.
        Returns a list of standardized bar dicts.
        """
        # Format the endpoint url
        endpoint = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        url = f"{endpoint}?adjusted=true&sort=asc&limit=50000&apiKey={self.api_key}"

        all_results = []
        next_url = url

        while next_url:
            data = self._http_get(next_url)
            results = data.get("results", [])
            all_results.extend(results)

            # Support next_url pagination (needed for dense intraday minute bars)
            next_url_part = data.get("next_url")
            if next_url_part:
                next_url = f"{next_url_part}&apiKey={self.api_key}"
            else:
                next_url = None

        # Standardize results to internal bar dicts
        standardized_bars = []
        for r in all_results:
            t_ms = r["t"]
            # Convert Unix millisecond timestamp to America/New_York time
            dt_utc = dt.datetime.fromtimestamp(t_ms / 1000.0, tz=dt.timezone.utc)
            dt_local = dt_utc.astimezone(self.eastern_tz)

            if timespan == "day":
                time_str = dt_local.strftime("%Y-%m-%d")
            else:
                time_str = dt_local.strftime("%Y-%m-%dT%H:%M:%S")

            standardized_bars.append({
                "time": time_str,
                "open": float(r["o"]),
                "high": float(r["h"]),
                "low": float(r["l"]),
                "close": float(r["c"]),
                "volume": float(r["v"]),
            })

        return standardized_bars
