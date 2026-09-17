"""Collect an auditable TWSE end-of-day equity snapshot for the static research site."""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)
DB = ROOT / "data" / "pioter.sqlite3"
OUT = ROOT / "dist" / "data" / "market.json"
BASE = "https://openapi.twse.com.tw/v1"
ENDPOINTS = {
    "quotes": "/exchangeReport/STOCK_DAY_ALL",
    "valuation": "/exchangeReport/BWIBBU_ALL",
    "companies": "/opendata/t187ap03_L",
}


def fetch(name: str, path: str) -> tuple[list[dict], dict]:
    url = BASE + path
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "PioterResearch/1.0 (daily official open data)", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read(30_000_001)
    if len(raw) > 30_000_000:
        raise ValueError(f"{name} payload exceeds 30 MB")
    rows = json.loads(raw)
    if not isinstance(rows, list):
        raise ValueError(f"{name} schema is not a list")
    return rows, {"id": name, "url": url, "rows": len(rows), "sha256": hashlib.sha256(raw).hexdigest()}


def value(row: dict, *names: str):
    for name in names:
        if name in row and row[name] not in (None, "", "--", "---"):
            text = str(row[name]).replace(",", "").replace("X", "").strip()
            try:
                result = float(text)
                return result if math.isfinite(result) else None
            except ValueError:
                pass
    return None


def text(row: dict, *names: str) -> str:
    for name in names:
        if row.get(name) not in (None, ""):
            return str(row[name]).strip()
    return ""


def normalize_date(raw: str) -> str:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 7:  # ROC yyyMMdd
        return date(int(digits[:3]) + 1911, int(digits[3:5]), int(digits[5:7])).isoformat()
    if len(digits) == 8:
        return date(int(digits[:4]), int(digits[4:6]), int(digits[6:8])).isoformat()
    return NOW.date().isoformat()


def normalize(quotes: list[dict], valuations: list[dict], companies: list[dict]) -> list[dict]:
    valuation = {text(r, "Code", "證券代號"): r for r in valuations}
    company = {text(r, "公司代號", "Code"): r for r in companies}
    stocks = []
    for row in quotes:
        code = text(row, "Code", "證券代號")
        close = value(row, "ClosingPrice", "收盤價")
        if not code or close is None:
            continue
        change = value(row, "Change", "漲跌價差")
        volume = value(row, "TradeVolume", "成交股數")
        amount = value(row, "TradeValue", "成交金額")
        previous = close - change if change is not None else None
        change_percent = (change / previous * 100) if previous not in (None, 0) else None
        vr, cr = valuation.get(code, {}), company.get(code, {})
        stocks.append({
            "code": code,
            "name": text(row, "Name", "證券名稱"),
            "market": "TWSE",
            "industry": text(cr, "產業別", "產業類別") or "未分類",
            "close": close,
            "change": change,
            "change_percent": round(change_percent, 4) if change_percent is not None else None,
            "open": value(row, "OpeningPrice", "開盤價"),
            "high": value(row, "HighestPrice", "最高價"),
            "low": value(row, "LowestPrice", "最低價"),
            "volume": volume,
            "amount": amount,
            "transactions": value(row, "Transaction", "成交筆數"),
            "pe": value(vr, "PEratio", "本益比"),
            "pb": value(vr, "PBratio", "股價淨值比"),
            "dividend_yield": value(vr, "DividendYield", "殖利率(%)"),
        })
    return stocks


def ranking(stocks: list[dict], key: str, reverse=True, limit=12) -> list[dict]:
    rows = [s for s in stocks if s.get(key) is not None]
    return sorted(rows, key=lambda s: s[key], reverse=reverse)[:limit]


def build_strategies(stocks: list[dict]) -> list[dict]:
    liquid = [s for s in stocks if (s.get("amount") or 0) >= 100_000_000]
    return [
        {"id": "momentum", "name": "量價動能", "definition": "成交額至少 1 億元，按當日漲幅排序", "results": ranking(liquid, "change_percent", True, 10)},
        {"id": "value_yield", "name": "收益價值", "definition": "殖利率可得且本益比為正，按殖利率排序", "results": ranking([s for s in stocks if (s.get("pe") or 0) > 0], "dividend_yield", True, 10)},
        {"id": "risk_off", "name": "跌幅風險", "definition": "成交額至少 1 億元，按當日跌幅排序", "results": ranking(liquid, "change_percent", False, 10)},
    ]


def persist(stocks: list[dict], observed_at: str):
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.executescript("""
        create table if not exists stock_daily(
          trade_date text not null, code text not null, payload text not null,
          source text not null, ingested_at text not null,
          primary key(trade_date, code)
        );
        create table if not exists pipeline_runs(
          run_id text primary key, started_at text not null, status text not null,
          stock_count integer not null, details text not null
        );
        """)
        db.executemany(
            "insert or replace into stock_daily values(?,?,?,?,?)",
            [(observed_at, s["code"], json.dumps(s, ensure_ascii=False), "TWSE OpenAPI", NOW.isoformat()) for s in stocks],
        )
        db.execute(
            "insert or replace into pipeline_runs values(?,?,?,?,?)",
            (NOW.strftime("%Y%m%dT%H%M%S"), NOW.isoformat(), "ready", len(stocks), "official EOD snapshot"),
        )


def main() -> dict:
    loaded, sources, errors = {}, [], []
    for name, endpoint in ENDPOINTS.items():
        try:
            loaded[name], source = fetch(name, endpoint)
            source["status"] = "ready"
            sources.append(source)
        except Exception as exc:
            loaded[name] = []
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            sources.append({"id": name, "url": BASE + endpoint, "status": "error", "error": str(exc)})
    if not loaded["quotes"]:
        raise RuntimeError("TWSE quote snapshot unavailable; previous public file is preserved")
    stocks = normalize(loaded["quotes"], loaded["valuation"], loaded["companies"])
    observed_at = normalize_date(max((text(r, "Date", "日期") for r in loaded["quotes"]), default=""))
    output = {
        "schema_version": "1.0",
        "generated_at": NOW.isoformat(timespec="seconds"),
        "observed_at": observed_at,
        "mode": "official_eod",
        "stocks": stocks,
        "rankings": {
            "turnover": ranking(stocks, "amount"),
            "gainers": ranking(stocks, "change_percent"),
            "losers": ranking(stocks, "change_percent", False),
            "volume": ranking(stocks, "volume"),
            "yield": ranking(stocks, "dividend_yield"),
        },
        "strategies": build_strategies(stocks),
        "sources": sources,
        "errors": errors,
        "limitations": [
            "本頁為證交所盤後資料，不是即時行情。",
            "上櫃、興櫃、券商分點與完整法人資料尚待個別官方或授權 Provider。",
            "策略為可重算的條件排序，不是買賣建議；未包含手續費、滑價與回測績效。",
        ],
    }
    persist(stocks, observed_at)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(OUT)
    print(json.dumps({"stocks": len(stocks), "observed_at": observed_at, "errors": errors}, ensure_ascii=False))
    return output


if __name__ == "__main__":
    main()
