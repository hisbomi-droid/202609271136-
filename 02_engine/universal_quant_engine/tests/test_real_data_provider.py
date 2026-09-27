import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from universal_quant_engine import Market
from universal_quant_engine.collectors import FinanceDataReaderProvider


class TestRealDataProvider(unittest.TestCase):
    def test_provider_registration_and_instantiation(self):
        provider = FinanceDataReaderProvider(exchange="KRX")
        self.assertEqual(provider.name, "fdr")
        self.assertEqual(provider.exchange, "KRX")

    def test_market_allows_fdr_provider(self):
        market = Market(providers=["fdr"])
        self.assertIn("fdr", market.providers)


if __name__ == "__main__":
    unittest.main()
