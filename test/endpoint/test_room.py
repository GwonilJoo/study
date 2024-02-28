import json
from unittest import TestCase, mock
import uuid

from test.conftest import Fixture
from src.domain.room import Room


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
        mock_room_list_use_case_exec.return_value = self.rooms
        
        client = Fixture.client()
        response = client.get("/rooms")
        print(f"response.content: {response.content}")
        # print(f"response.status_code: {response.status_code}")
        # print(f"response.headers: {response.headers["content-type"]}")
        
        self.assertEqual(json.loads(response.content.decode("UTF-8")), self.room_dicts)
        mock_room_list_use_case_exec.assert_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
