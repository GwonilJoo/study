from unittest import TestCase

from src.requests.room_list import RoomListRequest


class TestRoomListRequest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass


    def setUp(self) -> None:
        print(f"[START] {self.__class__.__name__} - {self._testMethodName}")


    def tearDown(self) -> None:
        print(f"[Done] {self.__class__.__name__} - {self._testMethodName}\n")


    # def test_build_room_list_request_without_parameters(self):
    #     request = RoomListRequest.from_dict({})

    #     self.assertTrue(bool(request))


    def test_build_room_list_request_from_empty_dict(self):
        request = RoomListRequest.from_dict({})

        self.assertEqual(request.filters, {})
        self.assertTrue(bool(request))


    def test_build_room_list_request_with_invalid_filters_parameter(self):
        request = RoomListRequest.from_dict(5)

        self.assertTrue(request.has_erros())
        for error in request.errors:
            self.assertEqual(error["parameter"], "filters")
        self.assertFalse(bool(request))


    def test_build_room_list_request_with_incorrect_filters_keys(self):
        request = RoomListRequest.from_dict({"a": 1})

        self.assertTrue(request.has_erros())
        for error in request.errors:
            self.assertEqual(error["parameter"], "filters")
        self.assertFalse(bool(request))


    def test_build_room_list_request_with_accepted_filters(self):
        keys = ["code__eq", "price__eq", "price__lt", "price__gt"]

        def test(key: str):
            filters = {key: 1}
            request = RoomListRequest.from_dict(filters)

            self.assertEqual(request.filters, filters)
            self.assertTrue(bool(request))
        
        for key in keys:
            test(key)


    def test_build_room_list_request_with_rejected_filters(self):
        keys = ["code__lt", "code__gt"]

        def test(key: str):
            filters = {key: 1}
            request = RoomListRequest.from_dict(filters)

            self.assertTrue(request.has_erros())
            for error in request.errors:
                self.assertEqual(error["parameter"], "filters")
            self.assertFalse(bool(request))
        
        for key in keys:
            test(key)