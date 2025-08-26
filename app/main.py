from typing import Any, Dict
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import (
    CandleRequest, IndicatorRequest, IndicatorResponse, SignalResponse,
    BacktestRequest, BacktestResult, AICommentaryRequest
)
from app.services.market_data import fetch_candles, to_dataframe
from app.services.indicators import compute_indicators, attach
from app.services.strategy import ema_rsi_macd_signal
from app.services.ai_commentary import generate_commentary
from app.services.backtest import run_backtest_ema_rsi_macd
from app.utils.risk import risk_buckets, stoploss_takeprofit
from app.deps import require_groq_api_key

app = FastAPI(title="AI Trading Backend", version="1.0.0")

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")] if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "data_source": settings.DATA_SOURCE, "default_symbol": settings.DEFAULT_SYMBOL}

@app.post("/candles")
async def get_candles(req: CandleRequest):
    candles = await fetch_candles(req.symbol, req.interval, req.limit)
    return {"symbol": req.symbol, "interval": req.interval, "count": len(candles), "candles": candles}

@app.post("/indicators", response_model=IndicatorResponse)
async def indicators(req: IndicatorRequest):
    candles = await fetch_candles(req.symbol, req.interval, req.limit)
    df = to_dataframe(candles)
    inds = compute_indicators(
        df,
        rsi_length=req.rsi_length,
        ema_fast=req.ema_fast,
        ema_slow=req.ema_slow,
        bb_length=req.bb_length,
        bb_std=req.bb_std,
    )
    df = attach(df, inds)
    # Build indicator snapshot for the last row only (plus last N if needed)
    last = df.iloc[-1].to_dict()
    indicators = {
        "rsi": float(last["rsi"]),
        "ema_fast": float(last["ema_fast"]),
        "ema_slow": float(last["ema_slow"]),
        "bb_lower": float(last["bb_lower"]),
        "bb_mid": float(last["bb_mid"]),
        "bb_upper": float(last["bb_upper"]),
        "macd": float(last["macd"]),
        "macd_signal": float(last["macd_signal"]),
        "macd_hist": float(last["macd_hist"]),
        "close": float(last["close"]),
    }
    # Return the original candle array as well
    return IndicatorResponse(symbol=req.symbol, interval=req.interval, candles=candles, indicators=indicators)

@app.post("/signal", response_model=SignalResponse)
async def signal(req: IndicatorRequest, _=Depends(require_groq_api_key)):
    candles = await fetch_candles(req.symbol, req.interval, req.limit)
    df = to_dataframe(candles)
    inds = compute_indicators(
        df,
        rsi_length=req.rsi_length,
        ema_fast=req.ema_fast,
        ema_slow=req.ema_slow,
        bb_length=req.bb_length,
        bb_std=req.bb_std,
    )
    df = attach(df, inds)

    sig, conf, rationale = ema_rsi_macd_signal(df)

    # crude volatility proxy using Bollinger % width
    last = df.iloc[-1]
    bb_width_pct = (last["bb_upper"] - last["bb_lower"]) / last["bb_mid"] * 100 if last["bb_mid"] else 0.0
    risk = {"volatility_pct": round(float(bb_width_pct), 2), "bucket": risk_buckets(float(bb_width_pct))}
    levels = stoploss_takeprofit(last_price=float(last["close"]), atr_like_pct=float(bb_width_pct))

    # Prepare snapshot for AI commentary
    snapshot = {
        "symbol": req.symbol,
        "interval": req.interval,
        "price": round(float(last["close"]), 6),
        "rsi": round(float(last["rsi"]), 2),
        "ema_fast": round(float(last["ema_fast"]), 6),
        "ema_slow": round(float(last["ema_slow"]), 6),
        "macd": round(float(last["macd"]), 6),
        "macd_signal": round(float(last["macd_signal"]), 6),
        "bb_width_pct": risk["volatility_pct"],
        "signal": sig,
        "confidence": conf,
        "levels": levels,
    }
    rationale_text = generate_commentary(snapshot, style="concise")

    return SignalResponse(
        symbol=req.symbol,
        interval=req.interval,
        signal=sig,
        confidence=conf,
        rationale=rationale_text,
        risk=risk,
        levels=levels
    )

@app.post("/backtest", response_model=BacktestResult)
async def backtest(req: BacktestRequest):
    candles = await fetch_candles(req.symbol, req.interval, req.limit)
    if len(candles) < 100:
        raise HTTPException(status_code=400, detail="Not enough candles for backtest.")
    df = to_dataframe(candles)

    # compute indicators
    from app.services.indicators import compute_indicators, attach
    inds = compute_indicators(df)
    df = attach(df, inds)

    # generate signals row-wise (simple, not vectorized for clarity)
    sigs = []
    for i in range(len(df)):
        if i < 50:
            sigs.append("HOLD")
            continue
        sub = df.iloc[:i+1]
        s, _, _ = ema_rsi_macd_signal(sub)
        sigs.append(s)
    df["signal"] = sigs

    stats = run_backtest_ema_rsi_macd(df, fee_bps=req.fee_bps)

    return BacktestResult(
        symbol=req.symbol, interval=req.interval,
        n_trades=stats["n_trades"], win_rate=stats["win_rate"],
        pnl_pct=stats["pnl_pct"], max_drawdown_pct=stats["max_drawdown_pct"],
        sharpe=stats["sharpe"], equity_curve=stats["equity_curve"],
        notes="Naive long/flat backtest with fees, no slippage."
    )

@app.post("/ai/commentary")
async def ai_commentary(req: AICommentaryRequest, _=Depends(require_groq_api_key)):
    text = generate_commentary(req.snapshot, style=req.style)
    return {"commentary": text}
