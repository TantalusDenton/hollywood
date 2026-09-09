from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    async def generate_structured(self, *, system: str, user: str, schema: type[T]) -> T:
        """Return a provider-validated structured response."""
