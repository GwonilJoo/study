from unittest import TestCase, mock
from typing import List
import random

from test.conftest import Fixture
from src.domain.room import Room
from src.repository.memrepo import MemRepo


class TestMemRepoUseCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.room_dicts = Fixture.room_dicts(4)


    def setUp(self) -> None:
        print(f"[START] {self.__class__.__name__} - {self._testMethodName}")


    def tearDown(self) -> None:
        print(f"[Done] {self.__class__.__name__} - {self._testMethodName}\n")


    def test_memrepo_list_without_parameters(self):
        repo = MemRepo(self.room_dicts)
        rooms = [Room.from_dict(x) for x in self.room_dicts]

        self.assertEqual(repo.list(), rooms)