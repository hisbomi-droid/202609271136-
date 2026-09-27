"""Mock Provider — 엔진 구조 검증 및 테스트용. 결정적(deterministic) 데이터 생성."""
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
