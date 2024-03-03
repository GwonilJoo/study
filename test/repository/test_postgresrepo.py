import uuid

import pytest

from src.repository.postgres.postgres_objects import Room
from src.repository import PostgresRepo, PostgresConfig, Filters
from application.config import TestConfig

pytestmark = pytest.mark.integration


def test_repo_list_without_parameters(app_configuration: TestConfig, pg_session, room_dicts):
    config = PostgresConfig(
        USER=app_configuration.POSTGRES_USER,
        PASSWORD=app_configuration.POSTGRES_PASSWORD,
        HOST=app_configuration.POSTGRES_HOST,
        PORT=app_configuration.POSTGRES_PORT,
        APPLICATION_DB=app_configuration.POSTGRES_APPLICATION_DB,
    )
    repo = PostgresRepo(config)
    repo_rooms = repo.list()

    assert set([r.code for r in repo_rooms]) == set([r["code"] for r in room_dicts])


def test_repo_list_with_code_equal_filter(app_configuration: TestConfig, pg_session, room_dicts):
    target_code = room_dicts[0]["code"]
    filters = {"code__eq": target_code}

    config = PostgresConfig(
        USER=app_configuration.POSTGRES_USER,
        PASSWORD=app_configuration.POSTGRES_PASSWORD,
        HOST=app_configuration.POSTGRES_HOST,
        PORT=app_configuration.POSTGRES_PORT,
        APPLICATION_DB=app_configuration.POSTGRES_APPLICATION_DB,
    )
    repo = PostgresRepo(config)
    repo_rooms = repo.list(filters=Filters(**filters))

    assert len(repo_rooms) == 1
    assert repo_rooms[0].code == target_code


def test_repo_list_with_price_equal_filter(app_configuration: TestConfig, pg_session, room_dicts):
    target_price = 60
    filters = {"price__eq": target_price}

    config = PostgresConfig(
        USER=app_configuration.POSTGRES_USER,
        PASSWORD=app_configuration.POSTGRES_PASSWORD,
        HOST=app_configuration.POSTGRES_HOST,
        PORT=app_configuration.POSTGRES_PORT,
        APPLICATION_DB=app_configuration.POSTGRES_APPLICATION_DB,
    )
    repo = PostgresRepo(config)
    repo_rooms = repo.list(filters=Filters(**filters))

    assert len(repo_rooms) == 1
    assert repo_rooms[0].code == uuid.UUID("913694c6-435a-4366-ba0d-da5334a611b2")


def test_repo_list_with_price_less_than_filter(app_configuration: TestConfig, pg_session, room_dicts):
    target_price = 60
    filters = {"price__lt": target_price}

    config = PostgresConfig(
        USER=app_configuration.POSTGRES_USER,
        PASSWORD=app_configuration.POSTGRES_PASSWORD,
        HOST=app_configuration.POSTGRES_HOST,
        PORT=app_configuration.POSTGRES_PORT,
        APPLICATION_DB=app_configuration.POSTGRES_APPLICATION_DB,
    )
    repo = PostgresRepo(config)
    rooms = repo.list(filters=Filters(**filters))

    assert len(rooms) == 2
    assert set([r.code for r in rooms]) == {
        uuid.UUID("f853578c-fc0f-4e65-81b8-566c5dffa35a"),
        uuid.UUID("eed76e77-55c1-41ce-985d-ca49bf6c0585"),
    }


def test_repo_list_with_price_greater_than_filter(app_configuration: TestConfig, pg_session, room_dicts):
    target_price = 48
    filters = {"price__gt": target_price}

    config = PostgresConfig(
        USER=app_configuration.POSTGRES_USER,
        PASSWORD=app_configuration.POSTGRES_PASSWORD,
        HOST=app_configuration.POSTGRES_HOST,
        PORT=app_configuration.POSTGRES_PORT,
        APPLICATION_DB=app_configuration.POSTGRES_APPLICATION_DB,
    )
    repo = PostgresRepo(config)
    rooms = repo.list(filters=Filters(**filters))

    assert len(rooms) == 2
    assert set([r.code for r in rooms]) == {
        uuid.UUID("fe2c3195-aeff-487a-a08f-e0bdc0ec6e9a"),
        uuid.UUID("913694c6-435a-4366-ba0d-da5334a611b2"),
    }


def test_repo_list_with_price_between_filter(app_configuration: TestConfig, pg_session, room_dicts):
    low_price = 48
    high_price = 66
    filters = {"price__gt": low_price, "price__lt": high_price}

    config = PostgresConfig(
        USER=app_configuration.POSTGRES_USER,
        PASSWORD=app_configuration.POSTGRES_PASSWORD,
        HOST=app_configuration.POSTGRES_HOST,
        PORT=app_configuration.POSTGRES_PORT,
        APPLICATION_DB=app_configuration.POSTGRES_APPLICATION_DB,
    )
    repo = PostgresRepo(config)
    rooms = repo.list(filters=Filters(**filters))

    assert len(rooms) == 1
    assert rooms[0].code == uuid.UUID("913694c6-435a-4366-ba0d-da5334a611b2")