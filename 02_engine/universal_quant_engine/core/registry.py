"""Provider 레지스트리 — 새 Provider 추가 시 엔진 수정 없이 등록만 한다."""
from typing import Dict, Type
from .interfaces import MarketDataProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, Type[MarketDataProvider]] = {}

    def register(self, cls: Type[MarketDataProvider]) -> Type[MarketDataProvider]:
        self._providers[cls.name] = cls
        return cls

    def create(self, name: str, **kwargs) -> MarketDataProvider:
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' 미등록. 등록된: {list(self._providers)}")
        return self._providers[name](**kwargs)

    def available(self) -> list:
        return list(self._providers)
