from typing import List
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

from src.domain import room
from src.repository.interface import IRepo, Filters
from .postgres_objects import Base, Room


class PostgresConfig(BaseModel):
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    APPLICATION_DB: str


class PostgresRepo(IRepo):
    def __init__(self, config: PostgresConfig):
        connection_string = f"postgresql+psycopg2://{config.USER}:{config.PASSWORD}@{config.HOST}:{config.PORT}/{config.APPLICATION_DB}"

        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        Base.metadata.bind = self.engine

    
    def _create_room_objects(self, results: List[Room]) -> List[room.Room]:
        return [
            room.Room(
                code=res.code,
                size=res.size,
                price=res.price,
                longitude=res.longitude,
                latitude=res.latitude,
            ) for res in results
        ]
    

    def list(self, filters: Filters = Filters()) -> List[room.Room]:
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()

        query = session.query(Room)

        if filters.code__eq:
            query = query.filter(Room.code == str(filters.code__eq))

        if filters.price__eq:
            query = query.filter(Room.price == filters.price__eq)

        if filters.price__lt:
            query = query.filter(Room.price < filters.price__lt)

        if filters.price__gt:
            query = query.filter(Room.price > filters.price__gt)

        return self._create_room_objects(query.all())