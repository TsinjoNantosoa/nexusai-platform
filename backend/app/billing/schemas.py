from pydantic import BaseModel, ConfigDict, Field


class ProductOut(BaseModel):
    sku: str
    name: str
    price_cents: int = Field(serialization_alias="priceCents")
    currency: str
    gems: int
    subscription: bool

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CheckoutIn(BaseModel):
    sku: str
