from typing import Dict, Any, List

from .interface import IRepo
from src.domain.room import Room


class MemRepo(IRepo):
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    
    def list(self, filters: Dict[str, Any] = {}) -> List[Room]:
        return [Room.from_dict(x) for x in self._data]