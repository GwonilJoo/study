import pytest

from src.requests.room_list import RoomListRequest


# def test_build_room_list_request_without_parameters(self):
#     request = RoomListRequest.from_dict({})

#     self.assertTrue(bool(request))


def test_build_room_list_request_from_empty_dict():
    request = RoomListRequest.from_dict({})

    assert request.filters == {}
    assert bool(request) is True


def test_build_room_list_request_with_invalid_filters_parameter():
    request = RoomListRequest.from_dict(5)

    assert request.has_erros() is True
    for error in request.errors:
        assert error["parameter"] == "filters"
    assert bool(request) is False


def test_build_room_list_request_with_incorrect_filters_keys():
    request = RoomListRequest.from_dict({"a": 1})

    assert request.has_erros() is True
    for error in request.errors:
        assert error["parameter"] == "filters"
    assert bool(request) is False


@pytest.mark.parametrize("key", ["code__eq", "price__eq", "price__lt", "price__gt"])
def test_build_room_list_request_with_accepted_filters(key):
    filters = {key: 1}
    request = RoomListRequest.from_dict(filters)

    assert request.filters == filters
    assert bool(request) is True


@pytest.mark.parametrize("key", ["code__lt", "code__gt"])
def test_build_room_list_request_with_rejected_filters(key):
    filters = {key: 1}
    request = RoomListRequest.from_dict(filters)

    assert request.has_erros() is True
    for error in request.errors:
        assert error["parameter"] == "filters"
    assert bool(request) is False