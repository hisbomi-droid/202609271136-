"""Volatility 지표."""
import pandas as pd
import numpy as np

from ...core.interfaces import Indicator


def true_range(data: pd.DataFrame) -> pd.Series:
    h, l, c = data["high"], data["low"], data["close"]
    prev_c = c.shift()
    return pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)


def atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    return true_range(data).ewm(alpha=1 / period, adjust=False).mean()


def bollinger(series: pd.Series, period: int = 20, num_std: float = 2.0):
    mid = series.rolling(period).mean()
    std = series.rolling(period).std()
    return mid + num_std * std, mid, mid - num_std * std


def keltner_channel(data: pd.DataFrame, period: int = 20, mult: float = 2.0):
    mid = data["close"].ewm(span=period, adjust=False).mean()
    a = atr(data, period)
    return mid + mult * a, mid, mid - mult * a


class ATRIndicator(Indicator):
    name = "atr"
    def calculate(self, data, period=14): return atr(data, period)


class BollingerIndicator(Indicator):
    name = "bollinger"
    def calculate(self, data, period=20, num_std=2.0):
        upper, mid, lower = bollinger(data["close"], period, num_std)
        return pd.DataFrame({"upper": upper, "middle": mid, "lower": lower})


class RollingStdIndicator(Indicator):
    name = "rolling_std"
    def calculate(self, data, period=20): return data["close"].rolling(period).std()


class KeltnerIndicator(Indicator):
    name = "keltner"
    def calculate(self, data, period=20, mult=2.0):
        upper, mid, lower = keltner_channel(data, period, mult)
        return pd.DataFrame({"upper": upper, "middle": mid, "lower": lower})
