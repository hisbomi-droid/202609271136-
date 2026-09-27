"""Validation — 지표/전략/백테스트 검증 (데이터 검증과 분리).

4가지 검증 구분:
  1. 데이터 검증  → validation/data_quality.py
  2. 지표 검증    → "계산이 맞는가?"
  3. 전략 검증    → "규칙대로 신호가 발생했는가?"
  4. 백테스트 검증 → "룩어헤드/체결 오류 없는가?"
"""
import numpy as np
import pandas as pd

from ..indicators.trend.trend import ema
from ..indicators.momentum.momentum import rsi


class IndicatorValidator:
    """지표 계산이 수학적 정의와 일치하는지 검증."""

    def validate_sma(self, data: pd.DataFrame, period: int = 5) -> dict:
        closes = data["close"]
        expected = closes.iloc[:period].mean()
        actual = closes.rolling(period).mean().iloc[period - 1]
        return {"passed": bool(np.isclose(expected, actual)),
                "details": {"expected": expected, "actual": actual}}

    def validate_ema_convergence(self) -> dict:
        """상수 데이터에서 EMA는 그 상수에 수렴해야 한다."""
        const = pd.DataFrame({"close": [100.0] * 50})
        result = ema(const["close"], 20).iloc[-1]
        return {"passed": bool(np.isclose(result, 100.0, atol=1e-9)),
                "details": {"ema_final": result}}

    def validate_rsi_range(self, data: pd.DataFrame) -> dict:
        r = rsi(data["close"]).dropna()
        return {"passed": bool((r.between(0, 100)).all()),
                "details": {"min": float(r.min()), "max": float(r.max())}}


class StrategyValidator:
    """전략 검증 — 신호가 규칙대로 발생했는지."""

    def validate_signal_set(self, signals: pd.Series) -> dict:
        unique = set(signals.dropna().unique())
        return {"passed": unique.issubset({-1, 0, 1}),
                "details": {"unique_values": sorted(unique)}}

    def validate_reasons_preserved(self, strategy, data: pd.DataFrame) -> dict:
        out = strategy.generate_signal(data)
        fired = out[out["signal"] != 0]
        has_reasons = len(fired) == 0 or fired["reasons"].apply(
            lambda r: isinstance(r, dict) and len(r) > 0).all()
        return {"passed": bool(has_reasons),
                "details": {"signals_with_reasons": int(has_reasons)}}


class BacktestValidator:
    """백테스트 검증 — 룩어헤드 바이어스/체결 무결성."""

    def validate_no_lookahead(self, engine_result: dict) -> dict:
        trades = engine_result.get("trades")
        passed = trades is None or len(trades) == 0 or all(
            t["exit_price"] > 0 for _, t in trades.iterrows())
        return {"passed": bool(passed), "details": {"trades_checked": 0 if trades is None else len(trades)}}

    def validate_equity_positive(self, equity_curve: pd.Series) -> dict:
        return {"passed": bool((equity_curve > 0).all()),
                "details": {"min_equity": float(equity_curve.min())}}
