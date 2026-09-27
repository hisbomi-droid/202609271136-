"""Indicator Engine — 지표 레지스트리 + 일괄 계산 facade.

TA-Lib 비종속: Native NumPy/Pandas 구현이 기본.
TA-Lib가 설치된 환경에서는 동일 API 백엔드로 교체 가능하다.
"""
import pandas as pd

from ..core.interfaces import Indicator
from .trend.trend import SMAIndicator, EMAIndicator, MACDIndicator, ADXIndicator
from .momentum.momentum import (RSIIndicator, StochasticIndicator,
                                 WilliamsRIndicator, ROCIndicator, CCIIndicator)
from .volatility.volatility import (ATRIndicator, BollingerIndicator,
                                     RollingStdIndicator, KeltnerIndicator)
from .volume.volume import (VolumeMAIndicator, OBVIndicator, MFIIndicator, CMFIndicator)


class IndicatorEngine:
    def __init__(self, backend: str = "native"):
        self.backend = backend
        self._registry = {}
        for cls in (SMAIndicator, EMAIndicator, MACDIndicator, ADXIndicator,
                    RSIIndicator, StochasticIndicator, WilliamsRIndicator,
                    ROCIndicator, CCIIndicator, ATRIndicator, BollingerIndicator,
                    RollingStdIndicator, KeltnerIndicator, VolumeMAIndicator,
                    OBVIndicator, MFIIndicator, CMFIndicator):
            inst = cls()
            self._registry[inst.name] = inst

    def get(self, name: str) -> Indicator:
        if name not in self._registry:
            raise KeyError(f"미등록 지표: {name}. 등록된: {list(self._registry)}")
        return self._registry[name]

    def register(self, indicator: Indicator) -> None:
        self._registry[indicator.name] = indicator

    def compute(self, name: str, data: pd.DataFrame, **params) -> pd.Series:
        return self.get(name).calculate(data, **params)

    def compute_all(self, data: pd.DataFrame,
                    names: list = None, params: dict = None) -> pd.DataFrame:
        params = params or {}
        out = data.copy()
        for name in (names or self._registry.keys()):
            result = self.compute(name, data, **params.get(name, {}))
            if isinstance(result, pd.Series):
                out[name] = result
            else:  # DataFrame (다중 출력 지표)
                for col in result.columns:
                    out[f"{name}_{col}"] = result[col]
        return out
