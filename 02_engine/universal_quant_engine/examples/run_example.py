"""Universal Quant Engine 사용 예시."""
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
