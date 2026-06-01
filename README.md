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
