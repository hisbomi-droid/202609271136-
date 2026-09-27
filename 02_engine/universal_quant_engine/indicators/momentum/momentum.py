"""Momentum 지표."""
import pandas as pd
import numpy as np

from ...core.interfaces import Indicator


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.fillna(50.0)


def stochastic(data: pd.DataFrame, k_period: int = 14, d_period: int = 3):
    lowest = data["low"].rolling(k_period).min()
    highest = data["high"].rolling(k_period).max()
    k = 100 * (data["close"] - lowest) / (highest - lowest).replace(0, np.nan)
    return k, k.rolling(d_period).mean()


class RSIIndicator(Indicator):
    name = "rsi"
    def calculate(self, data, period=14): return rsi(data["close"], period)


class StochasticIndicator(Indicator):
    name = "stochastic"
    def calculate(self, data, k_period=14, d_period=3):
        k, d = stochastic(data, k_period, d_period)
        return pd.DataFrame({"k": k, "d": d})


class WilliamsRIndicator(Indicator):
    name = "williams_r"
    def calculate(self, data, period=14):
        highest = data["high"].rolling(period).max()
        lowest = data["low"].rolling(period).min()
        return -100 * (highest - data["close"]) / (highest - lowest).replace(0, np.nan)


class ROCIndicator(Indicator):
    name = "roc"
    def calculate(self, data, period=12): return 100 * data["close"].pct_change(period)


class CCIIndicator(Indicator):
    name = "cci"
    def calculate(self, data, period=20):
        tp = (data["high"] + data["low"] + data["close"]) / 3
        ma = tp.rolling(period).mean()
        mad = (tp - ma).abs().rolling(period).mean()
        return (tp - ma) / (0.015 * mad.replace(0, np.nan))
