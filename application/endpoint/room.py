import uuid
import random
import json
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.repository.memrepo import MemRepo
from src.use_cases.room_list import RoomListUseCase
from src.domain.room import Room
from src.requests.room_list import RoomListRequest
from src.responses.responses import ResponseTypes
from src.serializers.room import RoomJsonEncoder


STATUS_CODE = {
    ResponseTypes.SUCCESS: 200,
    ResponseTypes.RESOURCE_ERROR: 404,
    ResponseTypes.PARAMETER_ERROR: 400,
    ResponseTypes.SYSTEM_ERROR: 500,
}


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


def room_list(
        request: Request,
        filter_code__eq: str | None = None,
        filter_price__eq: int | None = None, 
        filter_price__lt: int | None = None, 
        filter_price__gt: int | None = None,
    ) -> List[Room]:
    qrystr_params = {
        "filters": {},
    }

    for arg, value in request.query_params.items():
        if arg.startswith("filter_"):
            qrystr_params["filters"][arg.replace("filter_", "")] = value

    request = RoomListRequest.from_dict(qrystr_params["filters"])

    repo = MemRepo(rooms)
    room_list_use_case = RoomListUseCase(repo)
    response = room_list_use_case.exec(request)
    return JSONResponse(
        content=json.dumps(response.value, cls=RoomJsonEncoder),
        status_code=STATUS_CODE[response.type],
    )


room_router = APIRouter()
room_router.add_api_route("/rooms", room_list, methods=["GET"])