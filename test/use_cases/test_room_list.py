from unittest import mock
import uuid

from src.use_cases.room_list import RoomListUseCase
from src.requests.room_list import RoomListRequest
from src.responses import ResponseTypes
from src.repository.interface import Filters


def test_room_list_without_parameters(domain_rooms):
    repo = mock.Mock()
    repo.list.return_value = domain_rooms

    request = RoomListRequest.from_dict({})
    room_list_use_case = RoomListUseCase(repo)
    response = room_list_use_case.exec(request)

    assert bool(response) is True
    repo.list.assert_called_with(filters=Filters())
    assert response.value == domain_rooms


def test_room_list_with_filters(domain_rooms):
    repo = mock.Mock()
    repo.list.return_value = domain_rooms

    filters = {"code__eq": str(uuid.uuid4())}
    request = RoomListRequest.from_dict(filters)
    room_list_use_case = RoomListUseCase(repo)
    response = room_list_use_case.exec(request)

    assert bool(response) is True
    repo.list.assert_called_with(filters=Filters(**filters))
    assert response.value == domain_rooms


def test_room_list_handles_generic_error():
    repo = mock.Mock()
    repo.list.side_effect = Exception("Just an error message")

    request = RoomListRequest.from_dict({})
    room_list_use_case = RoomListUseCase(repo)
    response = room_list_use_case.exec(request)

    assert bool(response) is False
    assert response.value == {"type": ResponseTypes.SYSTEM_ERROR, "message": "Exception: Just an error message"}


def test_room_list_handles_bad_request():
    repo = mock.Mock()

    request = RoomListRequest.from_dict(5)
    room_list_use_case = RoomListUseCase(repo)
    response = room_list_use_case.exec(request)

    assert bool(response) is False
    assert response.value == {"type": ResponseTypes.PARAMETERS_ERROR, "message": "filters: Is not iterable"}