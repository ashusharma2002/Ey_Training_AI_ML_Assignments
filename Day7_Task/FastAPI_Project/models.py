from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CARD = "card"
    UPI = "upi"
    CASH = "cash"
    WALLET = "wallet"


class Address(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "street": "42 MG Road",
                "city": "Dehradun",
                "state": "Uttarakhand",
                "pincode": "248001",
                "country": "India",
            }
        }
    )

    street: str = Field(..., min_length=3)
    city: str
    state: str
    pincode: str = Field(..., pattern=r"^\d{6}$")
    country: str = Field(default="India")


class Product(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    sku: str
    in_stock: bool = True

    @field_validator("price")
    @classmethod
    def price_precision(cls, v: float):
        return round(v, 2)


class OrderItem(BaseModel):
    product: Product
    quantity: int = Field(..., ge=1, le=100)
    discount: float = Field(default=0.0, ge=0.0, le=100.0)

    @property
    def line_total(self):
        discounted = self.product.price * (1 - self.discount / 100)
        return round(discounted * self.quantity, 2)


class Customer(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=2)
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$")
    shipping_address: Address
    billing_address: Optional[Address] = None

    @model_validator(mode="after")
    def set_billing_address(self):
        if self.billing_address is None:
            self.billing_address = self.shipping_address
        return self


class OrderCreate(BaseModel):
    customer: Customer
    items: List[OrderItem] = Field(..., min_length=1)
    payment_method: PaymentMethod
    notes: Optional[str] = None

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("Order must contain at least one item.")
        return v


class Order(OrderCreate):
    id: UUID = Field(default_factory=uuid4)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrderSummary(BaseModel):
    subtotal: float
    total_discount: float
    grand_total: float
    item_count: int


class OrderResponse(Order):
    summary: OrderSummary

    @classmethod
    def from_order(cls, order: Order):
        items = order.items

        subtotal = sum(i.product.price * i.quantity for i in items)

        total_discount = sum(
            (i.product.price * i.quantity) - i.line_total
            for i in items
        )

        grand_total = round(subtotal - total_discount, 2)

        return cls(
            **order.model_dump(),
            summary=OrderSummary(
                subtotal=round(subtotal, 2),
                total_discount=round(total_discount, 2),
                grand_total=grand_total,
                item_count=sum(i.quantity for i in items),
            )
        )