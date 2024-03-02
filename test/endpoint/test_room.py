import json
from unittest import mock

import pytest

from src.domain.room import Room
from src.responses import ResponseTypes, ResponseSuccess, ResponseFailure


@mock.patch("application.endpoint.room.RoomListUseCase.exec")
def test_get(mock_room_list_use_case_exec, client, domain_rooms):
    mock_room_list_use_case_exec.return_value = ResponseSuccess(domain_rooms)
    http_response = client.get("/rooms")

    data = json.loads(http_response.content.decode("UTF-8"))
    assert [Room.model_validate(x) for x in data] == domain_rooms

    mock_room_list_use_case_exec.assert_called()
    args, kwargs = mock_room_list_use_case_exec.call_args
    assert args[0].filters == {}

    assert http_response.status_code == 200
    assert http_response.headers["content-type"] == "application/json"


@mock.patch("application.endpoint.room.RoomListUseCase.exec")
def test_get_with_filters(mock_use_case, client, domain_rooms):
    mock_use_case.return_value = ResponseSuccess(domain_rooms)

    http_response = client.get(
        "/rooms?filter_price__gt=2&filter_price__lt=6"
    )

    data = json.loads(http_response.content.decode("UTF-8"))
    assert [Room.model_validate(x) for x in data] == domain_rooms

    mock_use_case.assert_called()
    args, kwargs = mock_use_case.call_args
    assert args[0].filters == {"price__gt": "2", "price__lt": "6"}

    assert http_response.status_code == 200
    assert http_response.headers["content-type"] == "application/json"


@pytest.mark.parametrize(
    "response_type, expected_status_code",
    [
        (ResponseTypes.PARAMETERS_ERROR, 400),
        (ResponseTypes.RESOURCE_ERROR, 404),
        (ResponseTypes.SYSTEM_ERROR, 500),
    ],
)
@mock.patch("application.endpoint.room.RoomListUseCase.exec")
def test_get_response_failures(
    mock_use_case,
    client,
    response_type,
    expected_status_code,
):
    mock_use_case.return_value = ResponseFailure(
        response_type,
        message="Just an error message",
    )

    http_response = client.get("/rooms?dummy_request_string")

    mock_use_case.assert_called()

    assert http_response.status_code == expected_status_code