# -*- coding: utf-8 -*-
"""
main.py
-------
Multi-ticker stock analysis with 3 AI agents + Word report generation.

Usage:
    python main.py                        # uses default TICKERS list below
    python main.py AAPL MSFT GOOGL        # analyze specific tickers
    python main.py TSLA --no-cache        # skip cache for fresh data
    python main.py AAPL --no-report       # skip Word report generation
"""

import argparse
import datetime
import json
import logging
import os
import sys
import time

from dotenv import load_dotenv

# Load .env before importing agents (which needs GEMINI_API_KEY)
load_dotenv()

import agents
import data_fetcher
import report_generator

# ── Logging setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_TICKERS = ["AAPL", "NVDA", "TSLA"]

HISTORY_FILE = "analysis_history.json"

# Seconds to wait between API calls within one ticker
INTER_AGENT_DELAY = 4

# Seconds to wait between tickers (respects Gemini rate limits)
INTER_TICKER_DELAY = 10


# ── History helpers ───────────────────────────────────────────────────────────

def load_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}


def save_history(history: dict):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_trend(history: dict, ticker: str, field: str) -> str:
    records = history.get(ticker, [])
    if len(records) < 2:
        return ""
    last = records[-2].get(field)
    curr = records[-1].get(field)
    if last is None or curr is None:
        return ""
    if curr > last:
        return f" ↑ (was {last})"
    elif curr < last:
        return f" ↓ (was {last})"
    return " → (unchanged)"


# ── Per-ticker analysis ───────────────────────────────────────────────────────

def analyze_ticker(ticker: str, use_cache: bool = True) -> dict | None:
    print(f"\n{'='*55}")
    print(f"  Analyzing: {ticker}")
    print(f"{'='*55}")

    try:
        fundamentals, headlines, company_name = data_fetcher.get_stock_data(
            ticker, use_cache=use_cache
        )
    except Exception as exc:
        logger.error("Could not fetch data for %s: %s", ticker, exc)
        return None

    print(f"\n  Company: {company_name}")
    print("  Fundamentals:")
    print(data_fetcher.format_fundamentals_for_display(fundamentals))

    print("\n  Recent Headlines:")
    if headlines:
        for i, h in enumerate(headlines, 1):
            print(f"    {i}. {h}")
    else:
        print("    (none found)")

    print("\n  Running AI Agents...")

    try:
        fund_score, fund_just = agents.run_fundamental_analyst(ticker, fundamentals)
        time.sleep(INTER_AGENT_DELAY)

        sent_score, sent_just = agents.run_sentiment_analyst(ticker, headlines)
        time.sleep(INTER_AGENT_DELAY)

        val_score, val_just, risk_flags = agents.run_valuation_analyst(ticker, fundamentals)

    except Exception as exc:
        logger.error("Agent error for %s: %s", ticker, exc)
        return None

    # Weighted composite: fundamentals 40%, valuation 35%, sentiment 25%
    composite = round(fund_score * 0.40 + val_score * 0.35 + sent_score * 0.25, 1)

    print(f"\n  Agent A – Fundamentals : {fund_score}/10  {fund_just}")
    print(f"  Agent B – Sentiment    : {sent_score}/10  {sent_just}")
    print(f"  Agent C – Valuation    : {val_score}/10  {val_just}")
    if risk_flags:
        print(f"  ⚑  Risk Flags         : {' | '.join(risk_flags)}")
    print(f"  ★  Composite Score     : {composite}/10")

    # Verdict
    if sent_score > fund_score + 3:
        verdict = "⚠️  Hype > Fundamentals — potential bubble"
    elif fund_score > sent_score + 3:
        verdict = "💎 Under-the-radar — strong fundamentals, low hype"
    elif composite >= 7:
        verdict = "✅ Solid across the board"
    elif composite <= 4:
        verdict = "🔴 Multiple red flags — proceed with caution"
    else:
        verdict = "⚖️  Balanced — no strong signal either way"

    print(f"  Verdict: {verdict}")

    return {
        "ticker":       ticker,
        "company_name": company_name,
        "date":         datetime.datetime.now().isoformat(timespec="seconds"),
        "fundamentals": fundamentals,
        "headlines":    headlines,
        "fund_score":   fund_score,
        "fund_just":    fund_just,
        "sent_score":   sent_score,
        "sent_just":    sent_just,
        "val_score":    val_score,
        "val_just":     val_just,
        "risk_flags":   risk_flags,
        "composite":    composite,
        "verdict":      verdict,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI-powered multi-ticker stock analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        metavar="TICKER",
        help=f"Ticker symbols to analyze (default: {DEFAULT_TICKERS})",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the local cache and always fetch fresh data",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip Word report generation",
    )
    return parser.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    tickers = [t.upper() for t in args.tickers] if args.tickers else DEFAULT_TICKERS
    use_cache = not args.no_cache

    if use_cache:
        logger.info("Cache enabled (TTL: 4 h). Use --no-cache to bypass.")

    history = load_history()
    results = []

    for i, ticker in enumerate(tickers):
        result = analyze_ticker(ticker, use_cache=use_cache)
        if result is None:
            continue

        # Persist to history
        history.setdefault(ticker, []).append({
            "date":       result["date"],
            "fund_score": result["fund_score"],
            "sent_score": result["sent_score"],
            "val_score":  result["val_score"],
            "composite":  result["composite"],
        })

        trend = get_trend(history, ticker, "composite")
        if trend:
            print(f"  Trend (composite):{trend}")

        results.append(result)

        # Rate-limit pause between tickers (skip after last one)
        if i < len(tickers) - 1:
            print(f"\n  [Waiting {INTER_TICKER_DELAY}s between tickers…]")
            time.sleep(INTER_TICKER_DELAY)

    save_history(history)

    if not results:
        print("\nNo results to report.")
        sys.exit(1)

    if not args.no_report:
        print("\n\nGenerating Word report…")
        try:
            report_path = report_generator.generate_report(results)
            print(f"✅ Report saved to: {report_path}")
        except Exception as exc:
            logger.error("Report generation failed: %s", exc)
    else:
        logger.info("Report generation skipped (--no-report).")


if __name__ == "__main__":
    main()
