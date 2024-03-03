import uuid
import random
from typing import List, Callable, Dict, Any

import pytest
from fastapi.testclient import TestClient

from src.domain.room import Room
from application.app import create_app


data = [
    {
        "code": uuid.UUID("f853578c-fc0f-4e65-81b8-566c5dffa35a"),
        "size": random.randint(50, 500),
        "price": 39,
        "longitude": random.random(),
        "latitude": random.random(),
    },
    {
        "code": uuid.UUID("fe2c3195-aeff-487a-a08f-e0bdc0ec6e9a"),
        "size": random.randint(50, 500),
        "price": 66,
        "longitude": random.random(),
        "latitude": random.random(),
    },
    {
        "code": uuid.UUID("913694c6-435a-4366-ba0d-da5334a611b2"),
        "size": random.randint(50, 500),
        "price": 60,
        "longitude": random.random(),
        "latitude": random.random(),
    },
    {
        "code": uuid.UUID("eed76e77-55c1-41ce-985d-ca49bf6c0585"),
        "size": random.randint(50, 500),
        "price": 48,
        "longitude": random.random(),
        "latitude": random.random(),
    }
]


@pytest.fixture
def domain_rooms() -> List[Room]:
    return [Room.model_validate(x) for x in data]

    
@pytest.fixture
def room_dicts() -> List[Dict[str, Any]]:
    return data


@pytest.fixture
def client() -> TestClient:
    app = create_app("test")
    return TestClient(app)