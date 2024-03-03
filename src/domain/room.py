import uuid
from pydantic import BaseModel


class Room(BaseModel):
    code: uuid.UUID
    size: int
    price: int
    longitude: float
    latitude: float