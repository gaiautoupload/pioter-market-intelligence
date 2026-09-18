"""Build a small Yahoo five-minute reference snapshot for GitHub Pages.

Yahoo's chart endpoint is unofficial. Failures are explicit and never overwrite
the official TWSE end-of-day dataset.
"""
from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
MARKET = ROOT / "dist" / "data" / "market.json"
LATEST = ROOT / "dist" / "data" / "latest.json"
OUT = ROOT / "dist" / "data" / "intraday.json"


def atomic(value: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(OUT)


def yahoo_symbol(stock: dict) -> str:
    return stock["code"] + (".TWO" if stock.get("market") == "TPEX" else ".TW")


def fetch(stock: dict) -> dict:
    symbol = yahoo_symbol(stock)
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol, safe="") + "?range=1d&interval=5m"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Pioter intraday reference)"})
    with urllib.request.urlopen(request, timeout=18) as response:
        payload = json.load(response)
    result = (payload.get("chart", {}).get("result") or [None])[0]
    if not result or result.get("meta", {}).get("symbol") != symbol:
        raise ValueError("Yahoo chart schema or symbol mismatch")
    meta = result["meta"]
    price = meta.get("regularMarketPrice")
    previous = meta.get("chartPreviousClose") or meta.get("previousClose")
    stamp = meta.get("regularMarketTime")
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (price, previous, stamp)) or previous <= 0:
        raise ValueError("Yahoo quote has invalid price, previous close, or time")
    observed = datetime.fromtimestamp(stamp, timezone.utc).astimezone(TZ)
    volumes = ((result.get("indicators", {}).get("quote") or [{}])[0].get("volume") or [])
    volume = sum(v for v in volumes if isinstance(v, (int, float)) and math.isfinite(v))
    return {
        "code": stock["code"], "name": stock.get("name", ""), "market": stock.get("market", "TWSE"),
        "symbol": symbol, "price": price, "previous_close": previous,
        "change": price - previous, "change_percent": (price / previous - 1) * 100,
        "volume": volume, "observed_at": observed.isoformat(timespec="seconds"),
        "source_url": "https://tw.stock.yahoo.com/quote/" + symbol + "/",
    }


def main() -> dict:
    now = datetime.now(TZ)
    market = json.loads(MARKET.read_text(encoding="utf-8"))
    latest = json.loads(LATEST.read_text(encoding="utf-8")) if LATEST.exists() else {}
    stocks = {s["code"]: s for s in market.get("stocks", [])}
    selected = sorted(
        (s for s in market.get("stocks", []) if s.get("code") and isinstance(s.get("amount"), (int, float))),
        key=lambda s: s["amount"], reverse=True,
    )[:50]
    for item in latest.get("watchlist", []):
        if item.get("code") in stocks and all(s["code"] != item["code"] for s in selected):
            selected.append(stocks[item["code"]])
    quotes, errors = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch, stock): stock for stock in selected}
        for future in as_completed(futures):
            stock = futures[future]
            try:
                quotes.append(future.result())
            except Exception as exc:
                errors.append({"code": stock["code"], "error": type(exc).__name__ + ": " + str(exc)[:180]})
    quotes.sort(key=lambda q: q["code"])
    output = {
        "schema_version": "1.0", "generated_at": now.isoformat(timespec="seconds"),
        "trade_date": now.date().isoformat(), "source": "Yahoo Finance chart endpoint · unofficial reference",
        "coverage": "TWSE previous-session turnover top 50 plus configured watchlist",
        "refresh_minutes": 5, "status": "ready" if quotes else "error", "quotes": quotes,
        "rankings": {
            "gainers": sorted(quotes, key=lambda q: q["change_percent"], reverse=True)[:12],
            "losers": sorted(quotes, key=lambda q: q["change_percent"])[:12],
            "volume": sorted(quotes, key=lambda q: q["volume"], reverse=True)[:12],
        },
        "errors": errors,
        "limitations": [
            "Yahoo chart endpoint is unofficial and may throttle or change without notice.",
            "Rankings cover the previous-session turnover top 50, not the full Taiwan market.",
            "Values are five-minute reference quotes and are not an exchange-authorized consolidated feed.",
        ],
    }
    atomic(output)
    print(json.dumps({"quotes": len(quotes), "errors": len(errors), "generated_at": output["generated_at"]}))
    return output


if __name__ == "__main__":
    main()
