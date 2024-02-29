import json

from src.domain.room import Room


class RoomJsonEncoder(json.JSONEncoder):
    def default(self, o: Room) -> json:
        try:
            to_serialize = {
                'code': str(o.code),
                'size': o.size,
                'price': o.price,
                'longitude': o.longitude,
                'latitude': o.latitude,
            }
            return to_serialize
        except AttributeError:
            return super().default(o)