"""Backtest Engine — DataFeed → Strategy → Order → Execution → Position → Portfolio.

현실 요소(수수료/슬리피지/거래세) 반영. 시장가 주문, 다음 봉 시가 체결 기준.
Look-ahead bias 방지: i 봉의 신호는 i+1 봉 시가에 체결된다.
"""
import pandas as pd

from .performance import PerformanceReport


class BrokerConfig:
    """한국 주식시장용 기본 설정 (사용자 환경에 맞게 교체)."""
    def __init__(self, commission: float = 0.00015, tax: float = 0.0018,
                 slippage: float = 0.0002, initial_cash: float = 100_000_000.0):
        self.commission = commission
        self.tax = tax          # 매도 시에만
        self.slippage = slippage
        self.initial_cash = initial_cash


class BacktestEngine:
    def __init__(self, config: BrokerConfig = None):
        self.config = config or BrokerConfig()

    def run(self, data: pd.DataFrame, strategy) -> dict:
        """data: 표준 OHLCV. strategy.generate_signal(data) → signal 컬럼."""
        cfg = self.config
        df = strategy.generate_signal(data)
        cash = cfg.initial_cash
        position = 0.0
        entry_price = 0.0
        equity, trades = [], []

        for i in range(len(df)):
            row = df.iloc[i]
            # ① 이전 봉(i-1)의 신호를 현재 봉 시가에 체결
            if i > 0:
                sig = df["signal"].iloc[i - 1]
                price = row["open"] * (1 + cfg.slippage * sig)

                if sig == 1 and position == 0:  # 진입
                    qty = cash * 0.95 / (price * (1 + cfg.commission))
                    if qty > 0:
                        cost = qty * price * (1 + cfg.commission)
                        cash -= cost
                        position = qty
                        entry_price = price
                elif sig == -1 and position > 0:  # 청산
                    proceeds = position * price * (1 - cfg.commission - cfg.tax)
                    pnl = proceeds - position * entry_price * (1 + cfg.commission)
                    trades.append({
                        "exit_time": row["timestamp"] if "timestamp" in row else i,
                        "entry_price": entry_price, "exit_price": price,
                        "pnl": pnl, "return": pnl / (position * entry_price),
                        "reasons": df["reasons"].iloc[i - 1],
                    })
                    cash += proceeds
                    position = 0.0

            # ② 당일 평가액
            equity.append(cash + position * row["close"])

        trades_df = pd.DataFrame(trades)
        report = PerformanceReport(pd.Series(equity), trades_df).build()
        return {"report": report, "equity_curve": pd.Series(equity),
                "trades": trades_df, "signals": df[["signal"]] if "signal" in df else None}
