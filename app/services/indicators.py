from typing import Dict
import pandas as pd
import pandas_ta as ta

def compute_indicators(
    df: pd.DataFrame,
    rsi_length: int = 14,
    ema_fast: int = 12,
    ema_slow: int = 26,
    bb_length: int = 20,
    bb_std: float = 2.0,
) -> Dict:
    # TA expects columns named 'open','high','low','close','volume'
    out = {}
    out["rsi"] = ta.rsi(df["close"], length=rsi_length)
    out["ema_fast"] = ta.ema(df["close"], length=ema_fast)
    out["ema_slow"] = ta.ema(df["close"], length=ema_slow)
    bb = ta.bbands(df["close"], length=bb_length, std=bb_std)
    # bb has columns: BBL, BBM, BBU
    out["bb_lower"] = bb.iloc[:,0]
    out["bb_mid"]   = bb.iloc[:,1]
    out["bb_upper"] = bb.iloc[:,2]
    macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
    out["macd"] = macd.iloc[:,0]
    out["macd_signal"] = macd.iloc[:,1]
    out["macd_hist"] = macd.iloc[:,2]
    return out

def attach(df: pd.DataFrame, indicators: Dict) -> pd.DataFrame:
    for k, v in indicators.items():
        df[k] = v.values
    return df
