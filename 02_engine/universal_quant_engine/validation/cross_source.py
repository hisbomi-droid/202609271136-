"""CROSS-SOURCE VERIFICATION — 원천 간 값 비교. 하나를 임의로 선택하지 않고 차이를 보존한다."""
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
