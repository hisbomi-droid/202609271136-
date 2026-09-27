"""V1 통합 테스트 — 데이터→지표→전략→백테스트→검증→신뢰도 전 파이프라인."""
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
    print(f"\n{'='*50}\n{len(results) - len(failed)}/{len(results)} 통과")
    if failed:
        print("실패 항목:", failed)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
