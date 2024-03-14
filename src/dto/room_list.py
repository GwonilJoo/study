from __future__ import annotations
from typing import Dict, Any, List

from pydantic import BaseModel

from src.domain.room import Room


class RoomListDto:
    class Read(BaseModel):
        code__eq: str | None = None
        price__eq: int | None = None
        price__lt: int | None = None
        price__gt: int | None = None


    class Response(BaseModel):
        code: str
        size: int
        price: int
        longitude: float
        latitude: float


    @classmethod
    def read(cls, request: Dict[str, Any]) -> Read:
        return cls.Read(**request)
    
    
    @classmethod
    def response(cls, entities: List[Room]) -> List[Response]:
        return [cls.Response(**entity.model_dump()) for entity in entities]