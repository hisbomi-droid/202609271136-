"""모든 확장점(Provider / Indicator / Strategy / Validator)의 표준 인터페이스."""
from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd

from .models import MarketBar, Quote


class MarketDataProvider(ABC):
    """데이터 수집 Provider. 새 사이트는 이 클래스만 구현하면 된다."""
    name: str = "base"

    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[Quote]:
        ...

    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str = "1d",
                 count: int = 200) -> List[MarketBar]:
        ...

    def subscribe(self, symbol: str) -> None:
        """실시간 구독 (지원하지 않으면 no-op)."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> bool:
        ...


class Indicator(ABC):
    """지표. 계산만 하고 매매 조건을 포함하지 않는다."""
    name: str = "base"

    @abstractmethod
    def calculate(self, data: pd.DataFrame, **params) -> pd.Series:
        ...


class Strategy(ABC):
    """전략. 지표를 조합해 진입/청산 신호를 만든다. 각 근거를 보존한다."""
    name: str = "base"

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> pd.DataFrame:
        """columns: signal(1/0/-1), reasons(dict) 를 포함한 DataFrame 반환."""
        ...


class Validator(ABC):
    """데이터 품질 검증 플러그인."""
    name: str = "base"

    @abstractmethod
    def validate(self, data: pd.DataFrame) -> dict:
        """{passed: bool, details: dict} 형태 반환."""
        ...
