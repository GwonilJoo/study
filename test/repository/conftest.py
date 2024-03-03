from typing import List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import pytest

from src.repository.postgres.postgres_objects import Base, Room
from application.config import TestConfig


@pytest.fixture(scope="session")
def pg_session_empty(app_configuration: TestConfig):
    connection_string = "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
        app_configuration.POSTGRES_USER,
        app_configuration.POSTGRES_PASSWORD,
        app_configuration.POSTGRES_HOST,
        app_configuration.POSTGRES_PORT,
        app_configuration.POSTGRES_APPLICATION_DB,
    )
    engine = create_engine(connection_string)
    connection = engine.connect()

    Base.metadata.create_all(engine)
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    yield session

    session.close()
    connection.close()


@pytest.fixture(scope="function")
def pg_session(pg_session_empty: Session, room_dicts: List[Dict[str, Any]]):
    for room in room_dicts:
        new_room = Room(
            code=str(room["code"]),
            size=room["size"],
            price=room["price"],
            longitude=room["longitude"],
            latitude=room["latitude"],
        )
        pg_session_empty.add(new_room)
        pg_session_empty.commit()
    
    yield pg_session_empty

    pg_session_empty.query(Room).delete()
    pg_session_empty.commit()