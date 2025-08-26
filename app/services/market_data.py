import time
from typing import List, Dict
import httpx
import pandas as pd
from app.config import settings

BINANCE_INTERVAL_MAP = {
    "1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"1h","4h":"4h","1d":"1d","1w":"1w","1mo":"1M"
}

YAHOO_INTERVAL_MAP = {
    "1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"60m","4h":"240m","1d":"1d","1w":"1wk","1mo":"1mo"
}

async def fetch_candles(symbol: str, interval: str, limit: int) -> List[Dict]:
    """
    Returns list of candles in a uniform schema:
    [{open_time, open, high, low, close, volume, close_time}, ...]
    """
    if settings.DATA_SOURCE == "BINANCE":
        return await _fetch_binance(symbol, interval, limit)
    else:
        return await _fetch_yahoo(symbol, interval, limit)

async def _fetch_binance(symbol: str, interval: str, limit: int):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": BINANCE_INTERVAL_MAP[interval], "limit": limit}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    out = []
    for k in data:
        out.append({
            "open_time": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
            "close_time": int(k[6]),
        })
    return out

async def _fetch_yahoo(symbol: str, interval: str, limit: int):
    """
    Minimal Yahoo finance candles via query1.finance.yahoo.com
    (Public endpoint; limits apply. For production, consider a paid API.)
    """
    interval_q = YAHOO_INTERVAL_MAP[interval]
    range_q = "5y" if interval in ["1d","1w","1mo"] else "60d"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": interval_q, "range": range_q}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        j = r.json()
    res = j["chart"]["result"][0]
    ts = res["timestamp"][-limit:]
    o = res["indicators"]["quote"][0]
    opens = o["open"][-limit:]
    highs = o["high"][-limit:]
    lows  = o["low"][-limit:]
    closes= o["close"][-limit:]
    vols  = o["volume"][-limit:]
    out=[]
    for i in range(len(ts)):
        out.append({
            "open_time": int(ts[i])*1000,
            "open": float(opens[i]),
            "high": float(highs[i]),
            "low": float(lows[i]),
            "close": float(closes[i]),
            "volume": float(vols[i]),
            "close_time": int(ts[i])*1000
        })
    return out

def to_dataframe(candles: List[dict]) -> pd.DataFrame:
    df = pd.DataFrame(candles)
    df.rename(columns={"open_time":"time"}, inplace=True)
    df.sort_values("time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
