from typing import List, Dict, Any
import pymongo
from pydantic import BaseModel

from .interface import IRepo
from src.domain import room
from src.dto.room_list import RoomListDto


class MongoConfig(BaseModel):
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    APPLICATION_DB: str


class MongoRepo(IRepo):
    def __init__(self, config: MongoConfig) -> None:
        client = pymongo.MongoClient(
            host=config.HOST,
            port=config.PORT,
            username=config.USER,
            password=config.PASSWORD,
            authSource="admin"
        )

        self.db = client[config.APPLICATION_DB]
    

    def _create_room_objects(self, results: List[Dict[str, Any]]) -> List[room.Room]:
        return [room.Room.model_validate(res) for res in results]
    

    def list(self, filters: RoomListDto = RoomListDto()) -> List[room.Room]:
        collection = self.db.rooms

        mongo_filter = {}
        for key, value in filters.model_dump().items():
            if not value:
                continue

            key, operator = key.split("__")
            filter_value = mongo_filter.get(key, {})
            filter_value[f"${operator}"] = value
            mongo_filter[key] = filter_value

        result = collection.find(mongo_filter)
        return self._create_room_objects(result)