"""Schwab (thinkorswim) adapter for the real-money path. Preview mode by default.

Facts this is built on (checked 2026-10-16, to be confirmed with a $1 test
order once API access exists):
- Trader API, Individual tier: equities and single-leg options, live
  accounts only (no paperMoney), whole shares only.
- OAuth: access token ~30 minutes, refresh token 7 days, after which a
  person must log in again. So the Monday check-in includes a login.
- Orders: MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP; composite
  strategies TRIGGER (first-triggers-second) and OCO.

Safety:
- `live = false` in [schwab] means every order is written to
  paper/schwab_preview.json and nothing is sent.
- Even with live = true, `send_approved` only sends orders whose ids are
  listed in the approval file, which a person writes.
- Nothing here is imported by the paper engine.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

TRADER_URL = "https://api.schwabapi.com/trader/v1"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
PREVIEW_FILE = PAPER_DIR / "schwab_preview.json"
TOKEN_FILE = PAPER_DIR / "schwab_token.json"  # gitignored; holds refresh/access tokens
REFRESH_TOKEN_DAYS = 7


class SchwabError(RuntimeError):
    pass


# ---------------------------------------------------------------- order bodies

def _leg(symbol: str, qty: int, instruction: str, asset_type: str = "EQUITY") -> dict:
    return {"instruction": instruction, "quantity": int(qty), "instrument": {"symbol": symbol, "assetType": asset_type}}


def market(symbol: str, qty: int, side: str, duration: str = "DAY") -> dict:
    if qty < 1:
        raise SchwabError("Schwab API trades whole shares only")
    return {
        "orderType": "MARKET", "session": "NORMAL", "duration": duration, "orderStrategyType": "SINGLE",
        "orderLegCollection": [_leg(symbol, qty, "BUY" if side == "buy" else "SELL")],
    }


def limit(symbol: str, qty: int, side: str, price: float, duration: str = "DAY") -> dict:
    o = market(symbol, qty, side, duration)
    o.update(orderType="LIMIT", price=f"{price:.2f}")
    return o


def stop(symbol: str, qty: int, stop_price: float, duration: str = "GOOD_TILL_CANCEL") -> dict:
    """Sell stop: becomes a market sell when the price trades at or below stop_price."""
    o = market(symbol, qty, "sell", duration)
    o.update(orderType="STOP", stopPrice=f"{stop_price:.2f}")
    return o


def trailing_stop(symbol: str, qty: int, trail_pct: float, duration: str = "GOOD_TILL_CANCEL") -> dict:
    """Sell trailing stop that follows the last price up by trail_pct (e.g. 0.10 = 10%)."""
    o = market(symbol, qty, "sell", duration)
    o.update(orderType="TRAILING_STOP", stopPriceLinkBasis="LAST", stopPriceLinkType="PERCENT",
             stopPriceOffset=round(trail_pct * 100, 2))
    return o


def first_triggers_second(first: dict, second: dict) -> dict:
    """Place `second` only after `first` fills (e.g. buy, then attach the stop)."""
    out = dict(first)
    out["orderStrategyType"] = "TRIGGER"
    out["childOrderStrategies"] = [second]
    return out


def one_cancels_other(a: dict, b: dict) -> dict:
    return {"orderStrategyType": "OCO", "childOrderStrategies": [a, b]}


def buy_with_stop(symbol: str, qty: int, trail_pct: float) -> dict:
    """The core pattern for Steward: market buy, and once filled a trailing stop rides it."""
    return first_triggers_second(market(symbol, qty, "buy"), trailing_stop(symbol, qty, trail_pct))


def whole_shares(dollars: float, price: float) -> int:
    return int(dollars // price) if price > 0 else 0


# ---------------------------------------------------------------- preview file (no credentials needed)

def load_preview(path: Path = PREVIEW_FILE) -> list[dict]:
    return json.loads(path.read_text()) if path.exists() else []


def _save_preview(items: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2) + "\n")


def preview(orders: list[dict], note: str = "", path: Path = PREVIEW_FILE) -> list[dict]:
    """Queue orders for a person to approve. Anything still unapproved from an
    earlier run is marked superseded: the newest plan is the only live one."""
    existing = load_preview(path)
    for it in existing:
        if it["status"] == "preview":
            it["status"] = "superseded"
    start = len(existing) + 1
    items = [{"id": f"p{start + i}", "status": "preview", "note": note, "order": o} for i, o in enumerate(orders)]
    _save_preview(existing + items, path)
    return items


def describe(item: dict) -> str:
    """One line for a preview item, safe for any order shape."""
    o = item.get("order", {})
    legs = o.get("orderLegCollection") or []
    leg = legs[0] if legs else {}
    kind = o.get("orderType") or o.get("orderStrategyType", "?")
    child = o.get("childOrderStrategies") or []
    extra = f" + {child[0].get('orderType', 'child')}" if child else ""
    return (f"{item.get('id', '?')}: {leg.get('instruction', '?')} {leg.get('quantity', '?')} "
            f"{leg.get('instrument', {}).get('symbol', '?')} {kind}{extra}  ({item.get('note', '')})")


# ---------------------------------------------------------------- the client

@dataclass
class Tokens:
    access_token: str
    refresh_token: str
    access_expires: float  # epoch seconds
    refresh_created: float

    def refresh_days_left(self) -> float:
        return REFRESH_TOKEN_DAYS - (time.time() - self.refresh_created) / 86400


class Schwab:
    """Minimal Trader API client. `live=False` previews instead of sending."""

    def __init__(self, app_key: str | None = None, app_secret: str | None = None, live: bool = False,
                 token_file: Path = TOKEN_FILE, callback_url: str = "https://127.0.0.1:8182",
                 account_last4: str | None = None):
        self.app_key = app_key or os.environ.get("SCHWAB_APP_KEY")
        self.app_secret = app_secret or os.environ.get("SCHWAB_APP_SECRET")
        if not self.app_key or not self.app_secret:
            raise SchwabError("Set SCHWAB_APP_KEY and SCHWAB_APP_SECRET")
        self.live = live
        self.token_file = token_file
        self.callback_url = callback_url
        self.account_last4 = account_last4
        self._tokens: Tokens | None = None
        self._account_hash: str | None = None

    # --- auth
    def login_url(self) -> str:
        q = urllib.parse.urlencode({"client_id": self.app_key, "redirect_uri": self.callback_url})
        return f"{AUTH_URL}?{q}"

    def _basic(self) -> str:
        return "Basic " + base64.b64encode(f"{self.app_key}:{self.app_secret}".encode()).decode()

    def _token_request(self, data: dict) -> Tokens:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(TOKEN_URL, data=body, method="POST",
                                     headers={"Authorization": self._basic(), "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                j = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise SchwabError(f"token request failed: {e.code} {e.read().decode()[:200]}") from None
        new_rt = j.get("refresh_token")
        if data.get("grant_type") == "refresh_token" and self._tokens and (not new_rt or new_rt == self._tokens.refresh_token):
            created = self._tokens.refresh_created  # same refresh token: the 7-day clock keeps running
            new_rt = self._tokens.refresh_token
        else:
            created = time.time()
        return Tokens(j["access_token"], new_rt or "", time.time() + int(j.get("expires_in", 1800)) - 60, created)

    def exchange_code(self, redirected_url: str) -> Tokens:
        """Finish the weekly login: paste the URL the browser landed on after approving."""
        code = urllib.parse.parse_qs(urllib.parse.urlparse(redirected_url).query).get("code", [""])[0]
        if not code:
            raise SchwabError("No code in the redirected URL")
        self._tokens = self._token_request({"grant_type": "authorization_code", "code": code, "redirect_uri": self.callback_url})
        self._save_tokens()
        return self._tokens

    def _save_tokens(self) -> None:
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)  # owner-only: it grants trading access
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(self._tokens.__dict__))

    def _load_tokens(self) -> Tokens:
        if self._tokens is None:
            if not self.token_file.exists():
                raise SchwabError(f"No Schwab login on file. Open {self.login_url()} and run `steward schwab login <redirected-url>`")
            self._tokens = Tokens(**json.loads(self.token_file.read_text()))
        if self._tokens.refresh_days_left() <= 0:
            raise SchwabError("Schwab refresh token expired (7-day limit). Log in again.")
        if time.time() >= self._tokens.access_expires:
            self._tokens = self._token_request({"grant_type": "refresh_token", "refresh_token": self._tokens.refresh_token})
            self._save_tokens()
        return self._tokens

    # --- requests
    def _request(self, method: str, path: str, body: dict | None = None):
        tok = self._load_tokens()
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{TRADER_URL}{path}", data=data, method=method,
                                     headers={"Authorization": f"Bearer {tok.access_token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode()
                loc = resp.headers.get("Location", "")
        except urllib.error.HTTPError as e:
            raise SchwabError(f"{method} {path} -> {e.code}: {e.read().decode()[:300]}") from None
        if not text:
            return {"location": loc}
        return json.loads(text)

    def account_hash(self) -> str:
        """The one account orders go to. With several accounts, [schwab] account_last4 must pick it."""
        if self._account_hash is None:
            nums = self._request("GET", "/accounts/accountNumbers")
            if not nums:
                raise SchwabError("No Schwab accounts visible to this app")
            if self.account_last4:
                match = [n for n in nums if str(n["accountNumber"]).endswith(str(self.account_last4))]
                if len(match) != 1:
                    raise SchwabError(f"account_last4={self.account_last4} matches {len(match)} accounts")
                nums = match
            elif len(nums) > 1:
                raise SchwabError("Several Schwab accounts found; set [schwab] account_last4 in rules.toml")
            self._account_hash = nums[0]["hashValue"]
        return self._account_hash

    def account(self) -> dict:
        a = self._request("GET", f"/accounts/{self.account_hash()}?fields=positions")["securitiesAccount"]
        bal = a.get("currentBalances", {})
        return {
            "equity": float(bal.get("liquidationValue", 0)),
            "cash": float(bal.get("cashAvailableForTrading", bal.get("cashBalance", 0))),
            "positions": {p["instrument"]["symbol"]: float(p.get("longQuantity", 0)) for p in a.get("positions", [])},
        }

    def send_approved(self, approved_ids: list[str], path: Path = PREVIEW_FILE) -> list[dict]:
        """Send only the previewed orders whose ids a person approved. Needs live=True."""
        if not self.live:
            raise SchwabError("Schwab adapter is in preview mode ([schwab] live = false); nothing sent")
        items = load_preview(path)
        sent = []
        for it in items:
            if it["id"] not in approved_ids or it["status"] != "preview":
                continue
            try:
                r = self._request("POST", f"/accounts/{self.account_hash()}/orders", it["order"])
                it["status"] = "sent"
                it["location"] = r.get("location", "")
                sent.append(it)
            except Exception as e:  # record it and stop; never leave a sent order looking unsent
                it["status"] = f"failed: {e}"
                _save_preview(items, path)
                raise
            _save_preview(items, path)  # after every order, so a later failure cannot cause a re-send
        return sent
