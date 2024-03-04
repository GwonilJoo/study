import pytest
import uuid

from src.domain.room import Room
from src.repository.memrepo import MemRepo, Filters


def test_memrepo_list_without_parameters(room_dicts):
    repo = MemRepo(room_dicts)
    rooms = [Room.model_validate(x) for x in room_dicts]

    assert repo.list() == rooms


def test_memrepo_list_with_code_equal_filter(room_dicts):
    target_code = room_dicts[0]["code"]
    filters = {"code__eq": target_code}

    repo = MemRepo(room_dicts)
    rooms = repo.list(filters=Filters(**filters))

    assert len(rooms) == 1
    assert rooms[0].code == target_code


def test_memrepo_list_with_price_equal_filter(room_dicts):
    target_price = 60
    filters = {"price__eq": target_price}

    repo = MemRepo(room_dicts)
    rooms = repo.list(filters=Filters(**filters))

    assert len(rooms) == 1
    assert rooms[0].code == "913694c6-435a-4366-ba0d-da5334a611b2"


def test_memrepo_list_with_price_less_than_filter(room_dicts):
    target_price = 60
    filters = {"price__lt": target_price}

    repo = MemRepo(room_dicts)
    rooms = repo.list(filters=Filters(**filters))

    assert len(rooms) == 2
    assert set([r.code for r in rooms]) == {
        "f853578c-fc0f-4e65-81b8-566c5dffa35a",
        "eed76e77-55c1-41ce-985d-ca49bf6c0585",
    }


def test_memrepo_list_with_price_greater_than_filter(room_dicts):
    target_price = 48
    filters = {"price__gt": target_price}

    repo = MemRepo(room_dicts)
    rooms = repo.list(filters=Filters(**filters))

    assert len(rooms) == 2
    assert set([r.code for r in rooms]) == {
        "fe2c3195-aeff-487a-a08f-e0bdc0ec6e9a",
        "913694c6-435a-4366-ba0d-da5334a611b2",
    }


def test_memrepo_list_with_price_between_filter(room_dicts):
    low_price = 48
    high_price = 66
    filters = {"price__gt": low_price, "price__lt": high_price}

    repo = MemRepo(room_dicts)
    rooms = repo.list(filters=Filters(**filters))

    assert len(rooms) == 1
    assert rooms[0].code == "913694c6-435a-4366-ba0d-da5334a611b2"