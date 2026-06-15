from typing import Dict, Optional
from uuid import UUID

from models import Order


class OrderRepository:

    def __init__(self):
        self._store: Dict[UUID, Order] = {}

    def save(self, order: Order) -> Order:
        self._store[order.id] = order
        return order

    def get(self, order_id: UUID) -> Optional[Order]:
        return self._store.get(order_id)

    def list_all(self) -> list[Order]:
        return list(self._store.values())

    def update_status(self, order_id: UUID, status):
        order = self._store.get(order_id)

        if not order:
            return None

        updated = order.model_copy(
            update={"status": status}
        )

        self._store[order_id] = updated

        return updated

    def delete(self, order_id: UUID) -> bool:

        if order_id in self._store:
            del self._store[order_id]
            return True

        return False


_repo = OrderRepository()


def get_repository() -> OrderRepository:
    return _repo