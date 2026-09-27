import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from universal_quant_engine import Market
from universal_quant_engine.strategies.trend.ema_cross import EmaCrossStrategy


def main():
    market = Market(providers=['fdr'])
    data = market.market('005930', count=60)
    print(data.tail(3)[['timestamp', 'open', 'high', 'low', 'close', 'volume']])

    indicators = market.analyze(data, indicators=['ema', 'rsi', 'atr'])
    print(indicators[['close', 'ema', 'rsi', 'atr']].tail(3))

    bt = market.backtest(data, EmaCrossStrategy())
    print(bt['report'])


if __name__ == '__main__':
    main()
