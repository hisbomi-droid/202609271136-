import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from universal_quant_engine import Market
from universal_quant_engine.collectors.fdr_provider import FinanceDataReaderProvider


class FakeFinanceDataReader:
    @staticmethod
    def DataReader(symbol, start, end=None, exchange=None):
        return {
            "symbol": symbol,
            "start": start,
            "end": end,
            "exchange": exchange,
            "data": [
                {"Date": "2024-01-02", "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.5, "Volume": 1000},
                {"Date": "2024-01-03", "Open": 100.5, "High": 102.0, "Low": 100.0, "Close": 101.5, "Volume": 1200},
            ],
        }


class TestFinanceDataReaderAdapter(unittest.TestCase):
    def test_provider_builds_bars_from_dataframe(self):
        with patch("universal_quant_engine.collectors.fdr_provider.fdr", FakeFinanceDataReader):
            provider = FinanceDataReaderProvider()
            bars = provider.get_bars("005930", count=2)
            self.assertEqual(len(bars), 2)
            self.assertEqual(bars[0].symbol, "005930")
            self.assertEqual(bars[0].source, "fdr")
            self.assertGreater(bars[0].close, 0)

    def test_market_engine_registers_fdr_provider(self):
        market = Market(providers=["fdr"], provider_kwargs={"fdr": {"exchange": "KRX"}})
        self.assertIn("fdr", market.providers)


if __name__ == "__main__":
    unittest.main()
