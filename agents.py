# -*- coding: utf-8 -*-
"""
agents.py
---------
Defines the three AI agents using Google Gemini.
API key is loaded from environment variable (never hardcoded).
Includes retry logic and robust JSON parsing.
"""

import json
import logging
import os
import time
from typing import Any

import google.generativeai as genai
from pydantic import BaseModel, ValidationError, field_validator

logger = logging.getLogger(__name__)

# ── Model & API setup ─────────────────────────────────────────────────────────

MODEL_NAME = "models/gemini-2.5-flash"

_api_key = os.environ.get("GEMINI_API_KEY")
if not _api_key:
    raise EnvironmentError(
        "GEMINI_API_KEY environment variable is not set. "
        "Copy .env.example to .env and add your key, then run: "
        "`pip install python-dotenv` and load it in main.py."
    )
genai.configure(api_key=_api_key)

# ── Pydantic response models ──────────────────────────────────────────────────

class AgentScore(BaseModel):
    score: int
    justification: str

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError(f"score must be 1–10, got {v}")
        return v


class ValuationScore(BaseModel):
    score: int
    justification: str
    risk_flags: list[str] = []

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError(f"score must be 1–10, got {v}")
        return v


# ── Retry helper ──────────────────────────────────────────────────────────────

def _call_with_retry(
    model: Any,
    prompt: str,
    max_retries: int = 3,
    base_delay: float = 5.0,
) -> str:
    """Call Gemini with exponential backoff on transient errors."""
    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as exc:
            if attempt == max_retries:
                logger.error("All %d attempts failed: %s", max_retries, exc)
                raise
            wait = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "Attempt %d/%d failed (%s). Retrying in %.0fs…",
                attempt, max_retries, exc, wait,
            )
            time.sleep(wait)


# ── JSON parser ───────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
    cleaned = raw.strip()
    # Remove ```json ... ``` or ``` ... ``` fences
    for fence in ("```json", "```"):
        cleaned = cleaned.replace(fence, "")
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON from agent response: %s\nRaw: %s", exc, raw)
        raise


# ── Prompts ───────────────────────────────────────────────────────────────────

FUNDAMENTAL_SYSTEM_PROMPT = """You are a strict, conservative fundamental value investor with 30 years of experience.
Your job is to evaluate a company's financial health based solely on financial metrics.
Do not consider market popularity, media buzz, or price momentum.

Analyze the provided metrics and return a JSON object with exactly two fields:
- "score": integer from 1 to 10 (1 = terrible fundamentals, 10 = exceptional fundamentals)
- "justification": one concise sentence (max 25 words) explaining your score

Scoring guide:
1-3  = Severe red flags (negative margins, extreme debt, shrinking revenue)
4-5  = Below average or mixed signals
6-7  = Healthy business with solid metrics
8-10 = Exceptional fundamentals with strong growth and profitability

Return ONLY the JSON object, no additional text or markdown."""


SENTIMENT_SYSTEM_PROMPT = """You are a behavioral economist specializing in retail market sentiment and media hype cycles.
Your job is to gauge public enthusiasm and media narrative around a stock.
Ignore balance sheets, earnings reports, and valuation ratios entirely.

Analyze the following recent news headlines and return a JSON object with exactly two fields:
- "score": integer from 1 to 10 (1 = completely ignored, 10 = peak retail euphoria/panic)
- "justification": one concise sentence (max 25 words) explaining the sentiment level

Scoring guide:
1-3  = Barely mentioned, no retail interest, forgotten by media
4-5  = Moderate coverage, mixed or neutral tone
6-7  = Notable buzz, positive narrative, growing retail attention
8-10 = Viral enthusiasm, meme energy, overwhelming bullish media frenzy

Return ONLY the JSON object, no additional text or markdown."""


VALUATION_SYSTEM_PROMPT = """You are a meticulous quantitative analyst focused on valuation multiples and risk assessment.
Your job is to determine if a stock is overvalued, undervalued, or fairly valued based on its financial metrics.

Analyze the provided metrics and return a JSON object with exactly three fields:
- "score": integer from 1 to 10 (1 = severely overvalued/bubble, 10 = deeply undervalued/bargain)
- "justification": one concise sentence (max 25 words) explaining your valuation score
- "risk_flags": list of short strings for specific quantitative risks (e.g. "Extremely high P/E"). Empty list [] if none.

Scoring guide:
1-3  = Severely overvalued, dangerous multiples
4-5  = Slightly expensive / priced for perfection
6-7  = Fairly valued
8-10 = Undervalued, excellent margin of safety

Return ONLY the JSON object, no additional text or markdown."""


# ── Agent runners ─────────────────────────────────────────────────────────────

def run_fundamental_analyst(ticker: str, fundamentals: dict) -> tuple[int, str]:
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = (
        f"{FUNDAMENTAL_SYSTEM_PROMPT}\n\n"
        f"Ticker: {ticker}\n\n"
        f"Financial Metrics:\n{json.dumps(fundamentals, indent=2)}"
    )
    raw = _call_with_retry(model, prompt)
    data = AgentScore.model_validate(_parse_json(raw))
    return data.score, data.justification


def run_sentiment_analyst(ticker: str, headlines: list[str]) -> tuple[int, str]:
    model = genai.GenerativeModel(MODEL_NAME)
    headline_block = "\n".join(f"- {h}" for h in headlines) if headlines else "No headlines available."
    prompt = (
        f"{SENTIMENT_SYSTEM_PROMPT}\n\n"
        f"Ticker: {ticker}\n\n"
        f"Recent Headlines:\n{headline_block}"
    )
    raw = _call_with_retry(model, prompt)
    data = AgentScore.model_validate(_parse_json(raw))
    return data.score, data.justification


def run_valuation_analyst(ticker: str, fundamentals: dict) -> tuple[int, str, list[str]]:
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = (
        f"{VALUATION_SYSTEM_PROMPT}\n\n"
        f"Ticker: {ticker}\n\n"
        f"Financial Metrics:\n{json.dumps(fundamentals, indent=2)}"
    )
    raw = _call_with_retry(model, prompt)
    data = ValuationScore.model_validate(_parse_json(raw))
    return data.score, data.justification, data.risk_flags
