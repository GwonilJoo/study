import json
import uuid
from unittest import TestCase

from test.conftest import Fixture
from src.serializers.room import RoomJsonEncoder
from src.domain.room import Room






class TestRoomJsonEncoder(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.domain_room = Fixture.domain_rooms(1)[0]
        cls.room_dict = cls.domain_room.to_dict()


    def setUp(self) -> None:
        print(f"[START] {self.__class__.__name__} - {self._testMethodName}")


    def tearDown(self) -> None:
        print(f"[Done] {self.__class__.__name__} - {self._testMethodName}\n")


    def test_serialize_domain_room(self):
        room = Fixture.domain_rooms(1)[0]
        expected_json = f"""{{"code": "{room.code}", "size": {room.size}, "price": {room.price}, "longitude": {room.longitude}, "latitude": {room.latitude}}}"""

        json_room = json.dumps(room, cls=RoomJsonEncoder)

        self.assertEqual(json_room, expected_json)