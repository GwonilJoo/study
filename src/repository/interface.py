from abc import ABC, abstractmethod
from typing import List

from src.domain.room import Room


class IRepo(ABC):
    @abstractmethod
    def list(self) -> List[Room]:
        pass