from unittest import TestCase

from src.responses import ResponseTypes, ResponseSuccess, ResponseFailure
from src.requests.room_list import RoomListInvalidRequest


class TestResponses(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.SUCCESS_VALUE = {"key": ["value1", "value2"]}
        cls.GENERIC_RESPONSE_TYPE = "Response"
        cls.GENERIC_RESPONSE_MESSAGE = "This is a response"


    def setUp(self) -> None:
        print(f"[START] {self.__class__.__name__} - {self._testMethodName}")


    def tearDown(self) -> None:
        print(f"[Done] {self.__class__.__name__} - {self._testMethodName}\n")


    def test_response_success_is_true(self):
        response = ResponseSuccess()

        self.assertTrue(bool(response))


    def test_response_failure_is_false(self):
        response = ResponseFailure(self.GENERIC_RESPONSE_TYPE, self.GENERIC_RESPONSE_MESSAGE)

        self.assertFalse(bool(response))


    def test_response_success_has_type_and_value(self):
        response = ResponseSuccess(self.SUCCESS_VALUE)

        self.assertEqual(response.type, ResponseTypes.SUCCESS)
        self.assertEqual(response.value, self.SUCCESS_VALUE)


    def test_response_failure_has_type_and_message(self):
        response = ResponseFailure(self.GENERIC_RESPONSE_TYPE, self.GENERIC_RESPONSE_MESSAGE)

        self.assertEqual(response.type, self.GENERIC_RESPONSE_TYPE)
        self.assertEqual(response.message, self.GENERIC_RESPONSE_MESSAGE)
        self.assertEqual(response.value, {"type": self.GENERIC_RESPONSE_TYPE, "message": self.GENERIC_RESPONSE_MESSAGE})


    def test_response_failure_initialisation_with_exception(self):
        response = ResponseFailure(self.GENERIC_RESPONSE_TYPE, Exception("Just an error message"))

        self.assertEqual(response.type, self.GENERIC_RESPONSE_TYPE)
        self.assertEqual(response.message, "Exception: Just an error message")


    def test_response_failure_from_empty_invalid_request(self):
        response = ResponseFailure.from_invalid_request(RoomListInvalidRequest())

        self.assertFalse(bool(response))
        self.assertEqual(response.type, ResponseTypes.PARAMETER_ERROR)


    def test_response_failure_from_invalid_request_with_errors(self):
        request = RoomListInvalidRequest()
        request.add_error("path", "Is mandatory")
        request.add_error("path", "can't be blank")

        response = ResponseFailure.from_invalid_request(request)

        self.assertFalse(bool(response))
        self.assertEqual(response.type, ResponseTypes.PARAMETER_ERROR)
        self.assertEqual(response.message, "path: Is mandatory\npath: can't be blank")