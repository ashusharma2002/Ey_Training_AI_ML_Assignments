from typing import List, Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from models import (
    Order,
    OrderCreate,
    OrderResponse,
    OrderStatus,
)

from database import (
    OrderRepository,
    get_repository,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# ─────────────────────────────────────────────────────────
# CREATE ORDER
# ─────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a new order",
)
def create_order(
    payload: OrderCreate,
    repo: OrderRepository = Depends(get_repository),
) -> OrderResponse:

    order = Order(**payload.model_dump())

    saved = repo.save(order)

    return OrderResponse.from_order(saved)


# ─────────────────────────────────────────────────────────
# LIST ORDERS
# FILTER + PAGINATION + SORTING
# ─────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List all orders",
)
def list_orders(
    status: Optional[OrderStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: Literal["created_at", "grand_total"] = "created_at",
    repo: OrderRepository = Depends(get_repository),
) -> List[OrderResponse]:

    # Get all orders
    orders = repo.list_all()

    # Filter by status
    if status:
        orders = [o for o in orders if o.status == status]

    # Sort orders
    if sort_by == "grand_total":
        orders.sort(
            key=lambda o: OrderResponse.from_order(o).summary.grand_total,
            reverse=True
        )
    else:
        orders.sort(
            key=lambda o: o.created_at,
            reverse=True
        )

    # Pagination
    paginated_orders = orders[skip: skip + limit]

    return [
        OrderResponse.from_order(o)
        for o in paginated_orders
    ]


# ─────────────────────────────────────────────────────────
# GET SINGLE ORDER
# ─────────────────────────────────────────────────────────

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get a single order by ID",
)
def get_order(
    order_id: UUID,
    repo: OrderRepository = Depends(get_repository),
) -> OrderResponse:

    order = repo.get(order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found.",
        )

    return OrderResponse.from_order(order)


# ─────────────────────────────────────────────────────────
# UPDATE STATUS
# ─────────────────────────────────────────────────────────

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
)
def update_order_status(
    order_id: UUID,
    new_status: OrderStatus,
    repo: OrderRepository = Depends(get_repository),
) -> OrderResponse:

    order = repo.update_status(order_id, new_status)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found.",
        )

    return OrderResponse.from_order(order)


# ─────────────────────────────────────────────────────────
# DELETE ORDER
# ─────────────────────────────────────────────────────────

@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete order",
)
def delete_order(
    order_id: UUID,
    repo: OrderRepository = Depends(get_repository),
) -> None:

    deleted = repo.delete(order_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found.",
        )