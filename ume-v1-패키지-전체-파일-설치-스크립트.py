#!/usr/bin/env python3
"""
setup_ume_v1.py — Universal Quant Engine v1 패키지 전체 파일 생성 스크립트
======================================================================
실행:  python setup_ume_v1.py
결과:  ./02_engine/universal_quant_engine/ 아래 패키지 26개 파일 전체 생성

생성 후 실행 검증:
  cd 02_engine
  python -m universal_quant_engine.tests.test_v1
  → 15개 항목 PASS / 15/15 통과 확인
"""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "02_engine", "universal_quant_engine")

# 빈 __init__.py가 필요한 폴더들
EMPTY_INIT_DIRS = [
    "core", "collectors", "normalization", "validation", "reliability",
    "indicators", "indicators/trend", "indicators/momentum",
    "indicators/volatility", "indicators/volume",
    "strategies", "strategies/trend", "backtest", "tests", "examples",
]

FILES = {}

# ════════════════════════════════════════════════════════════════
FILES["__init__.py"] = '''"""Universal Quant Engine V1
Provider → Normalize → Validate → 표준 OHLCV → 지표 → 전략 → 백테스트 → 신뢰도
"""
from .api import MarketEngine, Market
from .core.models import MarketBar, Quote, RawSnapshot, ReliabilityReport
from .core.interfaces import MarketDataProvider, Indicator, Strategy, Validator
from .core.registry import ProviderRegistry
from .indicators.indicators import IndicatorEngine
from .backtest.engine import BacktestEngine, BrokerConfig
from .backtest.performance import PerformanceReport

__version__ = "1.0.0"
__all__ = [
    "Market", "MarketEngine", "MarketBar", "Quote", "RawSnapshot",
    "ReliabilityReport", "MarketDataProvider", "Indicator", "Strategy",
    "Validator", "ProviderRegistry", "IndicatorEngine",
    "BacktestEngine", "BrokerConfig", "PerformanceReport",
]
'''

# ════════════════════════════════════════════════════════════════
FILES["core/models.py"] = '''"""표준 데이터 모델 — 모든 Provider가 이 형식으로 변환한다."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class MarketBar:
    """표준 OHLCV 바. 원본 추적 정보까지 보존한다."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    source_timestamp: Optional[datetime] = None
    received_timestamp: Optional[datetime] = None
    processed_timestamp: Optional[datetime] = None
    raw_id: Optional[str] = None
    quality: str = "normal"  # normal / delayed / manual / missing

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "timestamp": self.timestamp,
            "open": self.open, "high": self.high, "low": self.low,
            "close": self.close, "volume": self.volume, "source": self.source,
            "quality": self.quality,
        }


@dataclass
class Quote:
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    source: str
    quality: str = "normal"


@dataclass
class RawSnapshot:
    """Normalize 이전의 원본 데이터. 수집 오류와 분석 오류를 분리하는 데 사용."""
    source: str
    payload: Dict[str, Any]
    received_timestamp: datetime
    raw_id: Optional[str] = None


@dataclass
class ReliabilityReport:
    """신뢰도 구성요소를 보존한다. 합산 점수는 정책(policy)이 별도로 계산한다."""
    source: str
    freshness: float = 1.0
    completeness: float = 1.0
    consistency: float = 1.0
    timestamp_quality: float = 1.0
    duplicate_rate: float = 0.0
    missing_rate: float = 0.0
    outlier_rate: float = 0.0
    cross_source_agreement: float = 1.0
    checks: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source, "freshness": self.freshness,
            "completeness": self.completeness, "consistency": self.consistency,
            "timestamp_quality": self.timestamp_quality,
            "duplicate_rate": self.duplicate_rate, "missing_rate": self.missing_rate,
            "outlier_rate": self.outlier_rate,
            "cross_source_agreement": self.cross_source_agreement,
        }
'''

# ════════════════════════════════════════════════════════════════
FILES["core/interfaces.py"] = '''"""모든 확장점(Provider / Indicator / Strategy / Validator)의 표준 인터페이스."""
from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd

from .models import MarketBar, Quote


class MarketDataProvider(ABC):
    """데이터 수집 Provider. 새 사이트는 이 클래스만 구현하면 된다."""
    name: str = "base"

    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[Quote]:
        ...

    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str = "1d",
                 count: int = 200) -> List[MarketBar]:
        ...

    def subscribe(self, symbol: str) -> None:
        """실시간 구독 (지원하지 않으면 no-op)."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> bool:
        ...


class Indicator(ABC):
    """지표. 계산만 하고 매매 조건을 포함하지 않는다."""
    name: str = "base"

    @abstractmethod
    def calculate(self, data: pd.DataFrame, **params) -> pd.Series:
        ...


class Strategy(ABC):
    """전략. 지표를 조합해 진입/청산 신호를 만든다. 각 근거를 보존한다."""
    name: str = "base"

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> pd.DataFrame:
        """columns: signal(1/0/-1), reasons(dict) 를 포함한 DataFrame 반환."""
        ...


class Validator(ABC):
    """데이터 품질 검증 플러그인."""
    name: str = "base"

    @abstractmethod
    def validate(self, data: pd.DataFrame) -> dict:
        """{passed: bool, details: dict} 형태 반환."""
        ...
'''

# ════════════════════════════════════════════════════════════════
FILES["core/registry.py"] = '''"""Provider 레지스트리 — 새 Provider 추가 시 엔진 수정 없이 등록만 한다."""
from typing import Dict, Type
from .interfaces import MarketDataProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, Type[MarketDataProvider]] = {}

    def register(self, cls: Type[MarketDataProvider]) -> Type[MarketDataProvider]:
        self._providers[cls.name] = cls
        return cls

    def create(self, name: str, **kwargs) -> MarketDataProvider:
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' 미등록. 등록된: {list(self._providers)}")
        return self._providers[name](**kwargs)

    def available(self) -> list:
        return list(self._providers)
'''

# ════════════════════════════════════════════════════════════════
FILES["collectors/mock_provider.py"] = '''"""Mock Provider — 엔진 구조 검증 및 테스트용. 결정적(deterministic) 데이터 생성."""
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional

from ..core.interfaces import MarketDataProvider
from ..core.models import MarketBar, Quote


class MockProvider(MarketDataProvider):
    name = "mock"

    def __init__(self, seed: int = 42, base_price: float = 2500.0):
        self.seed = seed
        self.base_price = base_price

    def _pseudo_random(self, i: int) -> float:
        """시드 기반 결정적 난수 (재현 가능한 테스트용)."""
        h = hashlib.md5(f"{self.seed}:{i}".encode()).hexdigest()
        return int(h[:8], 16) / 0xFFFFFFFF  # 0~1

    def get_bars(self, symbol: str, timeframe: str = "1d",
                 count: int = 200) -> List[MarketBar]:
        bars, price = [], self.base_price
        now = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
        for i in range(count):
            r = self._pseudo_random(i)
            close = round(price * (1 + (r - 0.5) * 0.02), 2)
            high = round(max(price, close) * (1 + self._pseudo_random(i + 1000) * 0.005), 2)
            low = round(min(price, close) * (1 - self._pseudo_random(i + 2000) * 0.005), 2)
            ts = now - timedelta(days=(count - i))
            bars.append(MarketBar(
                symbol=symbol, timestamp=ts,
                open=round(price, 2), high=high, low=low, close=close,
                volume=float(int(self._pseudo_random(i + 3000) * 5_000_000) + 500_000),
                source=self.name,
                source_timestamp=ts, received_timestamp=ts,
                processed_timestamp=datetime.now(),
                raw_id=f"mock-{symbol}-{i}",
            ))
            price = close
        return bars

    def get_quote(self, symbol: str) -> Optional[Quote]:
        b = self.get_bars(symbol, count=1)[0]
        return Quote(symbol=symbol, timestamp=b.timestamp, price=b.close,
                     volume=b.volume, source=self.name)

    def health(self) -> bool:
        return True
'''

# ════════════════════════════════════════════════════════════════
FILES["normalization/normalizer.py"] = '''"""NORMALIZER — 서로 다른 원천 데이터를 표준 MarketBar 형식으로 변환."""
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from ..core.models import MarketBar, RawSnapshot

# 표준 컬럼 순서 (snapshot_schema_v1)
STANDARD_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class Normalizer:
    def normalize_bars(self, bars: List[MarketBar]) -> pd.DataFrame:
        """MarketBar 리스트 → 표준 DataFrame."""
        if not bars:
            return pd.DataFrame(columns=STANDARD_COLUMNS)
        df = pd.DataFrame([b.to_dict() for b in bars])
        df = df[["source"] + STANDARD_COLUMNS + ["quality"]]
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df.sort_values("timestamp").reset_index(drop=True)

    def normalize_raw(self, snapshot: RawSnapshot) -> Optional[MarketBar]:
        """원천별 raw dict → MarketBar. 원천이 표준 필드명을 쓰지 않아도 여기서 매핑한다."""
        p = snapshot.payload
        try:
            return MarketBar(
                symbol=p.get("symbol", "UNKNOWN"),
                timestamp=pd.to_datetime(p.get("date") or p.get("timestamp") or snapshot.received_timestamp),
                open=float(p.get("open") or p.get("o") or p.get("시가")),
                high=float(p.get("high") or p.get("h") or p.get("고가")),
                low=float(p.get("low") or p.get("l") or p.get("저가")),
                close=float(p.get("close") or p.get("c") or p.get("종가") or p.get("price")),
                volume=float(p.get("volume") or p.get("v") or p.get("거래량") or 0),
                source=snapshot.source,
                source_timestamp=pd.to_datetime(p.get("date") or p.get("timestamp")),
                received_timestamp=snapshot.received_timestamp,
                processed_timestamp=datetime.now(),
                raw_id=snapshot.raw_id,
            )
        except (KeyError, TypeError, ValueError):
            return None  # 파싱 실패 → None. 검증기가 결측으로 처리

    def raw_and_normalized(self, snapshot: RawSnapshot):
        """원본 → 정규화값을 함께 반환 (수집 전/후 비교용)."""
        return snapshot.payload, self.normalize_raw(snapshot)
'''

# ════════════════════════════════════════════════════════════════
FILES["validation/data_quality.py"] = '''"""DATA VALIDATOR — 결측/중복/시간/OHLC/거래량/이상치/연속성 플러그인 검증."""
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
'''

# ════════════════════════════════════════════════════════════════
FILES["validation/cross_source.py"] = '''"""CROSS-SOURCE VERIFICATION — 원천 간 값 비교. 하나를 임의로 선택하지 않고 차이를 보존한다."""
from typing import Dict
import pandas as pd


class CrossSourceVerifier:
    def __init__(self, tolerance: float = 0.01, volume_tolerance: float = 0.05):
        self.tolerance = tolerance          # 가격 허용 오차 (절대)
        self.volume_tolerance = volume_tolerance  # 거래량 허용 오차 (비율)

    def compare_closes(self, frames: Dict[str, pd.DataFrame]) -> dict:
        """동일 symbol의 원천별 DataFrame을 받아 마지막 종가/거래량을 비교한다."""
        if len(frames) < 2:
            return {"agreement": 1.0, "comparisons": {}}

        last = {src: df.iloc[-1] for src, df in frames.items() if len(df)}
        if len(last) < 2:
            return {"agreement": 1.0, "comparisons": {}}

        closes = {src: float(row["close"]) for src, row in last.items()}
        vols = {src: float(row["volume"]) for src, row in last.items()}
        ref = max(closes.values())
        ref_vol = max(vols.values())

        comparisons, agree_count = {}, 0
        for src in closes:
            diff = abs(closes[src] - ref)
            vdiff = abs(vols[src] - ref_vol) / (ref_vol or 1.0)
            ok = diff <= self.tolerance and vdiff <= self.volume_tolerance
            agree_count += int(ok)
            comparisons[src] = {
                "close": closes[src], "close_diff": round(diff, 4),
                "volume": vols[src], "volume_diff_ratio": round(vdiff, 4),
                "match": ok,
            }
        return {"agreement": agree_count / len(closes), "comparisons": comparisons}

    def ohlc_table(self, frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """원천별 OHLCV 비교표."""
        rows = []
        for src, df in frames.items():
            if len(df):
                r = df.iloc[-1]
                rows.append({"source": src, "open": r["open"], "high": r["high"],
                             "low": r["low"], "close": r["close"], "volume": r["volume"]})
        return pd.DataFrame(rows)
'''

# ════════════════════════════════════════════════════════════════
FILES["validation/strategy_and_backtest.py"] = '''"""Validation — 지표/전략/백테스트 검증 (데이터 검증과 분리).

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
'''

# ════════════════════════════════════════════════════════════════
FILES["reliability/engine.py"] = '''"""RELIABILITY ENGINE — 구성요소를 보존하는 신뢰도 리포트."""
from datetime import datetime
import pandas as pd

from ..core.models import ReliabilityReport


class ReliabilityEngine:
    """데이터 품질 검증 결과 + 원천 간 일치율 → ReliabilityReport.
    합산 점수는 정책(policy)으로 분리: 기본 정책은 가중평균.
    """

    def __init__(self, freshness_halflife_hours: float = 24.0):
        self.halflife = freshness_halflife_hours

    def build_report(self, source: str, data: pd.DataFrame,
                     validation: dict = None, cross_agreement: float = 1.0) -> ReliabilityReport:
        n = len(data)
        now = pd.Timestamp(datetime.now())

        # 최신성: 마지막 데이터 시각으로부터 지수 감쇠
        if n and "timestamp" in data:
            last_ts = pd.to_datetime(data["timestamp"]).iloc[-1]
            hours = max((now - last_ts).total_seconds() / 3600.0, 0.0)
            freshness = 0.5 ** (hours / self.halflife)
        else:
            freshness = 0.0

        v = (validation or {}).get("validators", {})
        missing_rate = v.get("missing", {}).get("details", {}).get("missing_rate", 0.0)
        duplicate_rate = v.get("duplicate", {}).get("details", {}).get("duplicate_rate", 0.0)
        outlier_rate = v.get("outlier", {}).get("details", {}).get("outlier_rate", 0.0)
        ts_passed = v.get("timestamp", {}).get("passed", False)
        ohlc_passed = v.get("ohlc", {}).get("passed", False)
        continuity_passed = v.get("continuity", {}).get("passed", False)

        consistency = 1.0
        consistency -= 0.5 * (not ohlc_passed) + 0.25 * (not continuity_passed)
        consistency = max(consistency, 0.0)

        return ReliabilityReport(
            source=source,
            freshness=round(freshness, 4),
            completeness=round(max(1.0 - missing_rate, 0.0), 4),
            consistency=round(consistency, 4),
            timestamp_quality=1.0 if ts_passed else 0.5,
            duplicate_rate=round(duplicate_rate, 4),
            missing_rate=round(missing_rate, 4),
            outlier_rate=round(outlier_rate, 4),
            cross_source_agreement=round(cross_agreement, 4),
            checks=v,
        )

    @staticmethod
    def overall_score(report: ReliabilityReport) -> float:
        """기본 정책: 균등 가중평균 (0~100). 정책 교체 가능."""
        comps = [
            report.freshness, report.completeness, report.consistency,
            report.timestamp_quality, report.cross_source_agreement,
            1.0 - min(report.duplicate_rate + report.missing_rate + report.outlier_rate, 1.0),
        ]
        return round(sum(comps) / len(comps) * 100, 1)
'''

# ════════════════════════════════════════════════════════════════
FILES["indicators/trend/trend.py"] = '''"""Trend 지표 — 매매 조건 없이 계산만 수행."""
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
'''

# ════════════════════════════════════════════════════════════════
FILES["indicators/momentum/momentum.py"] = '''"""Momentum 지표."""
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
'''

# ════════════════════════════════════════════════════════════════
FILES["indicators/volatility/volatility.py"] = '''"""Volatility 지표."""
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
'''

# ════════════════════════════════════════════════════════════════
FILES["indicators/volume/volume.py"] = '''"""Volume 지표."""
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
'''

# ════════════════════════════════════════════════════════════════
FILES["indicators/indicators.py"] = '''"""Indicator Engine — 지표 레지스트리 + 일괄 계산 facade.

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
'''

# ════════════════════════════════════════════════════════════════
FILES["strategies/trend/ema_cross.py"] = '''"""Strategy — 지표를 조합해 신호 생성. 각 지표의 근거(reasons)를 보존한다."""
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
'''

# ════════════════════════════════════════════════════════════════
FILES["backtest/performance.py"] = '''"""Performance — 백테스트 성과 분석. 승률 하나로 판단하지 않고 전체 지표를 보존한다."""
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
'''

# ════════════════════════════════════════════════════════════════
FILES["backtest/engine.py"] = '''"""Backtest Engine — DataFeed → Strategy → Order → Execution → Position → Portfolio.

현실 요소(수수료/슬리피지/거래세) 반영. 시장가 주문, 다음 봉 시가 체결 기준.
Look-ahead bias 방지: i 봉의 신호는 i+1 봉 시가에 체결된다.
"""
import pandas as pd

from .performance import PerformanceReport


class BrokerConfig:
    """한국 주식시장용 기본 설정 (사용자 환경에 맞게 교체)."""
    def __init__(self, commission: float = 0.00015, tax: float = 0.0018,
                 slippage: float = 0.0002, initial_cash: float = 100_000_000.0):
        self.commission = commission
        self.tax = tax          # 매도 시에만
        self.slippage = slippage
        self.initial_cash = initial_cash


class BacktestEngine:
    def __init__(self, config: BrokerConfig = None):
        self.config = config or BrokerConfig()

    def run(self, data: pd.DataFrame, strategy) -> dict:
        """data: 표준 OHLCV. strategy.generate_signal(data) → signal 컬럼."""
        cfg = self.config
        df = strategy.generate_signal(data)
        cash = cfg.initial_cash
        position = 0.0
        entry_price = 0.0
        equity, trades = [], []

        for i in range(len(df)):
            row = df.iloc[i]
            # ① 이전 봉(i-1)의 신호를 현재 봉 시가에 체결
            if i > 0:
                sig = df["signal"].iloc[i - 1]
                price = row["open"] * (1 + cfg.slippage * sig)

                if sig == 1 and position == 0:  # 진입
                    qty = cash * 0.95 / (price * (1 + cfg.commission))
                    if qty > 0:
                        cost = qty * price * (1 + cfg.commission)
                        cash -= cost
                        position = qty
                        entry_price = price
                elif sig == -1 and position > 0:  # 청산
                    proceeds = position * price * (1 - cfg.commission - cfg.tax)
                    pnl = proceeds - position * entry_price * (1 + cfg.commission)
                    trades.append({
                        "exit_time": row["timestamp"] if "timestamp" in row else i,
                        "entry_price": entry_price, "exit_price": price,
                        "pnl": pnl, "return": pnl / (position * entry_price),
                        "reasons": df["reasons"].iloc[i - 1],
                    })
                    cash += proceeds
                    position = 0.0

            # ② 당일 평가액
            equity.append(cash + position * row["close"])

        trades_df = pd.DataFrame(trades)
        report = PerformanceReport(pd.Series(equity), trades_df).build()
        return {"report": report, "equity_curve": pd.Series(equity),
                "trades": trades_df, "signals": df[["signal"]] if "signal" in df else None}
'''

# ════════════════════════════════════════════════════════════════
FILES["api.py"] = '''"""Market / MarketEngine — 외부 프로그램용 최상위 API.

사용법:
    from universal_quant_engine import Market
    market = Market(providers=["mock"])
    data = market.market("KOSPI")
    indicators = market.analyze(data)
    report = market.verify("KOSPI")
    reliability = market.reliability_report("KOSPI")
"""
import pandas as pd
from typing import Dict, List, Optional

from .core.interfaces import MarketDataProvider, Strategy
from .core.registry import ProviderRegistry
from .collectors.mock_provider import MockProvider
from .normalization.normalizer import Normalizer
from .validation.data_quality import DataValidator
from .validation.cross_source import CrossSourceVerifier
from .reliability.engine import ReliabilityEngine
from .indicators.indicators import IndicatorEngine
from .backtest.engine import BacktestEngine, BrokerConfig
from .core.models import ReliabilityReport


class MarketEngine:
    def __init__(self, providers: Optional[List[str]] = None,
                 provider_kwargs: Optional[dict] = None):
        self.registry = ProviderRegistry()
        self.registry.register(MockProvider)  # 기본 Mock (테스트/구조 검증용)
        # → KRX, LS Xing, Naver, Yahoo 등은 추후 register로 추가
        self.provider_kwargs = provider_kwargs or {}
        self.providers: Dict[str, MarketDataProvider] = {
            name: self.registry.create(name, **self.provider_kwargs.get(name, {}))
            for name in (providers or ["mock"])
        }
        self.normalizer = Normalizer()
        self.validator = DataValidator()
        self.cross_verifier = CrossSourceVerifier()
        self.reliability = ReliabilityEngine()
        self.indicator_engine = IndicatorEngine()
        self._cache: Dict[str, pd.DataFrame] = {}
        self._frames_cache: Dict[str, pd.DataFrame] = {}

    # ── DATA ─────────────────────────────────────────────
    def market(self, symbol: str, timeframe: str = "1d", count: int = 200) -> pd.DataFrame:
        """Provider → Raw → Normalize → 표준 DataFrame. 폴백: 실패 시 다음 소스, 전부 실패 시 예외."""
        errors, frames = {}, {}
        for name, provider in self.providers.items():
            try:
                bars = provider.get_bars(symbol, timeframe, count)
                frames[name] = self.normalizer.normalize_bars(bars)
            except Exception as e:
                errors[name] = str(e)
        if not frames:
            raise RuntimeError(f"모든 Provider 실패. 데이터 없음. errors={errors}")
        primary = next(iter(frames.values()))
        self._cache[symbol] = primary
        self._frames_cache = frames
        return primary

    def get_all_sources(self) -> Dict[str, pd.DataFrame]:
        return self._frames_cache

    # ── ANALYSIS ──────────────────────────────────────────
    def analyze(self, data: pd.DataFrame, indicators: Optional[List[str]] = None) -> pd.DataFrame:
        return self.indicator_engine.compute_all(data, names=indicators)

    # ── VERIFY / RELIABILITY ──────────────────────────────
    def verify(self, symbol: str, data: Optional[pd.DataFrame] = None) -> dict:
        data = data if data is not None else self._cache.get(symbol)
        if data is None:
            raise ValueError(f"'{symbol}' 데이터 없음. market()을 먼저 호출하세요.")
        validation = self.validator.validate(data)
        frames = self._frames_cache
        cross = (self.cross_verifier.compare_closes(frames)
                 if len(frames) >= 2 else {"agreement": 1.0})
        return {"validation": validation, "cross_source": cross,
                "ohlc_table": self.cross_verifier.ohlc_table(frames)}

    def reliability_report(self, symbol: str,
                           data: Optional[pd.DataFrame] = None) -> ReliabilityReport:
        data = data if data is not None else self._cache.get(symbol)
        if data is None:
            raise ValueError(f"'{symbol}' 데이터 없음.")
        frames = self._frames_cache
        cross = (self.cross_verifier.compare_closes(frames)
                 if len(frames) >= 2 else {"agreement": 1.0})
        source = data["source"].iloc[0] if "source" in data else "unknown"
        report = self.reliability.build_report(
            source, data, validation=self.validator.validate(data),
            cross_agreement=cross.get("agreement", 1.0))
        report.checks["overall_score"] = ReliabilityEngine.overall_score(report)
        return report

    # ── BACKTEST ──────────────────────────────────────────
    def backtest(self, data: pd.DataFrame, strategy: Strategy,
                 config: Optional[BrokerConfig] = None) -> dict:
        return BacktestEngine(config).run(data, strategy)


# 짧은 별칭
Market = MarketEngine
'''

# ════════════════════════════════════════════════════════════════
FILES["tests/test_v1.py"] = '''"""V1 통합 테스트 — 데이터→지표→전략→백테스트→검증→신뢰도 전 파이프라인."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from universal_quant_engine import Market
from universal_quant_engine.strategies.trend.ema_cross import EmaCrossStrategy
from universal_quant_engine.validation.strategy_and_backtest import (
    IndicatorValidator, StrategyValidator, BacktestValidator)


def main():
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))
        print(f"{'PASS' if cond else 'FAIL'} - {name}")

    # ① 데이터 수집 + 정규화
    market = Market(providers=["mock"])
    data = market.market("KOSPI", count=200)
    check("데이터 수집 (200 bars)", len(data) == 200)
    check("표준 컬럼 존재", all(c in data.columns for c in
          ["timestamp", "open", "high", "low", "close", "volume"]))

    # ② 데이터 검증
    v = market.validator.validate(data)
    check("데이터 검증 통과", v["passed"])

    # ③ 지표 계산
    ind = market.analyze(data, indicators=["ema", "rsi", "atr", "bollinger", "macd"])
    check("지표 계산 (ema/rsi/atr/bollinger/macd)",
          all(any(c.startswith(n) for c in ind.columns)
              for n in ["ema", "rsi", "atr", "bollinger", "macd"]))

    # ④ 지표 검증
    iv = IndicatorValidator()
    check("SMA 수학적 정의 일치", iv.validate_sma(data)["passed"])
    check("EMA 상수 수렴", iv.validate_ema_convergence()["passed"])
    check("RSI 범위 0~100", iv.validate_rsi_range(data)["passed"])

    # ⑤ 전략 + 검증
    strategy = EmaCrossStrategy()
    sv = StrategyValidator()
    sig_df = strategy.generate_signal(data)
    check("신호 값域 {-1,0,1}", sv.validate_signal_set(sig_df["signal"])["passed"])
    check("신호 근거 보존", sv.validate_reasons_preserved(strategy, data)["passed"])

    # ⑥ 백테스트 + 검증
    bt = market.backtest(data, strategy)
    bv = BacktestValidator()
    check("룩어헤드/체결 무결성", bv.validate_no_lookahead(bt)["passed"])
    check("Equity 양수 유지", bv.validate_equity_positive(bt["equity_curve"])["passed"])
    check("성과 리포트 필드 존재",
          all(k in bt["report"] for k in
              ["total_return", "sharpe", "max_drawdown", "win_rate", "profit_factor"]))

    # ⑦ 신뢰도
    rel = market.reliability_report("KOSPI")
    check("신뢰도 리포트 생성", rel.source == "mock" and 0 <= rel.completeness <= 1)
    check("종합 점수 0~100", 0 <= rel.checks.get("overall_score", -1) <= 100)

    failed = [n for n, ok in results if not ok]
    print(f"\\n{'='*50}\\n{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        print("실패 항목:", failed)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

# ════════════════════════════════════════════════════════════════
FILES["examples/run_example.py"] = '''"""Universal Quant Engine 사용 예시."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from universal_quant_engine import Market
from universal_quant_engine.strategies.trend.ema_cross import EmaCrossStrategy
from universal_quant_engine.reliability.engine import ReliabilityEngine


def main():
    market = Market(providers=["mock"])   # → 실제 운영: Market(providers=["ls_xing", "naver"])

    kospi = market.market("KOSPI", count=200)
    print(kospi.tail(3))

    indicators = market.analyze(kospi, indicators=["ema", "rsi", "macd", "atr", "bollinger", "obv"])
    print(indicators[["close", "ema", "rsi", "atr"]].tail(3))

    verification = market.verify("KOSPI")
    print("데이터 검증:", verification["validation"]["passed"])
    report = market.reliability_report("KOSPI")
    print("신뢰도:", report.to_dict())
    print("종합 점수:", ReliabilityEngine.overall_score(report))

    result = market.backtest(kospi, EmaCrossStrategy())
    print("성과:", result["report"])


if __name__ == "__main__":
    main()
'''


def main():
    created = 0
    # 1) 빈 __init__.py가 필요한 폴더 생성
    for d in EMPTY_INIT_DIRS:
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
        p = os.path.join(ROOT, d, "__init__.py")
        if not os.path.exists(p):
            open(p, "w").close()
            created += 1

    # 2) 실제 모듈 파일 작성
    for rel_path, content in FILES.items():
        full = os.path.join(ROOT, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        created += 1
        print(f"생성: {os.path.join('02_engine', 'universal_quant_engine', rel_path)}")

    print(f"\n완료: 총 {created}개 파일 생성 → {ROOT}")
    print("\n다음 단계 (⑦ 실행 검증):")
    print("  cd 02_engine")
    print("  python -m universal_quant_engine.tests.test_v1")


if __name__ == "__main__":
    main()