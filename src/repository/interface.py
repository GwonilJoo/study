from abc import ABC, abstractmethod
from typing import List, Dict, Any

from src.domain.room import Room


class IRepo(ABC):
    @abstractmethod
    def list(self, filters: Dict[str, Any] = {}) -> List[Room]:
        pass