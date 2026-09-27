"""Performance — 백테스트 성과 분석. 승률 하나로 판단하지 않고 전체 지표를 보존한다."""
import math
import pandas as pd
import numpy as np


class PerformanceReport:
    def __init__(self, equity_curve: pd.Series, trades: pd.DataFrame,
                 risk_free: float = 0.0, periods_per_year: int = 252):
        self.equity = equity_curve
        self.trades = trades
        self.rf = risk_free
        self.ppy = periods_per_year

    def build(self) -> dict:
        eq = self.equity.dropna()
        ret = eq.pct_change().dropna()
        total_return = eq.iloc[-1] / eq.iloc[0] - 1 if len(eq) > 1 else 0.0
        years = len(eq) / self.ppy if self.ppy else 1
        cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / max(years, 1e-9)) - 1 if len(eq) > 1 else 0.0
        vol = ret.std() * math.sqrt(self.ppy)
        downside = ret[ret < 0].std() * math.sqrt(self.ppy)
        sharpe = (ret.mean() * self.ppy - self.rf) / vol if vol else 0.0
        sortino = (ret.mean() * self.ppy - self.rf) / downside if downside and not np.isnan(downside) else 0.0
        max_dd = ((eq / eq.cummax()) - 1).min()

        pnl = self.trades["pnl"] if len(self.trades) else pd.Series(dtype=float)
        wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
        win_rate = len(wins) / len(pnl) if len(pnl) else 0.0
        if len(wins) and len(losses) and losses.sum() != 0:
            profit_factor = wins.sum() / abs(losses.sum())
        elif len(wins):
            profit_factor = "inf"
        else:
            profit_factor = 0.0

        return {
            "total_return": round(total_return, 4),
            "cagr": round(cagr, 4),
            "volatility": round(vol, 4),
            "sharpe": round(sharpe, 3),
            "sortino": round(sortino, 3),
            "max_drawdown": round(max_dd, 4),
            "num_trades": int(len(pnl)),
            "win_rate": round(win_rate, 4),
            "profit_factor": round(profit_factor, 3) if profit_factor != "inf" else "inf",
            "avg_trade": round(pnl.mean(), 4) if len(pnl) else 0.0,
            "avg_win": round(wins.mean(), 4) if len(wins) else 0.0,
            "avg_loss": round(losses.mean(), 4) if len(losses) else 0.0,
        }
