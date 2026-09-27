"""Market / MarketEngine — 외부 프로그램용 최상위 API.

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
from .collectors.fdr_provider import FinanceDataReaderProvider
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
        self.registry.register(FinanceDataReaderProvider)
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
