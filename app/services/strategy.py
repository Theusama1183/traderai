from typing import Tuple, Literal
import pandas as pd

def ema_rsi_macd_signal(df: pd.DataFrame) -> Tuple[Literal["BUY","SELL","HOLD"], str, str]:
    """
    Simple ensemble logic:
    - Bullish if EMA fast > EMA slow, RSI < 60, MACD > Signal
    - Bearish if EMA fast < EMA slow, RSI > 40, MACD < Signal
    Otherwise HOLD
    Returns: (signal, confidence, rationale)
    """
    last = df.iloc[-1]
    votes = []

    # EMA trend
    if last["ema_fast"] > last["ema_slow"]:
        votes.append("bullish_trend")
    elif last["ema_fast"] < last["ema_slow"]:
        votes.append("bearish_trend")

    # RSI regime
    if last["rsi"] < 30:
        votes.append("oversold")
    elif last["rsi"] > 70:
        votes.append("overbought")

    # MACD momentum
    if last["macd"] > last["macd_signal"]:
        votes.append("bullish_momentum")
    elif last["macd"] < last["macd_signal"]:
        votes.append("bearish_momentum")

    # Decide
    bull_score = sum(1 for v in votes if v.startswith("bullish")) + (1 if "oversold" in votes else 0)
    bear_score = sum(1 for v in votes if v.startswith("bearish")) + (1 if "overbought" in votes else 0)

    if bull_score >= 2 and bull_score > bear_score:
        signal = "BUY"
    elif bear_score >= 2 and bear_score > bull_score:
        signal = "SELL"
    else:
        signal = "HOLD"

    # Confidence
    strength = abs(bull_score - bear_score)
    confidence = "low"
    if strength == 1:
        confidence = "medium"
    elif strength >= 2:
        confidence = "high"

    rationale = f"Votes={votes}, bull={bull_score}, bear={bear_score}"
    return signal, confidence, rationale
