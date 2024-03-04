import uuid
from pydantic import BaseModel


class Room(BaseModel):
    code: str
    size: int
    price: int
    longitude: float
    latitude: float