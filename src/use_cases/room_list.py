from typing import List

from src.domain.room import Room
from src.repository.interface import IRepo
from src.requests.room_list import RoomListValidRequest, RoomListInvalidRequest
from src.responses import ResponseTypes, ResponseSuccess, ResponseFailure


class RoomListUseCase:
    def __init__(self, repo: IRepo):
        self._repo = repo


    def exec(
            self, 
            request: RoomListValidRequest | RoomListInvalidRequest
        ) -> ResponseSuccess | ResponseFailure:
        if not request:
            return ResponseFailure.from_invalid_request(request)
        try:
            rooms = self._repo.list(filters=request.filters)
            return ResponseSuccess(rooms)
        except Exception as e:
            return ResponseFailure(ResponseTypes.SYSTEM_ERROR, e)