import uuid
from unittest import TestCase, mock
from typing import List
import random

from test.conftest import Fixture
from src.domain.room import Room
from src.use_cases.room_list import RoomListUseCase


class TestRoomListUseCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.domain_rooms = Fixture.domain_rooms(4)

    def setUp(self) -> None:
        print(f"[START] {self.__class__.__name__} - {self._testMethodName}")


    def tearDown(self) -> None:
        print(f"[Done] {self.__class__.__name__} - {self._testMethodName}\n")


    def test_room_list_without_parameters(self):
        repo = mock.Mock()
        repo.list.return_value = self.domain_rooms

        room_list_use_case = RoomListUseCase(repo)
        result = room_list_use_case.exec()

        repo.list.assert_called_with()
        self.assertEqual(result, self.domain_rooms)