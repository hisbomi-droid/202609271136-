"""Collector providers for the Universal Quant Engine.

This package contains both the built-in mock provider used for test coverage and the
real-world FinanceDataReader adapter used in production-style data collection.
"""

from .mock_provider import MockProvider
from .fdr_provider import FinanceDataReaderProvider

__all__ = ["MockProvider", "FinanceDataReaderProvider"]
