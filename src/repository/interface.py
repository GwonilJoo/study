from abc import ABC, abstractmethod
from typing import List, Dict, Any
import uuid

from pydantic import BaseModel

from src.domain.room import Room


class Filters(BaseModel):
    code__eq: uuid.UUID | None = None
    price__eq: int | None = None
    price__lt: int | None = None
    price__gt: int | None = None


class IRepo(ABC):
    @abstractmethod
    def list(self, filters: Filters = Filters()) -> List[Room]:
        pass