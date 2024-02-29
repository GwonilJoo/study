import json
from unittest import TestCase, mock
import uuid

from test.conftest import Fixture
from src.domain.room import Room
from src.responses import ResponseTypes, ResponseSuccess, ResponseFailure


class TestRoomEndpoint(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.room_dicts = Fixture.room_dicts(1)
        cls.rooms = [Room.from_dict(data) for data in cls.room_dicts]


    def setUp(self) -> None:
        print(f"[START] {self.__class__.__name__} - {self._testMethodName}")


    def tearDown(self) -> None:
        print(f"[Done] {self.__class__.__name__} - {self._testMethodName}\n")


    @mock.patch("application.endpoint.room.RoomListUseCase.exec")
    def test_get(self, mock_room_list_use_case_exec):
        mock_room_list_use_case_exec.return_value = ResponseSuccess(self.rooms)
        
        client = Fixture.client()
        response = client.get("/rooms")
        print(f"response.content: {response.content}")
        print(f"response.status_code: {response.status_code}")
        print(f"response.headers: {response.headers['content-type']}")
        
        print(f"response.content: {json.loads(response.content)}")
        print(f"room_dicts: {self.room_dicts}")

        json_decode = json.loads(response.content.decode("UTF-8"))
        print(type(json_decode))
        self.assertEqual(json.loads(response.content.decode("UTF-8")), self.room_dicts)
        self.assertEqual(
            [{"code": "0a55c31d-3831-43fd-8f76-50686614f9bf", "size": 468, "price": 13, "longitude": 0.13125314853977488, "latitude": 0.5822431932912345}],
            [{'code': '0a55c31d-3831-43fd-8f76-50686614f9bf', 'size': 468, 'price': 13, 'longitude': 0.13125314853977488, 'latitude': 0.5822431932912345}]
        )
        # mock_room_list_use_case_exec.assert_called()
        # args, kwargs = mock_room_list_use_case_exec.call_args
        # self.assertEqual(args[1].filters, {})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
