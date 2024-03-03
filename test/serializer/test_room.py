import json
from src.serializers.room import RoomJsonEncoder
from src.domain.room import Room


def test_serialize_domain_room(domain_rooms):
    room: Room = domain_rooms[0]
    expected_json = f"""{{"code": "{room.code}", "size": {room.size}, "price": {room.price}, "longitude": {room.longitude}, "latitude": {room.latitude}}}"""

    json_room = json.dumps(room, cls=RoomJsonEncoder)

    assert json_room == expected_json