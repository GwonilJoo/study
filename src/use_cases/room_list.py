from typing import List

from src.domain.room import Room


class RoomListUseCase:
    def __init__(self, repo):
        self._repo = repo


    def exec(self) -> List[Room]:
        return self._repo.list()