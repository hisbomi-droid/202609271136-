"""Universal Quant Engine V1
Provider → Normalize → Validate → 표준 OHLCV → 지표 → 전략 → 백테스트 → 신뢰도
"""
from .api import MarketEngine, Market
from .collectors.fdr_provider import FinanceDataReaderProvider
from .collectors.mock_provider import MockProvider
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
    "FinanceDataReaderProvider", "MockProvider",
]
