from typing import Dict

def risk_buckets(volatility_pct: float) -> str:
    if volatility_pct < 1.0:
        return "low"
    if volatility_pct < 2.5:
        return "medium"
    return "high"

def stoploss_takeprofit(last_price: float, atr_like_pct: float) -> Dict[str, float]:
    """
    Simple levels using a volatility-like percentage (proxy).
    """
    sl = last_price * (1 - 0.8 * atr_like_pct/100)
    tp1 = last_price * (1 + 1.2 * atr_like_pct/100)
    tp2 = last_price * (1 + 2.4 * atr_like_pct/100)
    return {"stop_loss": round(sl, 6), "take_profit_1": round(tp1, 6), "take_profit_2": round(tp2, 6)}
