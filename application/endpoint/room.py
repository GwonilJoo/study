import uuid
import random
import json
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder

from src.repository.memrepo import MemRepo
from src.use_cases.room_list import RoomListUseCase
from src.domain.room import Room
from src.requests.room_list import RoomListRequest
from src.responses.responses import ResponseTypes
from src.serializers.room import RoomJsonEncoder


STATUS_CODE = {
    ResponseTypes.SUCCESS: 200,
    ResponseTypes.RESOURCE_ERROR: 404,
    ResponseTypes.PARAMETERS_ERROR: 400,
    ResponseTypes.SYSTEM_ERROR: 500,
}


rooms = [
    {
        "code": "f853578c-fc0f-4e65-81b8-566c5dffa35a",
        "size": random.randint(50, 500),
        "price": 39,
        "longitude": random.random(),
        "latitude": random.random(),
    },
    {
        "code": "fe2c3195-aeff-487a-a08f-e0bdc0ec6e9a",
        "size": random.randint(50, 500),
        "price": 66,
        "longitude": random.random(),
        "latitude": random.random(),
    },
    {
        "code": "913694c6-435a-4366-ba0d-da5334a611b2",
        "size": random.randint(50, 500),
        "price": 60,
        "longitude": random.random(),
        "latitude": random.random(),
    },
    {
        "code": "eed76e77-55c1-41ce-985d-ca49bf6c0585",
        "size": random.randint(50, 500),
        "price": 48,
        "longitude": random.random(),
        "latitude": random.random(),
    }
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
    return Response(
        content=json.dumps(response.value, cls=RoomJsonEncoder),
        status_code=STATUS_CODE[response.type],
        headers={"content-type": "application/json"}
    )
    # return JSONResponse(
    #     content=jsonable_encoder(response.value),
    #     status_code=STATUS_CODE[response.type]
    # )


room_router = APIRouter()
room_router.add_api_route("/rooms", room_list, methods=["GET"])