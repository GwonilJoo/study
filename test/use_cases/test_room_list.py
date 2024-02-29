from unittest import TestCase, mock

from test.conftest import Fixture
from src.use_cases.room_list import RoomListUseCase
from src.requests.room_list import RoomListRequest
from src.responses import ResponseTypes


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

        request = RoomListRequest.from_dict({})
        room_list_use_case = RoomListUseCase(repo)
        response = room_list_use_case.exec(request)

        self.assertTrue(bool(response))
        repo.list.assert_called_with(filters={})
        self.assertEqual(response.value, self.domain_rooms)


    def test_room_list_with_filters(self):
        repo = mock.Mock()
        repo.list.return_value = self.domain_rooms

        filters = {"code__eq": 5}
        request = RoomListRequest.from_dict(filters)
        room_list_use_case = RoomListUseCase(repo)
        response = room_list_use_case.exec(request)

        self.assertTrue(bool(response))
        repo.list.assert_called_with(filters=filters)
        self.assertEqual(response.value, self.domain_rooms)


    def test_room_list_handles_generic_error(self):
        repo = mock.Mock()
        repo.list.side_effect = Exception("Just an error message")

        request = RoomListRequest.from_dict({})
        room_list_use_case = RoomListUseCase(repo)
        response = room_list_use_case.exec(request)

        self.assertFalse(bool(response))
        self.assertEqual(response.value, {"type": ResponseTypes.SYSTEM_ERROR, "message": "Exception: Just an error message"})


    def test_room_list_handles_bad_request(self):
        repo = mock.Mock()

        request = RoomListRequest.from_dict(5)
        room_list_use_case = RoomListUseCase(repo)
        response = room_list_use_case.exec(request)

        self.assertFalse(bool(response))
        self.assertEqual(response.value, {"type": ResponseTypes.PARAMETER_ERROR, "message": "filters: Is not iterable"})