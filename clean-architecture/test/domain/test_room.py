import unittest
import uuid

from src.domain.room import Room


class TestRoomModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.init_dict = {
            "code": uuid.uuid4(),
            "size": 200,
            "price": 100,
            "longitude": -0.09942,
            "latitude": 51.432, 
        }


    def setUp(self) -> None:
        print(f"[START] {self.__class__.__name__} - {self._testMethodName}")


    def tearDown(self) -> None:
        print(f"[Done] {self.__class__.__name__} - {self._testMethodName}\n")


    def test_room_model_init(self):
        room = Room(
            code=self.init_dict["code"],
            size=self.init_dict["size"],
            price=self.init_dict["price"],
            longitude=self.init_dict["longitude"],
            latitude=self.init_dict["latitude"]
        )

        self.assertEqual(room.code, self.init_dict["code"])
        self.assertEqual(room.size, self.init_dict["size"])
        self.assertEqual(room.price, self.init_dict["price"])
        self.assertEqual(room.longitude, self.init_dict["longitude"])
        self.assertEqual(room.latitude, self.init_dict["latitude"])


    def test_room_model_from_dict(self):
        room = Room.from_dict(self.init_dict)

        self.assertEqual(room.code, self.init_dict["code"])
        self.assertEqual(room.size, self.init_dict["size"])
        self.assertEqual(room.price, self.init_dict["price"])
        self.assertEqual(room.longitude, self.init_dict["longitude"])
        self.assertEqual(room.latitude, self.init_dict["latitude"])


    def test_room_model_to_dict(self):
        room = Room.from_dict(self.init_dict)

        self.assertEqual(room.to_dict(), self.init_dict)


    def test_room_model_comparison(self):
        room1 = Room.from_dict(self.init_dict)
        room2 = Room.from_dict(self.init_dict)

        self.assertEqual(room1, room2)