import uuid
import random
from typing import List

from fastapi import APIRouter

from src.repository.memrepo import MemRepo
from src.use_cases.room_list import RoomListUseCase
from src.domain.room import Room


rooms = [
    {
        "code": uuid.uuid4(),
        "size": random.randint(50, 500),
        "price": random.randint(10, 100),
        "longitude": random.random(),
        "latitude": random.random(),
    }
    for _ in range(4)
]


def room_list() -> List[Room]:
    repo = MemRepo(rooms)
    room_list_use_case = RoomListUseCase(repo)
    result = room_list_use_case.exec()
    return result


room_router = APIRouter()
room_router.add_api_route("/rooms", room_list, methods=["GET"])