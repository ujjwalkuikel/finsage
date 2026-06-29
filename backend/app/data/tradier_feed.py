import datetime as dt
import urllib.request
import urllib.error
import json
import time
from app.engine.feed import Feed
from app.engine.strategy import Bar

# websockets.sync is available in websockets>=10.0
try:
    from websockets.sync.client import connect as ws_connect
except ImportError:
    ws_connect = None


class TradierFeed(Feed):
    """
    TradierFeed implements a real-time streaming feed using Tradier's markets/events API.
    Aggregates tick timesale data into 1-minute Bars.
    """
    def __init__(self, token: str, is_sandbox: bool = False):
        self.token = token
        self.base_url = "https://sandbox.tradier.com/v1" if is_sandbox else "https://api.tradier.com/v1"

    def _get_session(self) -> tuple[str, str]:
        """
        Creates a streaming session and returns (sessionid, websocket_url)
        """
        url = f"{self.base_url}/markets/events/session"
        req = urllib.request.Request(
            url,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                stream_info = data.get("stream", {})
                return stream_info.get("sessionid"), stream_info.get("url")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Tradier streaming session: {e}")

    def bars(self, symbol: str):
        if ws_connect is None:
            raise RuntimeError("websockets library is required for live streaming.")

        session_id, ws_url = self._get_session()

        # Connect synchronously to WebSocket
        print(f"Connecting to Tradier WebSocket stream for {symbol}...")
        with ws_connect(ws_url) as websocket:
            # Subscribe payload
            payload = {
                "filter": ["timesale"],
                "symbols": [symbol],
                "sessionid": session_id,
                "events": ["timesale"]
            }
            websocket.send(json.dumps(payload))

            # Initial state for 1-minute bar aggregation
            current_minute = None
            bar_open = None
            bar_high = -999999.0
            bar_low = 999999.0
            bar_close = None
            bar_volume = 0

            # Loop receiving real-time ticks
            for msg in websocket:
                tick = json.loads(msg)
                
                # Check for trade event
                if tick.get("event") == "timesale":
                    price = float(tick["price"])
                    size = int(tick["size"])
                    tick_time_ms = int(tick["time"])
                    
                    # Convert to datetime in New York time
                    dt_tick = dt.datetime.fromtimestamp(tick_time_ms / 1000.0, tz=dt.timezone.utc)
                    dt_ny = dt_tick.astimezone(dt.timezone(dt.timedelta(hours=-4)))  # simple EST/EDT offset
                    
                    minute_str = dt_ny.strftime("%Y-%m-%dT%H:%M:00")

                    # If minute changes, yield the complete bar
                    if current_minute is not None and minute_str != current_minute:
                        yield Bar(
                            time=current_minute,
                            open=round(bar_open, 3),
                            high=round(bar_high, 3),
                            low=round(bar_low, 3),
                            close=round(bar_close, 3),
                            volume=bar_volume
                        )
                        # Reset aggregation values
                        bar_open = None
                        bar_high = -999999.0
                        bar_low = 999999.0
                        bar_volume = 0

                    current_minute = minute_str
                    if bar_open is None:
                        bar_open = price
                    bar_high = max(bar_high, price)
                    bar_low = min(bar_low, price)
                    bar_close = price
                    bar_volume += size
