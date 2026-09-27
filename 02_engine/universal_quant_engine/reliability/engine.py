"""RELIABILITY ENGINE — 구성요소를 보존하는 신뢰도 리포트."""
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
