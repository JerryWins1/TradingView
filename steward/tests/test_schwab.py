import json
import time

import pytest

from steward import schwab


def test_order_bodies():
    m = schwab.market("SPY", 5, "buy")
    assert m["orderType"] == "MARKET" and m["orderStrategyType"] == "SINGLE"
    assert m["orderLegCollection"][0] == {"instruction": "BUY", "quantity": 5, "instrument": {"symbol": "SPY", "assetType": "EQUITY"}}

    s = schwab.stop("SPY", 5, 693.456)
    assert s["orderType"] == "STOP" and s["stopPrice"] == "693.46" and s["duration"] == "GOOD_TILL_CANCEL"
    assert s["orderLegCollection"][0]["instruction"] == "SELL"

    t = schwab.trailing_stop("SPY", 5, 0.10)
    assert t["orderType"] == "TRAILING_STOP" and t["stopPriceLinkType"] == "PERCENT" and t["stopPriceOffset"] == 10.0

    l = schwab.limit("EFA", 3, "sell", 99.5)
    assert l["orderType"] == "LIMIT" and l["price"] == "99.50"


def test_composites_and_whole_shares():
    b = schwab.buy_with_stop("SPY", 5, 0.10)
    assert b["orderStrategyType"] == "TRIGGER" and b["orderType"] == "MARKET"
    assert b["childOrderStrategies"][0]["orderType"] == "TRAILING_STOP"
    oco = schwab.one_cancels_other(schwab.limit("SPY", 5, "sell", 800), schwab.stop("SPY", 5, 700))
    assert oco["orderStrategyType"] == "OCO" and len(oco["childOrderStrategies"]) == 2
    assert schwab.whole_shares(4500, 770.25) == 5 and schwab.whole_shares(100, 770) == 0
    with pytest.raises(schwab.SchwabError):
        schwab.market("SPY", 0, "buy")


def test_preview_mode_never_sends_and_supersedes(monkeypatch, tmp_path):
    monkeypatch.setenv("SCHWAB_APP_KEY", "k")
    monkeypatch.setenv("SCHWAB_APP_SECRET", "s")
    prev = tmp_path / "prev.json"
    items = schwab.preview([schwab.buy_with_stop("SPY", 5, 0.10)], note="core rebalance", path=prev)  # no credentials needed
    assert items[0]["id"] == "p1" and items[0]["status"] == "preview"
    assert schwab.describe(items[0]).startswith("p1: BUY 5 SPY MARKET + TRAILING_STOP")
    schwab.preview([schwab.market("EFA", 3, "sell")], note="week 2", path=prev)
    statuses = [i["status"] for i in schwab.load_preview(prev)]
    assert statuses == ["superseded", "preview"]  # last week's unapproved order is no longer live

    c = schwab.Schwab(live=False, token_file=tmp_path / "tok.json")
    with pytest.raises(schwab.SchwabError):
        c.send_approved(["p2"], path=prev)
    assert schwab.load_preview(prev)[1]["status"] == "preview"
    assert "client_id=k" in c.login_url()
    assert schwab.describe({"order": {"orderStrategyType": "OCO", "orderLegCollection": []}}).startswith("?: ? ? ? OCO")


def test_send_persists_after_each_order(monkeypatch, tmp_path):
    monkeypatch.setenv("SCHWAB_APP_KEY", "k")
    monkeypatch.setenv("SCHWAB_APP_SECRET", "s")
    prev = tmp_path / "prev.json"
    schwab.preview([schwab.market("SPY", 1, "buy"), schwab.market("EFA", 1, "buy")], path=prev)
    c = schwab.Schwab(live=True, token_file=tmp_path / "tok.json")
    c._account_hash = "H"
    calls = []

    def fake_request(method, path, body=None):
        calls.append(body["orderLegCollection"][0]["instrument"]["symbol"])
        if len(calls) == 2:
            raise schwab.SchwabError("boom")
        return {"location": "order/1"}

    monkeypatch.setattr(c, "_request", fake_request)
    with pytest.raises(schwab.SchwabError):
        c.send_approved(["p1", "p2"], path=prev)
    on_disk = {i["id"]: i["status"] for i in schwab.load_preview(prev)}
    assert on_disk["p1"] == "sent" and on_disk["p2"].startswith("failed")  # p1 can never be re-sent by accident
    assert c.send_approved(["p1", "p2"], path=prev) == []


def test_account_hash_requires_a_choice_with_several_accounts(monkeypatch, tmp_path):
    monkeypatch.setenv("SCHWAB_APP_KEY", "k")
    monkeypatch.setenv("SCHWAB_APP_SECRET", "s")
    nums = [{"accountNumber": "11111234", "hashValue": "A"}, {"accountNumber": "22225678", "hashValue": "B"}]
    c = schwab.Schwab(token_file=tmp_path / "t.json")
    monkeypatch.setattr(c, "_request", lambda m, p, b=None: nums)
    with pytest.raises(schwab.SchwabError, match="Several"):
        c.account_hash()
    c2 = schwab.Schwab(token_file=tmp_path / "t.json", account_last4="5678")
    monkeypatch.setattr(c2, "_request", lambda m, p, b=None: nums)
    assert c2.account_hash() == "B"


def test_token_expiry_rules(monkeypatch, tmp_path):
    monkeypatch.setenv("SCHWAB_APP_KEY", "k")
    monkeypatch.setenv("SCHWAB_APP_SECRET", "s")
    c = schwab.Schwab(token_file=tmp_path / "tok.json")
    with pytest.raises(schwab.SchwabError, match="No Schwab login"):
        c._load_tokens()
    old = schwab.Tokens("a", "r", time.time() + 1000, time.time() - 8 * 86400)
    (tmp_path / "tok.json").write_text(json.dumps(old.__dict__))
    with pytest.raises(schwab.SchwabError, match="expired"):
        c._load_tokens()
    fresh = schwab.Tokens("a", "r", time.time() + 1000, time.time())
    (tmp_path / "tok.json").write_text(json.dumps(fresh.__dict__))
    c._tokens = None
    assert c._load_tokens().access_token == "a"
    assert 6.9 < fresh.refresh_days_left() <= 7


def test_refresh_keeps_seven_day_clock(monkeypatch, tmp_path):
    monkeypatch.setenv("SCHWAB_APP_KEY", "k")
    monkeypatch.setenv("SCHWAB_APP_SECRET", "s")
    c = schwab.Schwab(token_file=tmp_path / "tok.json")
    created = time.time() - 3 * 86400
    c._tokens = schwab.Tokens("old", "r", time.time() - 1, created)

    class Resp:
        def __init__(self, j): self.j = j
        def read(self): return json.dumps(self.j).encode()
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(schwab.urllib.request, "urlopen", lambda req, timeout=30: Resp({"access_token": "new", "expires_in": 1800}))
    tok = c._load_tokens()
    assert tok.access_token == "new" and tok.refresh_token == "r"
    assert abs(tok.refresh_created - created) < 1  # clock not reset by a refresh that kept the same token
    assert oct((tmp_path / "tok.json").stat().st_mode & 0o777) == "0o600"
