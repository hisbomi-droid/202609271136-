"""NORMALIZER — 서로 다른 원천 데이터를 표준 MarketBar 형식으로 변환."""
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
