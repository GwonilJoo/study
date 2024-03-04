from src.domain.room import Room


def test_room_model_init(room_dicts):
    room_dict = room_dicts[0]
    room = Room(
        code=room_dict["code"],
        size=room_dict["size"],
        price=room_dict["price"],
        longitude=room_dict["longitude"],
        latitude=room_dict["latitude"]
    )

    assert str(room.code) == room_dict["code"]
    assert room.size == room_dict["size"]
    assert room.price == room_dict["price"]
    assert room.longitude == room_dict["longitude"]
    assert room.latitude == room_dict["latitude"]


def test_room_model_from_dict(room_dicts):
    room_dict = room_dicts[0]
    room = Room.model_validate(room_dict)

    assert str(room.code) == room_dict["code"]
    assert room.size == room_dict["size"]
    assert room.price == room_dict["price"]
    assert room.longitude == room_dict["longitude"]
    assert room.latitude == room_dict["latitude"]


def test_room_model_to_dict(room_dicts):
    room_dict = room_dicts[0]
    room = Room.model_validate(room_dict)

    assert room.model_dump() == room_dict


def test_room_model_comparison(room_dicts):
    room_dict = room_dicts[0]
    room1 = Room.model_validate(room_dict)
    room2 = Room.model_validate(room_dict)

    assert room1 == room2


def test_room_model_to_json(room_dicts):
    room_dict = room_dicts[0]
    room = Room.model_validate(room_dict)
    
    json_room = room.model_dump_json()
    expected_json = f"""{{"code":"{str(room.code)}","size":{room.size},"price":{room.price},"longitude":{room.longitude},"latitude":{room.latitude}}}"""

    assert json_room == expected_json


def test_room_model_from_json(room_dicts):
    room_dict = room_dicts[0]
    room = Room.model_validate(room_dict)

    json_room = room.model_dump_json()
    room_from_json = Room.model_validate_json(json_room)
    assert room == room_from_json