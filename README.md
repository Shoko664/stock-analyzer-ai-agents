# Stock Analyzer — AI Multi-Agent

Automated stock analysis using 3 AI agents powered by Google Gemini 2.5 Flash, with Word report generation.

## What It Does

Analyzes any stock ticker using three independent AI agents:
- **Agent A — Fundamentals:** Evaluates financial health (P/E, margins, debt, growth)
- **Agent B — Sentiment:** Gauges media buzz and retail enthusiasm from recent headlines
- **Agent C — Valuation:** Assesses whether the stock is overvalued or undervalued, and flags risks

Each agent scores the stock 1–10. A weighted composite score is calculated:
- Fundamentals: 40%
- Valuation: 35%
- Sentiment: 25%

A polished Word (.docx) report is generated automatically after each run.

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/stock-analyzer-ai-agents.git
cd stock-analyzer-ai-agents
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Node.js dependency (for Word report)
```bash
npm install docx
```

### 4. Add your Gemini API key
```bash
cp .env.example .env
```
Then open `.env` and add your key:



#########################################
GEMINI_API_KEY=your_key_here
Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).

## Usage

```bash
# Default tickers (AAPL, NVDA, TSLA)
python main.py

# Custom tickers
python main.py MSFT GOOGL AMZN

# Skip cache (fetch fresh data)
python main.py AAPL --no-cache

# Skip Word report
python main.py AAPL --no-report
```

## Output Example
Agent A – Fundamentals : 9/10  Exceptional margins, strong revenue growth, and healthy balance sheet.
Agent B – Sentiment    : 6/10  Moderate positive coverage with growing retail interest.
Agent C – Valuation    : 4/10  Slightly expensive relative to peers, priced for perfection.
★  Composite Score     : 6.5/10
Verdict: ⚖️  Balanced — no strong signal either way

## Tech Stack

- **Python** — core logic
- **Google Gemini 2.5 Flash** — AI agents
- **yfinance** — financial data & news headlines
- **Pydantic** — response validation
- **docx (Node.js)** — Word report generation

## Notes

- Free Gemini tier allows 20 requests/day. For more, switch to `gemini-1.5-flash` in `agents.py` (1,500 requests/day free).
- Never commit your `.env` file. It is excluded via `.gitignore`.
- Analysis history is saved locally in `analysis_history.json`.
