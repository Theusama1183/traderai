from typing import List, Optional, Literal
from pydantic import BaseModel, Field

Interval = Literal["1m","5m","15m","30m","1h","4h","1d","1w","1mo"]

class Candle(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int

class CandleRequest(BaseModel):
    symbol: str
    interval: Interval = "1h"
    limit: int = Field(default=200, ge=50, le=1000)

class IndicatorRequest(CandleRequest):
    rsi_length: int = 14
    ema_fast: int = 12
    ema_slow: int = 26
    bb_length: int = 20
    bb_std: float = 2.0

class IndicatorResponse(BaseModel):
    symbol: str
    interval: Interval
    candles: List[Candle]
    indicators: dict

class SignalResponse(BaseModel):
    symbol: str
    interval: Interval
    signal: Literal["BUY","SELL","HOLD"]
    confidence: Literal["low","medium","high"]
    rationale: str
    risk: dict
    levels: dict  # e.g., {"stop_loss": ..., "take_profit_1": ..., "take_profit_2": ...}

class BacktestRequest(BaseModel):
    symbol: str
    interval: Interval = "1h"
    limit: int = 2000
    strategy: Literal["ema_rsi_macd"] = "ema_rsi_macd"
    fee_bps: float = 5.0  # basis points per trade = 0.05%

class BacktestResult(BaseModel):
    symbol: str
    interval: Interval
    n_trades: int
    win_rate: float
    pnl_pct: float
    max_drawdown_pct: float
    sharpe: float
    equity_curve: List[float]
    notes: Optional[str] = None

class AICommentaryRequest(BaseModel):
    symbol: str
    interval: Interval = "1h"
    snapshot: dict  # indicators/last prices you pass from client or computed server-side
    style: Literal["concise","detailed"] = "concise"
