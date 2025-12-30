from abc import ABC, abstractmethod
from typing import List
from domain.entities.order import Order


class OrderRepository(ABC):

    @abstractmethod
    def get_all(self) -> List[Order]:
        pass