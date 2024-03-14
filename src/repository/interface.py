from abc import ABC, abstractmethod
from typing import List, Dict, Any
import uuid

from pydantic import BaseModel

from src.domain.room import Room
from src.dto.room_list import RoomListDto


class IRepo(ABC):
    @abstractmethod
    def list(self, filters: RoomListDto.Read = RoomListDto.Read()) -> List[Room]:
        pass