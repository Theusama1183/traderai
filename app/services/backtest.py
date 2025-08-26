from typing import Dict
import numpy as np
import pandas as pd

def run_backtest_ema_rsi_macd(df: pd.DataFrame, fee_bps: float = 5.0) -> Dict:
    """
    Very minimal long/flat backtest:
    - Enter long when signal == BUY
    - Exit to flat when signal == SELL
    - HOLD does nothing
    Fees applied on each position change.
    """
    fee = fee_bps / 10000.0
    position = 0  # 0 = flat, 1 = long
    entry_price = 0.0
    equity = 1.0
    peak = 1.0
    trades = []
    rets = []

    for i in range(1, len(df)):
        sig = df.iloc[i]["signal"]
        price = df.iloc[i]["close"]

        if position == 0 and sig == "BUY":
            position = 1
            entry_price = price
            equity *= (1 - fee)
            trades.append(("BUY", price))
        elif position == 1 and sig == "SELL":
            # close position
            ret = (price / entry_price) - 1.0
            equity *= (1 + ret) * (1 - fee)
            trades.append(("SELL", price))
            position = 0
        # Track returns
        rets.append(equity)

        if equity > peak:
            peak = equity

    pnl_pct = (equity - 1.0) * 100
    # max drawdown
    curve = np.array(rets) if rets else np.array([1.0])
    running_max = np.maximum.accumulate(curve)
    dd = (curve / running_max) - 1.0
    mdd = dd.min() * 100

    # Sharpe (naive, daily-ish normalization skipped for simplicity)
    if len(curve) > 1:
        r = np.diff(curve) / curve[:-1]
        sharpe = (np.mean(r) / (np.std(r) + 1e-9)) * np.sqrt(252)
    else:
        sharpe = 0.0

    wins = 0
    n_trades = 0
    for j in range(1, len(trades), 2):
        buy_price = trades[j-1][1]
        sell_price = trades[j][1]
        n_trades += 1
        if sell_price > buy_price:
            wins += 1

    win_rate = (wins / n_trades * 100) if n_trades else 0.0

    return {
        "n_trades": n_trades,
        "win_rate": round(win_rate, 2),
        "pnl_pct": round(pnl_pct, 2),
        "max_drawdown_pct": round(mdd, 2),
        "sharpe": round(float(sharpe), 2),
        "equity_curve": [float(x) for x in curve]
    }
