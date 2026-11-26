from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductOut(BaseModel):
    sku: str
    name: str
    price_cents: int = Field(serialization_alias="priceCents")
    currency: str
    gems: int
    subscription: bool

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CheckoutIn(BaseModel):
    sku: str = Field(min_length=1, max_length=32)

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.strip().lower()


class CheckoutOut(BaseModel):
    order_id: UUID
    checkout_url: str


class OrderOut(BaseModel):
    id: UUID
    sku: str
    status: str
    payment_status: str = Field(serialization_alias="paymentStatus")
    fulfillment_status: str = Field(serialization_alias="fulfillmentStatus")
    gems: int
    price_cents: int = Field(serialization_alias="priceCents")
    currency: str
    created_at: datetime = Field(serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
