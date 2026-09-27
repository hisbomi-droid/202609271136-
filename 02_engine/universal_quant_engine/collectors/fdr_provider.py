"""FinanceDataReader 기반 데이터 Provider.

가장 안정적인 기본 선택: 한국 시장 데이터는 KRX/금융재료를 직접 제공하는
FinanceDataReader를 우선 사용하고, 필요 시 네이버/크롤링을 보조 소스로 둔다.
"""
from datetime import datetime
from typing import List, Optional

import pandas as pd

from ..core.interfaces import MarketDataProvider
from ..core.models import MarketBar, Quote

try:
    import FinanceDataReader as fdr
except ImportError:  # pragma: no cover
    fdr = None


class FinanceDataReaderProvider(MarketDataProvider):
    """한국 주식 데이터 수집용 Provider.

    사용 예:
        provider = FinanceDataReaderProvider(exchange="KRX")
        bars = provider.get_bars("005930", count=30)
    """

    name = "fdr"

    def __init__(self, exchange: str = "KRX", start_offset_days: int = 365,
                 end_date: Optional[str] = None):
        self.exchange = exchange
        self.start_offset_days = start_offset_days
        self.end_date = end_date

    def _ensure_available(self) -> None:
        if fdr is None:
            raise RuntimeError(
                "FinanceDataReader가 설치되지 않았습니다. `pip install finance-datareader` 를 실행하세요."
            )

    def get_quote(self, symbol: str) -> Optional[Quote]:
        bars = self.get_bars(symbol, count=1)
        if not bars:
            return None
        bar = bars[0]
        return Quote(symbol=symbol, timestamp=bar.timestamp, price=bar.close,
                     volume=bar.volume, source=self.name)

    def get_bars(self, symbol: str, timeframe: str = "1d",
                 count: int = 200) -> List[MarketBar]:
        self._ensure_available()

        end = self.end_date or datetime.now().strftime("%Y-%m-%d")
        start = (pd.Timestamp(end) - pd.Timedelta(days=max(self.start_offset_days, count))).strftime("%Y-%m-%d")

        data = fdr.DataReader(symbol, start, end, exchange=self.exchange)
        if data is None:
            return []

        if isinstance(data, dict):
            frame = pd.DataFrame(data.get("data", []))
        else:
            frame = pd.DataFrame(data)

        if frame.empty:
            return []

        normalized = frame.copy()
        if "Date" in normalized.columns:
            normalized["Date"] = pd.to_datetime(normalized["Date"])
        else:
            normalized.index = pd.to_datetime(normalized.index)
            normalized = normalized.reset_index().rename(columns={"index": "Date"})

        column_map = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        normalized = normalized.rename(columns={k: v for k, v in column_map.items() if k in normalized.columns})

        if "Date" not in normalized.columns:
            raise ValueError(f"FDR 응답에 Date 컬럼이 없어 표준화할 수 없습니다: {list(normalized.columns)}")

        for col in ["open", "high", "low", "close", "volume"]:
            if col in normalized.columns:
                normalized[col] = pd.to_numeric(normalized[col], errors="coerce")

        if "open" not in normalized.columns or "close" not in normalized.columns:
            return []

        latest = normalized.sort_values("Date").tail(count)
        bars = []
        for _, row in latest.iterrows():
            ts = pd.Timestamp(row["Date"]).to_pydatetime()
            bars.append(MarketBar(
                symbol=str(symbol),
                timestamp=ts,
                open=float(row.get("open", 0.0)),
                high=float(row.get("high", 0.0)),
                low=float(row.get("low", 0.0)),
                close=float(row.get("close", 0.0)),
                volume=float(row.get("volume", 0.0)),
                source=self.name,
                source_timestamp=ts,
                received_timestamp=datetime.now(),
                processed_timestamp=datetime.now(),
                raw_id=f"fdr:{symbol}:{ts.isoformat()}",
            ))
        return bars

    def health(self) -> bool:
        try:
            self._ensure_available()
            return True
        except Exception:
            return False
