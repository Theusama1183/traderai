# AI Trading Backend (FastAPI + GroqCloud)

This backend computes indicators, produces Buy/Sell/Hold signals, runs a quick backtest, and generates AI commentary using **GroqCloud** (`llama-3.1-70b-versatile`).

## Features
- Data sources: **Binance** (default) or **Yahoo Finance** (no API key)
- Indicators: RSI, EMA (fast/slow), Bollinger Bands, MACD
- Strategy: EMA/RSI/MACD ensemble → Buy/Sell/Hold + confidence
- Risk: simple volatility bucket + auto stop-loss & take-profit levels
- AI layer: concise/detailed commentary with GroqCloud
- Backtest: naive long/flat with fees, equity curve, win rate, MDD, Sharpe
- No database, no cron jobs—clean & minimal

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and add GROQ_API_KEY
uvicorn app.main:app --reload --port 8080
