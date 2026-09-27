"""Volume 지표."""
import pandas as pd
import numpy as np

from ...core.interfaces import Indicator


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = close.diff().fillna(0).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


class VolumeMAIndicator(Indicator):
    name = "volume_ma"
    def calculate(self, data, period=20): return data["volume"].rolling(period).mean()


class OBVIndicator(Indicator):
    name = "obv"
    def calculate(self, data): return obv(data["close"], data["volume"])


class MFIIndicator(Indicator):
    name = "mfi"
    def calculate(self, data, period=14):
        tp = (data["high"] + data["low"] + data["close"]) / 3
        raw = tp * data["volume"]
        pos = raw.where(tp > tp.shift(), 0.0).rolling(period).sum()
        neg = raw.where(tp < tp.shift(), 0.0).rolling(period).sum()
        return 100 * pos / (pos + neg).replace(0, np.nan)


class CMFIndicator(Indicator):
    name = "cmf"
    def calculate(self, data, period=20):
        h, l, c, v = data["high"], data["low"], data["close"], data["volume"]
        mfm = ((c - l) - (h - c)) / (h - l).replace(0, np.nan)
        return (mfm * v).rolling(period).sum() / v.rolling(period).sum()
