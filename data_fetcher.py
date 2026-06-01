# -*- coding: utf-8 -*-
"""
data_fetcher.py
---------------
Pulls fundamental metrics and recent news headlines for a given ticker
using yfinance. Includes a simple file-based cache (TTL: 4 hours) to
avoid redundant requests when running the tool multiple times per day.
"""

import json
import logging
import os
import time
from pathlib import Path

import yfinance as yf

logger = logging.getLogger(__name__)

# ── Cache config ──────────────────────────────────────────────────────────────

_CACHE_DIR = Path(".cache")
_CACHE_TTL = 4 * 60 * 60  # 4 hours in seconds


def _cache_path(ticker: str) -> Path:
    _CACHE_DIR.mkdir(exist_ok=True)
    return _CACHE_DIR / f"{ticker.upper()}.json"


def _load_cache(ticker: str) -> dict | None:
    path = _cache_path(ticker)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > _CACHE_TTL:
        logger.debug("Cache expired for %s (%.0f min old)", ticker, age / 60)
        return None
    with open(path) as f:
        data = json.load(f)
    logger.info("  [Cache hit] %s (%.0f min old)", ticker, age / 60)
    return data


def _save_cache(ticker: str, data: dict):
    with open(_cache_path(ticker), "w") as f:
        json.dump(data, f, indent=2)


# ── Main fetcher ──────────────────────────────────────────────────────────────

def get_stock_data(
    ticker_symbol: str,
    use_cache: bool = True,
) -> tuple[dict, list[str], str]:
    """
    Fetch fundamentals and recent headlines for a ticker.

    Returns:
        fundamentals  — dict of financial metrics
        headlines     — list of recent news titles
        company_name  — human-readable company name
    """
    ticker_symbol = ticker_symbol.upper()

    if use_cache:
        cached = _load_cache(ticker_symbol)
        if cached:
            return cached["fundamentals"], cached["headlines"], cached["company_name"]

    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    if not info or info.get("trailingPE") is None and info.get("marketCap") is None:
        logger.warning("yfinance returned sparse data for %s — ticker may be invalid.", ticker_symbol)

    # ── Fundamentals ───────────────────────────────────────────────────────
    fundamentals = {
        "trailing_pe":      info.get("trailingPE"),
        "forward_pe":       info.get("forwardPE"),
        "debt_to_equity":   info.get("debtToEquity"),
        "profit_margin":    info.get("profitMargins"),
        "revenue_growth":   info.get("revenueGrowth"),
        "return_on_equity": info.get("returnOnEquity"),
        "free_cashflow":    info.get("freeCashflow"),
        "market_cap":       info.get("marketCap"),
    }

    # ── Headlines ──────────────────────────────────────────────────────────
    try:
        news = ticker.news or []
        headlines = [
            item.get("content", {}).get("title") or item.get("title", "")
            for item in news[:6]
            if item.get("content", {}).get("title") or item.get("title")
        ][:5]
    except Exception as exc:
        logger.warning("Could not fetch headlines for %s: %s", ticker_symbol, exc)
        headlines = []

    company_name = info.get("longName") or info.get("shortName") or ticker_symbol

    payload = {
        "fundamentals": fundamentals,
        "headlines":    headlines,
        "company_name": company_name,
    }
    if use_cache:
        _save_cache(ticker_symbol, payload)

    return fundamentals, headlines, company_name


# ── Display helper ────────────────────────────────────────────────────────────

def format_fundamentals_for_display(fundamentals: dict) -> str:
    """Return a human-readable summary of fundamentals for the console."""

    def fmt(val, suffix="", prefix="", multiplier=1, decimals=2, fallback="N/A"):
        if val is None:
            return fallback
        try:
            return f"{prefix}{val * multiplier:.{decimals}f}{suffix}"
        except (TypeError, ValueError):
            return fallback

    lines = [
        f"  Trailing P/E:      {fmt(fundamentals['trailing_pe'], 'x', decimals=1)}",
        f"  Forward P/E:       {fmt(fundamentals['forward_pe'], 'x', decimals=1)}",
        f"  Profit Margin:     {fmt(fundamentals['profit_margin'], '%', multiplier=100, decimals=1)}",
        f"  Revenue Growth:    {fmt(fundamentals['revenue_growth'], '%', multiplier=100, decimals=1)}",
        f"  Debt/Equity:       {fmt(fundamentals['debt_to_equity'], decimals=1)}",
        f"  Return on Equity:  {fmt(fundamentals['return_on_equity'], '%', multiplier=100, decimals=1)}",
    ]
    return "\n".join(lines)

