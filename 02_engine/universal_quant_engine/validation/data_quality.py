"""DATA VALIDATOR — 결측/중복/시간/OHLC/거래량/이상치/연속성 플러그인 검증."""
from typing import List
import numpy as np
import pandas as pd

from ..core.interfaces import Validator


class MissingValidator(Validator):
    name = "missing"

    def validate(self, data: pd.DataFrame) -> dict:
        n = len(data)
        if n == 0:
            return {"passed": False, "details": {"missing_rate": 1.0}}
        missing = data.isna().sum().sum()
        rate = float(missing) / (n * len(data.columns))
        return {"passed": rate < 0.01, "details": {"missing_cells": int(missing), "missing_rate": rate}}


class DuplicateValidator(Validator):
    name = "duplicate"

    def validate(self, data: pd.DataFrame) -> dict:
        n = len(data)
        dups = int(data["timestamp"].duplicated().sum()) if "timestamp" in data else 0
        rate = dups / n if n else 0.0
        return {"passed": rate < 0.01, "details": {"duplicates": dups, "duplicate_rate": rate}}


class TimestampValidator(Validator):
    name = "timestamp"

    def validate(self, data: pd.DataFrame) -> dict:
        if "timestamp" not in data or len(data) < 2:
            return {"passed": False, "details": {"error": "insufficient_data"}}
        ts = pd.to_datetime(data["timestamp"])
        monotonic = bool(ts.is_monotonic_increasing)
        backward = int((ts.diff().dt.total_seconds() < 0).sum())
        return {"passed": monotonic, "details": {"monotonic": monotonic, "backward_steps": backward}}


class OhlcValidator(Validator):
    name = "ohlc"

    def validate(self, data: pd.DataFrame) -> dict:
        bad = ((data["high"] < data[["open", "close", "low"]].max(axis=1)) |
               (data["low"] > data[["open", "close", "high"]].min(axis=1)) |
               (data["high"] < data["low"]))
        n_bad = int(bad.sum())
        return {"passed": n_bad == 0, "details": {"violations": n_bad}}


class OutlierValidator(Validator):
    """Z-score 기반 가격 이상치 검출. 품질 검증용이며 방향 예측에 사용하지 않는다."""
    name = "outlier"

    def __init__(self, threshold: float = 4.0):
        self.threshold = threshold

    def validate(self, data: pd.DataFrame) -> dict:
        ret = np.log(data["close"]).diff().dropna()
        if len(ret) < 10:
            return {"passed": True, "details": {"outliers": 0}}
        z = (ret - ret.mean()) / (ret.std() or 1.0)
        n_out = int((z.abs() > self.threshold).sum())
        return {"passed": n_out == 0,
                "details": {"outliers": n_out, "outlier_rate": n_out / len(ret)}}


class ContinuityValidator(Validator):
    """거래일 간격 연속성 검사 (일봉 기준, 주말+공휴일 최대 ~5일 허용)."""
    name = "continuity"

    def validate(self, data: pd.DataFrame) -> dict:
        ts = pd.to_datetime(data["timestamp"])
        gaps = ts.diff().dt.days.dropna()
        large_gaps = int((gaps > 5).sum())
        return {"passed": large_gaps == 0, "details": {"large_gaps": large_gaps}}


DEFAULT_VALIDATORS: List[Validator] = [
    MissingValidator(), DuplicateValidator(), TimestampValidator(),
    OhlcValidator(), OutlierValidator(), ContinuityValidator(),
]


class DataValidator:
    """검증기 목록을 실행하고 결과를 취합한다."""

    def __init__(self, validators: List[Validator] = None):
        self.validators = validators or DEFAULT_VALIDATORS

    def validate(self, data: pd.DataFrame) -> dict:
        results = {}
        for v in self.validators:
            try:
                results[v.name] = v.validate(data)
            except Exception as e:  # 검증기 오류는 시스템을 죽이지 않는다
                results[v.name] = {"passed": False, "details": {"error": str(e)}}
        passed = all(r.get("passed", False) for r in results.values())
        return {"passed": passed, "validators": results}
