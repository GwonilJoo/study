from typing import List

from src.domain.room import Room
from src.repository.interface import IRepo


class RoomListUseCase:
    def __init__(self, repo: IRepo):
        self._repo = repo


    def exec(self) -> List[Room]:
        return self._repo.list()