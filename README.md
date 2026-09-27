# Universal Quant Engine v1

A compact quant research and backtesting framework built around a provider → normalize → validate → indicator → strategy → backtest → reliability pipeline.

## Structure

- `02_engine/universal_quant_engine/` — package source
- `setup_ume_v1.py` — project scaffold generator

## Data source strategy

The engine is designed around pluggable providers.

Preferred order:

1. `FinanceDataReader` for Korean market data
2. KRX-native provider for specialized access
3. Naver crawling only as fallback or secondary source

This avoids brittle scraping as the default path while keeping the architecture open for future sources.

## Installation

```bash
python3 -m pip install pandas numpy finance-datareader
```

## Quick start

```bash
cd 02_engine
python3 -m universal_quant_engine.tests.test_v1
```

## Example usage

```python
from universal_quant_engine import Market
from universal_quant_engine.strategies.trend.ema_cross import EmaCrossStrategy

market = Market(providers=['fdr'])
stock = market.market('005930', count=60)
indicators = market.analyze(stock, indicators=['ema', 'rsi', 'atr'])
print(indicators.tail())

result = market.backtest(stock, EmaCrossStrategy())
print(result['report'])
```

## Notes

- Uses `MarketBar` as the standard normalized OHLCV representation.
- Validation and reliability scoring are preserved as separate pipeline stages.
- All providers share the same interface via `MarketDataProvider`.
