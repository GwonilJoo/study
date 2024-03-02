from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import uuid
from typing import Dict, Any

from pydantic import BaseModel

from src.repository.interface import Filters


class RoomListRequest:
    accepted_filters = {"code__eq", "price__eq", "price__lt", "price__gt"}


    @classmethod
    def from_dict(cls, filters: Dict[str, Any] = {}) -> RoomListValidRequest | RoomListInvalidRequest:
        invalid_request = RoomListInvalidRequest()

        if filters is not None:
            if not isinstance(filters, Mapping):
                invalid_request.add_error("filters", "Is not iterable")
                return invalid_request
            for key in filters.keys():
                if key not in cls.accepted_filters:
                    invalid_request.add_error("filters", f"Key {key} cannot be used")
                    continue
            
            if invalid_request.has_erros():
                return invalid_request

        # return RoomListValidRequest(
        #     code__eq=filters.get("code__eq", None),
        #     price__eq=filters.get("price__eq", None),
        #     price__lt=filters.get("price__lt", None),
        #     price__gt=filters.get("price__gt", None),
        # )
        return RoomListValidRequest(filters=Filters(**filters))


    def __bool__(self) -> bool:
        return True
    

# class RoomListValidRequest:
#     def __init__(self, filters: Dict[str, Any]) -> None:
#         self.filters = filters


#     def __bool__(self) -> bool:
#         return True
    

# class Filters(BaseModel):
#     code__eq: uuid.UUID | None = None
#     price__eq: int | None = None
#     price__lt: int | None = None
#     price__gt: int | None = None


class RoomListValidRequest:
    def __init__(self, filters: Filters) -> None:
        self.filters = filters

    def __bool__(self) -> bool:
        return True
    

class RoomListInvalidRequest:
    def __init__(self) -> None:
        self.errors = []

    
    def add_error(self, parameter, message) -> None:
        self.errors.append({"parameter": parameter, "message": message})

    
    def has_erros(self) -> bool:
        return len(self.errors) > 0
    

    def __bool__(self) -> bool:
        return False