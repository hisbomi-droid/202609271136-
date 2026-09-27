"""Trend 지표 — 매매 조건 없이 계산만 수행."""
import pandas as pd
import numpy as np

from ...core.interfaces import Indicator


def sma(series: pd.Series, period: int = 20) -> pd.Series:
    return series.rolling(period).mean()


def ema(series: pd.Series, period: int = 20) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def wma(series: pd.Series, period: int = 20) -> pd.Series:
    weights = np.arange(1, period + 1)
    return series.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = ema(series, fast) - ema(series, slow)
    sig = line.ewm(span=signal, adjust=False).mean()
    return line, sig, line - sig  # macd, signal, histogram


class SMAIndicator(Indicator):
    name = "sma"
    def calculate(self, data, period=20): return sma(data["close"], period)


class EMAIndicator(Indicator):
    name = "ema"
    def calculate(self, data, period=20): return ema(data["close"], period)


class MACDIndicator(Indicator):
    name = "macd"
    def calculate(self, data, fast=12, slow=26, signal=9):
        line, sig, hist = macd(data["close"], fast, slow, signal)
        return pd.DataFrame({"macd": line, "signal": sig, "histogram": hist})


class ADXIndicator(Indicator):
    name = "adx"
    def calculate(self, data, period=14):
        h, l, c = data["high"], data["low"], data["close"]
        up = h.diff()
        down = -l.diff()
        plus_dm = np.where((up > down) & (up > 0), up, 0.0)
        minus_dm = np.where((down > up) & (down > 0), down, 0.0)
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / period, adjust=False).mean()
        plus_di = 100 * pd.Series(plus_dm, index=data.index).ewm(alpha=1 / period, adjust=False).mean() / atr
        minus_di = 100 * pd.Series(minus_dm, index=data.index).ewm(alpha=1 / period, adjust=False).mean() / atr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        return pd.DataFrame({"adx": dx.ewm(alpha=1 / period, adjust=False).mean(),
                             "plus_di": plus_di, "minus_di": minus_di})
