"""Alpaca paper-trading connection.

Hard-wired to the paper endpoint. The client refuses to start against any
other host, so this code cannot touch a live account even by mistake.
Keys come from ALPACA_API_KEY and ALPACA_SECRET_KEY.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

PAPER_URL = "https://paper-api.alpaca.markets"


@dataclass(frozen=True)
class Account:
    equity: float
    cash: float
    blocked: bool  # trading_blocked or account_blocked


@dataclass(frozen=True)
class Position:
    symbol: str
    qty: float
    market_value: float
    current_price: float


class BrokerError(RuntimeError):
    pass


class AlpacaPaper:
    def __init__(self, key: str | None = None, secret: str | None = None, base_url: str = PAPER_URL):
        if base_url.rstrip("/") != PAPER_URL:
            raise BrokerError("Steward only connects to the Alpaca paper endpoint")
        self.key = key or os.environ.get("ALPACA_API_KEY")
        self.secret = secret or os.environ.get("ALPACA_SECRET_KEY")
        if not self.key or not self.secret:
            raise BrokerError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY")
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def configured() -> bool:
        return bool(os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_SECRET_KEY"))

    def _request(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={
                "APCA-API-KEY-ID": self.key,
                "APCA-API-SECRET-KEY": self.secret,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode()
        except urllib.error.HTTPError as e:
            raise BrokerError(f"{method} {path} -> {e.code}: {e.read().decode()[:300]}") from None
        return json.loads(text) if text else None

    def account(self) -> Account:
        a = self._request("GET", "/v2/account")
        return Account(
            equity=float(a["equity"]),
            cash=float(a["cash"]),
            blocked=bool(a.get("trading_blocked") or a.get("account_blocked")),
        )

    def positions(self) -> list[Position]:
        return [
            Position(p["symbol"], float(p["qty"]), float(p["market_value"]), float(p["current_price"]))
            for p in self._request("GET", "/v2/positions")
        ]

    def market_open(self) -> bool:
        return bool(self._request("GET", "/v2/clock")["is_open"])

    def buy_notional(self, symbol: str, dollars: float) -> str:
        """Market buy of a dollar amount (fractional shares)."""
        o = self._request("POST", "/v2/orders", {
            "symbol": symbol, "notional": f"{dollars:.2f}", "side": "buy",
            "type": "market", "time_in_force": "day",
        })
        return o["id"]

    def sell_notional(self, symbol: str, dollars: float) -> str:
        o = self._request("POST", "/v2/orders", {
            "symbol": symbol, "notional": f"{dollars:.2f}", "side": "sell",
            "type": "market", "time_in_force": "day",
        })
        return o["id"]

    def close_position(self, symbol: str) -> str:
        o = self._request("DELETE", f"/v2/positions/{symbol}")
        return o["id"] if o else ""
