from typing import List, Dict, Any, Generator

import pymongo
from pymongo.database import Database
import pytest

from src.repository.postgres.postgres_objects import Base, Room
from application.config import TestConfig


@pytest.fixture(scope="session")
def mg_database_empty(app_configuration: TestConfig) -> Generator[Database, None, None]:
    client = pymongo.MongoClient(
        host=app_configuration.MONGO_HOST,
        port=app_configuration.MONGO_PORT,
        username=app_configuration.MONGO_USER,
        password=app_configuration.MONGO_PASSWORD,
        authSource="admin"
    )
    db = client[app_configuration.MONGO_APPLICATION_DB]

    yield db

    client.drop_database(app_configuration.MONGO_APPLICATION_DB)
    client.close()


@pytest.fixture(scope="function")
def mg_database(mg_database_empty: Database, room_dicts: List[Dict[str, Any]]):
    collection = mg_database_empty.rooms
    collection.insert_many(room_dicts)
    
    yield mg_database_empty

    collection.delete_many({})