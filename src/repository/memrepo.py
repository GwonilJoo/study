from typing import Dict, Any, List

from .interface import IRepo, Filters
from src.domain.room import Room


class MemRepo(IRepo):
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    
    def list(self, filters: Filters = Filters()) -> List[Room]:
        result = [Room.model_validate(x) for x in self._data]
        
        if filters.code__eq:
            result = [x for x in result if x.code == filters.code__eq]

        if filters.price__eq:
            result = [x for x in result if x.price == filters.price__eq]

        if filters.price__lt:
            result = [x for x in result if x.price < filters.price__lt]

        if filters.price__gt:
            result = [x for x in result if x.price > filters.price__gt]

        return result