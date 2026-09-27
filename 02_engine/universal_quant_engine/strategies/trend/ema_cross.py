"""Strategy — 지표를 조합해 신호 생성. 각 지표의 근거(reasons)를 보존한다."""
import pandas as pd

from ...core.interfaces import Strategy
from ...indicators.trend.trend import ema
from ...indicators.momentum.momentum import rsi
from ...indicators.volatility.volatility import atr


class EmaCrossStrategy(Strategy):
    """기본 예시 전략: EMA 단기/장기 교차 + RSI 필터 + ATR 상태 보존."""
    name = "ema_cross"

    def __init__(self, fast: int = 5, slow: int = 20, rsi_period: int = 14,
                 rsi_buy_max: float = 70, rsi_sell_min: float = 30):
        self.fast, self.slow = fast, slow
        self.rsi_period, self.rsi_buy_max, self.rsi_sell_min = rsi_period, rsi_buy_max, rsi_sell_min

    def generate_signal(self, data: pd.DataFrame) -> pd.DataFrame:
        out = data.copy()
        out["ema_fast"] = ema(data["close"], self.fast)
        out["ema_slow"] = ema(data["close"], self.slow)
        out["rsi"] = rsi(data["close"], self.rsi_period)
        out["atr"] = atr(data, 14)

        cross_up = (out["ema_fast"] > out["ema_slow"]) & (out["ema_fast"].shift() <= out["ema_slow"].shift())
        cross_dn = (out["ema_fast"] < out["ema_slow"]) & (out["ema_fast"].shift() >= out["ema_slow"].shift())

        signal = pd.Series(0, index=out.index)
        signal[cross_up & (out["rsi"] < self.rsi_buy_max)] = 1
        signal[cross_dn & (out["rsi"] > self.rsi_sell_min)] = -1
        out["signal"] = signal

        # 근거 보존 — 나중에 "왜 이 거래가 발생했는지" 추적 가능
        out["reasons"] = out.apply(
            lambda r: {
                "trend": "golden_cross" if r["signal"] == 1 else ("dead_cross" if r["signal"] == -1 else "hold"),
                "momentum": round(r["rsi"], 2) if pd.notna(r["rsi"]) else None,
                "volatility": round(r["atr"], 2) if pd.notna(r["atr"]) else None,
            } if r["signal"] != 0 else {}, axis=1)
        return out
