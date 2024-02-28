import uuid
import random
from typing import List

from src.domain.room import Room


class Fixture:
    @staticmethod
    def domain_rooms(num_of_rooms: int) -> List[Room]:
        return [
            Room(
                code=uuid.uuid4(),
                size=random.randint(50, 500),
                price=random.randint(10, 100),
                longitude=random.random(),
                latitude=random.random(),
            )
            for _ in range(num_of_rooms)
        ]
    
    
    @staticmethod
    def room_dicts(num_of_rooms: int) -> List[Room]:
        return [
            {
                "code": uuid.uuid4(),
                "size": random.randint(50, 500),
                "price": random.randint(10, 100),
                "longitude": random.random(),
                "latitude": random.random(),
            }
            for _ in range(num_of_rooms)
        ]