"""표준 데이터 모델 — 모든 Provider가 이 형식으로 변환한다."""
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
